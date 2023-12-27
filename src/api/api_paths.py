from __future__ import annotations

import asyncio

from utils.database import get_current_timetable, insert_credential, update_credentials

from .tasks import TasksLoops


class APIPaths(TasksLoops):
    async def _GET_index(self) -> dict[str, str]:
        return {"message": "Hello World"}

    async def _POST_credentials(
        self, *, admission_number: str, password: str, section: int
    ) -> dict[str, str]:
        result = await insert_credential(
            self.cursor,
            admission_number=admission_number,
            password=password,
            section=section,
        )
        if result is None:
            await update_credentials(
                self.cursor,
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
        cur = await self.cursor.executescript(
            f"""
                DELETE FROM students_credentials WHERE admission_number = {admission_number[:13:]};
                DELETE FROM students WHERE admission_number = {admission_number[:13:]};
            """,
        )
        results = await cur.fetchall()
        return {"message": "Deleted"} if results else {"message": "Not Found"}

    async def _GET_credentials(self, *, admission_number: str) -> dict[str, str]:
        cur = await self.cursor.execute(
            """
                SELECT * FROM students_credentials WHERE admission_number = ?
            """,
            (admission_number,),
        )
        results = await cur.fetchall()
        return {"message": "Found"} if results else {"message": "Not Found"}

    async def _GET_timetable(self, *, admission_number: str) -> dict:
        return await get_current_timetable(self.cursor, admission_number)
