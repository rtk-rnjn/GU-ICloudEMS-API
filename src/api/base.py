from __future__ import annotations

from abc import ABC, abstractmethod

import aiosqlite


class BaseClass(ABC):
    cursor: aiosqlite.Cursor
    database_connection: aiosqlite.Connection

    @abstractmethod
    async def init(self) -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    @abstractmethod
    def add_all_routes(self) -> None:
        ...

    @abstractmethod
    async def start_loops(self) -> None:
        ...
