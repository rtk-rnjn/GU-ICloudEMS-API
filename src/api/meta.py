from __future__ import annotations

import asyncio
import logging

from src.web_driver.profile_driver import ProfileDriver
from src.web_driver.time_table_driver import TimeTableDriver
from utils.database import insert_alternative_arrangement, insert_main_timetable
from utils.html_parser import ProfileParser, TimeTableParser

from .base import BaseClass

log = logging.getLogger("__name__")


class MetaClass(BaseClass):
    async def _update_profile(self, *, admission_number: str, password: str) -> None:
        profile = ProfileDriver(admission_number, password)
        log.info("logging in with %s and %s", admission_number, password)

        await asyncio.to_thread(profile.login)
        query = ProfileParser(profile.download_page_source()).create_sql_query()
        log.debug("executing sql query %s", query)
        await self.cursor.execute(query)

        log.info("committing changes")
        await self.database_connection.commit()

        profile.close()

    async def _update_timetable(self, admission_number: str, password: str) -> None:
        timetable = TimeTableDriver(admission_number, password)
        await asyncio.to_thread(timetable.login)
        parser = TimeTableParser(timetable.download_page_source())
        data = parser.get_data()

        functions = [
            insert_main_timetable(self.database_connection, **data["timetable"]),
            insert_alternative_arrangement(
                self.database_connection, **data["alternative_timetable"]
            ),
        ]

        await asyncio.gather(*functions, return_exceptions=False)

    async def _remove_old_timetable(self) -> None:
        await self.cursor.execute(
            """
                DELETE FROM
                    timetable
                WHERE
                    datetime(start_time) < datetime('now', '-7 days', '+5 hours', '+30 minutes');
            """
        )
        await self.cursor.execute(
            """
                DELETE FROM 
                    alternative_timetable
                WHERE
                    datetime(start_time) < datetime('now', '-7 days', '+5 hours', '+30 minutes');
            """
        )
        log.info("committing changes")
        await self.database_connection.commit()
