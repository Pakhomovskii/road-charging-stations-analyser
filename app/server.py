from aiohttp import web
from app.routing import calculate_route
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


async def init_app():
    app = web.Application()
    app.router.add_post("/calculate_route", calculate_route)
    return app


if __name__ == "__main__":
    web.run_app(init_app(), host="localhost", port=8080)
