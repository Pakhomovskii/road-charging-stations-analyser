import json
import logging
from aiohttp import web

logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s:%(message)s",
)

logger = logging.getLogger(__name__)


async def init_app():
    app = web.Application()
    app.router.add_post("/calculate_route", calculate_route)
    return app


async def calculate_route(request: web.Request):
    try:
        data = await request.json()
    except json.JSONDecodeError:
        logger.error("Invalid JSON data")
        return web.json_response({"error": "Invalid JSON data"}, status=400)

    required_fields = {
        "city1": str,
        "city2": str,
        "road": str,
        "user_current_distance": (int, float),
        "user_max_distance": (int, float),
    }

    for field, expected_type in required_fields.items():
        if field not in data:
            return _create_error_response(f"Missing field: {field}")

        value = data[field]

        if not isinstance(value, expected_type):
            return _create_error_response(f"Invalid type for field '{field}': expected {expected_type}, got {type(value)}")

        if field in ["user_current_distance", "user_max_distance"] and value < 0:
            return _create_error_response(f"Field '{field}' must be non-negative")

        if isinstance(value, str) and not value.strip():
            return _create_error_response(f"Field '{field}' cannot be empty")

    try:
        # # Replace with your actual route calculation logic
        # route_details = {"distance": 500, "estimated_time": "2 hours"}

        success_response = {
            "status": "success",
            "message": "Route calculation successful!",
            "route_details": "details info"
        }
        logger.info(success_response)
        return web.json_response(success_response)
    except Exception() as e:
        logger.exception("Error calculating route:")
        return _create_error_response("Internal server error. Please try again later.", status=500)


def _create_error_response(message: str, status: int = 400) -> web.Response:
    logger.error(message)
    return web.json_response({"error": message}, status=status)


if __name__ == "__main__":
    web.run_app(init_app(), host="localhost", port=8080)
