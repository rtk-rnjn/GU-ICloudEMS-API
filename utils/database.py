from __future__ import annotations

from typing import TYPE_CHECKING

from aiosqlite import Connection

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from .typehints import (
        AlternativeArrangement,
        Arrangement,
        Credentials,
        TimeTableReturnData,
    )

import logging

from .html_parser import _SlotParser

log = logging.getLogger("__name__")


async def insert_credential(connection: Connection, **data: Unpack[Credentials]):
    query = """
        INSERT INTO students_credentials
            (admission_number, password, section)
        VALUES
            (?, ?, ?)
        ON CONFLICT DO NOTHING
        RETURNING id
    """
    query_args = (data["admission_number"], data["password"], data["section"])

    log.info("inserting credentials %s", data)
    log.debug("executing sql query %s with args %s", query, query_args)

    cursor = await connection.cursor()
    cur = await cursor.execute(query, query_args)

    result = await cur.fetchone()

    log.debug("committing changes")
    await connection.commit()

    # why not return the result directly?
    #
    # When you use RETURNING with SQLite3,
    # the result have to be used before you commit the transaction or this error will occur.
    
    return result


async def update_credentials(connection: Connection, **data: Unpack[Credentials]):
    query = """
        UPDATE students_credentials
        SET
            password = ?,
            section = ?
        WHERE
            admission_number = ?
    """

    query_args = (data["password"], data["section"], data["admission_number"])

    log.info("updating credentials %s", data)
    log.debug("executing sql query %s with args %s", query, query_args)

    cursor = await connection.cursor()
    await cursor.execute(query, query_args)

    log.debug("committing changes")
    await connection.commit()


async def insert_main_timetable(
    connection: Connection, **raw_data: Unpack[Arrangement]
):
    # sourcery skip: inline-immediately-yielded-variable
    log.info("inserting main timetable %s", raw_data)
    for _, arrangements in raw_data.items():
        assert isinstance(arrangements, list)
        if not arrangements:
            continue
        cursor = await connection.cursor()
        for data in arrangements:
            query = _SlotParser.from_dict_to_sql(data["slot"])
            log.debug("executing sql query %s", query)

            cur = await cursor.execute(query)
            slot_id = await cur.fetchone()
            if slot_id is None:
                raise RuntimeError("Invalid slot data")

            timetable_query = """
                INSERT INTO timetable
                    (start_time, end_time, faculty_name, slot_id, class)
                VALUES
                    (?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
            """
            timetable_query_args = (
                data["start_time"],
                data["end_time"],
                data["faculty_name"],
                slot_id[0],
                data["class"],
            )
            log.debug(
                "executing sql query %s with args %s",
                timetable_query,
                timetable_query_args,
            )
            cur = await cursor.execute(timetable_query, timetable_query_args)

        log.debug("committing changes")
        await connection.commit()


async def insert_alternative_arrangement(
    connection: Connection, **data: Unpack[AlternativeArrangement]
):
    # sourcery skip: inline-immediately-yielded-variable
    log.info("inserting alternative timetable %s", data)

    for _, arrangements in data.items():
        assert isinstance(arrangements, list)
        if not arrangements:
            continue

        cursor = await connection.cursor()

        for arrangement in arrangements:
            query = _SlotParser.from_dict_to_sql(arrangement["slot"])
            log.debug("executing sql query %s", query)
            cur = await cursor.execute(query)
            slot_id = await cur.fetchone()
            if slot_id is None:
                raise RuntimeError("Invalid slot data")

            alternate_timetable = """
                INSERT INTO alternative_timetable
                    (start_time, end_time, faculty_name, alternative_faculty_name, slot_id, class)
                VALUES
                    (?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
            """
            alternate_timetable_args = (
                arrangement["start_time"],
                arrangement["end_time"],
                arrangement["faculty_name"],
                arrangement["alternate_faculty_name"],
                slot_id[0],
                arrangement["class"],
            )
            log.debug(
                "executing sql query %s with args %s",
                alternate_timetable,
                alternate_timetable_args,
            )
            cur = await cursor.execute(alternate_timetable, alternate_timetable_args)

        log.debug("committing changes")
        await connection.commit()


async def get_current_timetable(
    connection: Connection, admission_number: str
) -> TimeTableReturnData:
    if len(admission_number) > 14:
        raise ValueError("Invalid admission number")

    query = """
        SELECT
            TT.start_time, TT.end_time, TT.faculty_name, TT.class, S.course_code, S.course_name, S.course_type, S.room
        FROM 
            timetable AS TT
        JOIN 
            slots AS S
        ON
            TT.slot_id = S.id
        WHERE 
            datetime('now') BETWEEN datetime(TT.start_time) AND datetime(TT.end_time)
            AND
            S.section in (
                SELECT
                    SA.section
                FROM
                    students_credentials AS SA
                WHERE
                    SA.admission_number = ?
                    AND
                    SA.class = TT.class
            ) 
    """
    log.debug("executing sql query %s with args %s", query, (admission_number,))
    cursor = await connection.cursor()

    cur = await cursor.execute(query, (admission_number,))
    data: TimeTableReturnData = {}  # type: ignore
    async for (
        start_time,
        end_time,
        faculty_name,
        class_,
        course_code,
        course_name,
        course_type,
        room,
    ) in cur:
        data = {
            "start_time": start_time,
            "end_time": end_time,
            "faculty_name": faculty_name,
            "class": class_,
            "course_code": course_code,
            "course_name": course_name,
            "course_type": course_type,
            "room": room,
        }

    log.debug("committing changes")
    await connection.commit()
    return data
