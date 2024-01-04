from __future__ import annotations

import asyncio
import logging

from utils.database import get_current_timetable, insert_credential, update_credentials

from .tasks import TasksLoops

log = logging.getLogger("__name__")


class APIPaths(TasksLoops):
    async def _GET_index(self) -> dict[str, str]:
        return {"message": "Hello World"}

    async def _POST_credentials(
        self, *, admission_number: str, password: str, section: int
    ) -> dict[str, str]:
        result = await insert_credential(
            self.database_connection,
            admission_number=admission_number,
            password=password,
            section=section,
        )
        if result is None:
            await update_credentials(
                self.database_connection,
                admission_number=admission_number,
                password=password,
                section=section,
            )
            await asyncio.gather(
                self._update_profile(
                    admission_number=admission_number, password=password
                )
            )
            return {"message": "Updated"}

        await asyncio.gather(
            self._update_profile(admission_number=admission_number, password=password)
        )
        return {"message": "Inserted"}

    async def _DELETE_credentials(self, *, admission_number: str) -> dict[str, str]:
        # T_T

        script = f"""
            BEGIN;
            DELETE FROM students_credentials WHERE admission_number = {admission_number[:13:]};
            DELETE FROM students WHERE admission_number = {admission_number[:13:]};
            COMMIT;
        """
        log.debug("executing sql script %s", script)

        cur = await self.cursor.executescript(script)
        results = await cur.fetchall()
        return {"message": "Deleted"} if results else {"message": "Not Found"}

    async def _GET_credentials(self, *, admission_number: str) -> dict[str, str]:
        query = """SELECT * FROM students_credentials WHERE admission_number = ?"""
        log.debug("executing sql query %s with args %s", query, (admission_number,))
        cur = await self.cursor.execute(
            query,
            (admission_number,),
        )
        results = await cur.fetchall()
        return {"message": "Found"} if results else {"message": "Not Found"}

    async def _GET_timetable(self, *, admission_number: str) -> dict:
        return await get_current_timetable(self.database_connection, admission_number)  # type: ignore

    async def _GET_commit(self) -> dict[str, str]:
        log.info("committing changes")
        await self.database_connection.commit()
        return {"message": "Committed"}
