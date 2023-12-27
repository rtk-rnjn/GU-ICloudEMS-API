from __future__ import annotations

import asyncio

from utils.tasks import tasks

from .meta import MetaClass


class TasksLoops(MetaClass):
    @tasks.loop(seconds=5)
    async def global_commit_cycle(self) -> None:
        if hasattr(self, "database_connection"):
            await self.database_connection.commit()

    @tasks.loop(hours=3)
    async def global_timetable_update(self) -> None:
        if not hasattr(self, "database_connection"):
            return

        seen = set()
        query = """
            SELECT 
                SC.admission_number, SC.password, SC.section, S.semester, S.class
            FROM
                students_credentials AS SC
            JOIN
                students AS S
            ON
                S.admission_number = SC.admission_number
        """
        cur = await self.cursor.execute(query)
        async for admission_number, password, section, semester, class_ in cur:
            if (section, semester, class_) in seen:
                continue
            try:
                await asyncio.gather(
                    self._update_timetable(admission_number, password),
                    self._remove_old_timetable(),
                )
            except Exception:
                pass
            else:
                seen.add((section, semester, class_))
