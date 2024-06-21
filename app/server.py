import asyncio
import logging

from aiohttp import web
from dotenv import load_dotenv

from app.routing import calculate_route, create_async_engine

load_dotenv()  # Here I load my variables from the.env file

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/road_helper"
engine = create_async_engine(DATABASE_URL, echo=True)


async def init_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/calculate_route", calculate_route)

    app["db"] = engine

    async def close_db(app: web.Application) -> None:
        await engine.dispose()

    app.on_cleanup.append(close_db)
    return app


async def main():
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8081)
    await site.start()
    logger.info("Server started at http://localhost:8081")
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
