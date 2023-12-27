from __future__ import annotations

from typing import TYPE_CHECKING

from aiosqlite import Cursor

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from .typehints import (
        AlternativeArrangement,
        Arrangement,
        Credentials,
        TimeTableReturnData,
    )

from .html_parser import _SlotParser


async def insert_credential(cursor: Cursor, **data: Unpack[Credentials]):
    query = """
        INSERT INTO students_credentials
            (admission_number, password, section)
        VALUES
            (?, ?, ?)
        ON CONFLICT DO NOTHING
        RETURNING id
    """
    cur = await cursor.execute(
        query,
        (data["admission_number"], data["password"], data["section"]),
    )
    return await cur.fetchone()


async def update_credentials(cursor: Cursor, **data: Unpack[Credentials]):
    query = """
        UPDATE students_credentials
        SET
            password = ?,
            section = ?
        WHERE
            admission_number = ?
    """
    await cursor.execute(
        query,
        (data["password"], data["section"], data["admission_number"]),
    )


async def insert_main_timetable(cursor: Cursor, **raw_data: Unpack[Arrangement]):
    # sourcery skip: inline-immediately-yielded-variable
    for _, arrangements in raw_data.items():
        assert isinstance(arrangements, list)
        if not arrangements:
            continue
        for data in arrangements:
            cur = await cursor.execute(_SlotParser.from_dict_to_sql(data["slot"]))
            slot_id = await cur.fetchone()
            if slot_id is None:
                raise RuntimeError("Invalid slot data")

            cur = await cursor.execute(
                """
                    INSERT INTO timetable
                        (start_time, end_time, faculty_name, slot_id, class)
                    VALUES
                        (?, ?, ?, ?, ?)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """,
                (
                    data["start_time"],
                    data["end_time"],
                    data["faculty_name"],
                    slot_id[0],
                    data["class"],
                ),
            )


async def insert_alternative_arrangement(
    cursor: Cursor, **data: Unpack[AlternativeArrangement]
):
    # sourcery skip: inline-immediately-yielded-variable
    for _, arrangements in data.items():
        assert isinstance(arrangements, list)
        if not arrangements:
            continue

        for arrangement in arrangements:
            cur = await cursor.execute(
                _SlotParser.from_dict_to_sql(arrangement["slot"])
            )
            slot_id = await cur.fetchone()
            if slot_id is None:
                raise RuntimeError("Invalid slot data")

            cur = await cursor.execute(
                """
                    INSERT INTO alternative_timetable
                        (start_time, end_time, faculty_name, alternative_faculty_name, slot_id, class)
                    VALUES
                        (?, ?, ?, ?, ?, ?)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """,
                (
                    arrangement["start_time"],
                    arrangement["end_time"],
                    arrangement["faculty_name"],
                    arrangement["alternate_faculty_name"],
                    slot_id[0],
                    arrangement["class"],
                ),
            )


async def get_current_timetable(
    cursor: Cursor, admission_number: str
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
    return data
