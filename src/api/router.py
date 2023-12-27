from __future__ import annotations

import pathlib

import aiosqlite
from fastapi import APIRouter

from .api_paths import APIPaths

DATABASE_PATH = pathlib.Path(__file__).parent.parent.parent / "cached.sqlite"
DATEBASE_INIT_QUERY = pathlib.Path(__file__).parent.parent.parent / "init.sql"

query = DATEBASE_INIT_QUERY.read_text()


class Router(APIPaths):
    def __init__(self, name: str | None = None) -> None:
        self.name = name
        self.router = APIRouter()
        self.INIT = False
        self.add_all_routes()

    def __repr__(self) -> str:
        return f"<Server name={self.name}>"

    async def init(self) -> None:
        if self.INIT:
            return

        self.database_connection = await aiosqlite.connect(DATABASE_PATH)
        self.cursor = await self.database_connection.cursor()

        await self.cursor.executescript(query)
        await self.start_loops()
        self.INIT = True

    async def start_loops(self) -> None:
        if self.INIT:
            raise RuntimeError("Server already initialized")

        self.global_commit_cycle.start()
        self.global_timetable_update.start()

    async def close(self) -> None:
        await self.cursor.close()
        await self.database_connection.close()

    def add_all_routes(self) -> None:
        if self.INIT:
            raise RuntimeError("Server already initialized")

        self.add_meta_routes()
        self.add_credentials_routes()
        self.add_timetable_routes()

    def add_meta_routes(self) -> None:
        self.router.add_api_route(
            "/",
            lambda: {"message": "pong"},
            methods=["GET"],
            response_model=dict[str, str],
        )
        self.router.add_api_route(
            "/ping",
            lambda: {"message": "pong"},
            methods=["GET"],
            response_model=dict[str, str],
        )

    def add_credentials_routes(self) -> None:
        self.router.add_api_route(
            "/credentials",
            self._POST_credentials,
            methods=["POST"],
            response_model=self._POST_credentials.__annotations__["return"],
        )

        self.router.add_api_route(
            "/credentials",
            self._DELETE_credentials,
            methods=["DELETE"],
            response_model=self._DELETE_credentials.__annotations__["return"],
        )

        self.router.add_api_route(
            "/credentials",
            self._GET_credentials,
            methods=["GET"],
            response_model=self._GET_credentials.__annotations__["return"],
        )

    def add_timetable_routes(self) -> None:
        self.router.add_api_route(
            "/timetable",
            self._GET_timetable,
            methods=["GET"],
            response_model=self._GET_timetable.__annotations__["return"],
        )
