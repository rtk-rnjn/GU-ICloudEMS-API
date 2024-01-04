from __future__ import annotations

import asyncio
import logging

import uvicorn
from fastapi import FastAPI

from src.api import Router as APIRouter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
)

logging.getLogger()


async def main():
    app = FastAPI()
    api_router_instance = APIRouter()

    await api_router_instance.init()
    app.include_router(api_router_instance.router)

    app.debug = True

    config = uvicorn.Config(app, host="localhost", port=8000)
    server = uvicorn.Server(config=config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
