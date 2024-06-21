"""
This module provides functionality for calculating routes with electric charging stations,
reachability analysis, and interaction with a PostgreSQL database.

Key Features:

- **Route Calculation:** Calculates routes between two cities.
- **Charging Stations:** Identifies electric charging stations along the route.
- **Reachability Analysis:** Determines if the route is achievable based on the user's current and maximum distance capabilities.
- **Database Integration:** Stores and retrieves route information from a PostgreSQL database using SQLAlchemy.

Main Functions:

- `get_distance(location1, location2)`: Calculates the distance between two locations.
- `get_charging_stations(road_name)`: Fetches electric charging stations data for a given road.
- `get_route_coordinates(origin, destination)`: Retrieves route coordinates from Google Maps API.
- `filter_stations_on_route(stations, route_coordinates, distance_threshold)`: Filters charging stations on or near the route.
- `haversine_distance(lat1, lon1, lat2, lon2)`: Calculates the distance between two points using the Haversine formula.
- `calculate_reachability(stations_on_route, location1, location2, max_distance, current_distance)`: Calculates reachability and unreachable segments based on station distances.
- `calculate_route(request)`: Asynchronous function that handles route calculation requests, fetches data, calculates
  reachability, and interacts with the database.
"""
import json
import logging
import os

import geopy
import googlemaps
import aiohttp
import math

from googlemaps import Client, convert
from aiohttp import web, ClientSession
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import sqlalchemy as sa

from templates.constants import DATABASE_URL

logger = logging.getLogger(__name__)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.exc import SQLAlchemyError

# engine global
engine = create_async_engine(DATABASE_URL, echo=True)


def get_distance(location1, location2):
    """Calculates the distance between two locations."""
    return geodesic((location1.latitude, location1.longitude),
                    (location2.latitude, location2.longitude)).km


async def get_charging_stations(road_name):
    """Fetches electric charging stations data for a given road."""
    url = f'https://verkehr.autobahn.de/o/autobahn/{road_name}/services/electric_charging_station'
    headers = {'accept': 'application/json'}
    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            stations_data = await response.json()
            stations = stations_data.get('electric_charging_station', [])
            return [
                station for station in stations
                if road_name in station['title']
            ]


def get_route_coordinates(origin, destination):
    """Gets route coordinates from Google Maps API."""
    gmaps = Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
    directions_result = gmaps.directions(origin=origin,
                                         destination=destination,
                                         mode="driving")
    if not directions_result:
        raise ValueError("Unable to get route from Google Maps API")
    route_polyline = directions_result[0]['overview_polyline']['points']
    return [(point["lat"], point["lng"])
            for point in convert.decode_polyline(route_polyline)]


def filter_stations_on_route(stations,
                             route_coordinates,
                             distance_threshold=5):
    """Filters charging stations that are on or near the route."""
    stations_on_route = []
    nearest_station = None

    for station in stations:
        try:
            station_coords = (float(station["coordinate"]["lat"]),
                              float(station["coordinate"]["long"]))
            is_on_route = any(
                geodesic(station_coords, route_coord).kilometers <=
                distance_threshold for route_coord in route_coordinates)
            if is_on_route:
                stations_on_route.append(station)
        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                f"Error processing station data: {station}. Error: {e}")
            continue

    return stations_on_route, nearest_station


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates the distance between two points using the Haversine formula."""
    R = 6371  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


def calculate_reachability(stations_on_route, location1, location2,
                           max_distance, current_distance):
    """Calculates reachability and unreachable segments based on station distances."""
    unreachable_segments = []

    if stations_on_route:
        # Create a list of all relevant waypoints (start, stations, end)
        waypoints = [(location1.latitude, location1.longitude)] + \
                    [(float(station["coordinate"]["lat"]), float(station["coordinate"]["long"])) for station in
                     stations_on_route] + \
                    [(location2.latitude, location2.longitude)]

        for i in range(len(waypoints) - 1):
            point1 = waypoints[i]
            point2 = waypoints[i + 1]
            distance = haversine_distance(*point1, *point2)

            if distance > max_distance:
                unreachable_segments.append({
                    "start_point": point1,
                    "end_point": point2,
                    "distance": distance
                })

        # Check Reachability to Nearest and Farthest Station
        nearest_station_distance = haversine_distance(
            location1.latitude, location1.longitude,
            float(stations_on_route[0]["coordinate"]["lat"]),
            float(stations_on_route[0]["coordinate"]["long"]))
        farthest_station_distance = haversine_distance(
            float(stations_on_route[-1]["coordinate"]["lat"]),
            float(stations_on_route[-1]["coordinate"]["long"]),
            location2.latitude, location2.longitude)

        # Check reachability to the nearest and farthest station
        if nearest_station_distance > current_distance:
            unreachable_segments.insert(
                0, {
                    "start_point": (location1.latitude, location1.longitude),
                    "end_point":
                    (float(stations_on_route[0]["coordinate"]["lat"]),
                     float(stations_on_route[0]["coordinate"]["long"])),
                    "distance":
                    nearest_station_distance
                })
        if farthest_station_distance > max_distance - current_distance:
            unreachable_segments.append({
                "start_point":
                (float(stations_on_route[-1]["coordinate"]["lat"]),
                 float(stations_on_route[-1]["coordinate"]["long"])),
                "end_point": (location2.latitude, location2.longitude),
                "distance":
                farthest_station_distance
            })

    is_reachable = not unreachable_segments
    return is_reachable, unreachable_segments


async def calculate_route(request: web.Request):
    """
    Asynchronously calculates a route between two cities, identifies electric charging stations along the route,
    and evaluates the reachability based on the user's current and maximum distance capabilities.

    Parameters:
    - request (web.Request): The request object containing JSON data with the cities, road, and user distance information.

    Returns:
    - web.Response: A JSON response containing the route calculation results, including the distance between cities,
      stations on the route, the nearest station on the highway, reachability, and any unreachable segments.
      In case of errors, returns a JSON response with an appropriate error message and status code.
    """
    try:
        data = await request.json()
    except json.JSONDecodeError:
        logger.error("Invalid JSON data")
        return web.json_response({"error": "Invalid JSON data"}, status=400)

    # Input Validation
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
            return _create_error_response(
                f"Invalid type for field '{field}': expected {expected_type}, got {type(value)}"
            )
        if field in ["user_current_distance", "user_max_distance"
                     ] and value < 0:
            return _create_error_response(
                f"Field '{field}' must be non-negative")
        if isinstance(value, str) and not value.strip():
            return _create_error_response(f"Field '{field}' cannot be empty")

    city1, city2, road_name = data["city1"], data["city2"], data["road"]

    try:
        geolocator = Nominatim(user_agent="route_calculator")
        location1 = geolocator.geocode(city1)
        location2 = geolocator.geocode(city2)

        distance = get_distance(location1, location2)
        logger.info(f"The distance between cities is {distance}")

        stations = await get_charging_stations(road_name)
        route_coordinates = get_route_coordinates(city1, city2)
        stations_on_route, nearest_station = filter_stations_on_route(
            stations, route_coordinates)

        max_distance = data.get("user_max_distance", float("inf"))
        current_distance = data.get("user_current_distance", 0)

        is_reachable, unreachable_segments = calculate_reachability(
            stations_on_route, location1, location2, max_distance,
            current_distance)

        async with AsyncSession(engine) as session:

            try:
                # Prepare data for insertion
                is_possible = is_reachable
                problem_point1 = None
                problem_point2 = None
                if unreachable_segments:
                    # Ensure the list is not empty
                    if unreachable_segments[0]:
                        problem_point1 = str(
                            unreachable_segments[0]["start_point"])
                        problem_point2 = str(
                            unreachable_segments[0]["end_point"])

                # Insert Data into the Database for statistics
                insert_stmt = sa.text(
                    "INSERT INTO routes (city1, city2, road, is_possible, problem_point1, problem_point2) "
                    "VALUES (:city1, :city2, :road, :is_possible, :problem_point1, :problem_point2)"
                )

                await session.execute(
                    insert_stmt, {
                        "city1": city1,
                        "city2": city2,
                        "road": road_name,
                        "is_possible": is_possible,
                        "problem_point1": problem_point1,
                        "problem_point2": problem_point2
                    })

                await session.commit()

            except SQLAlchemyError as e:
                logger.error(f"Database error: {e}")
                await session.rollback()
                return web.json_response(
                    {"error": "Failed to save route data"}, status=500)

        success_response = {
            "status": "success",
            "message": "Route calculation successful!",
            "route_details": "details info",
            "distance": distance,
            "stations_on_route": stations_on_route,
            "nearest_station_on_highway": nearest_station,
            "is_reachable": is_reachable,
            "unreachable_segments": unreachable_segments,
        }
        logger.info(success_response)
        return web.json_response(success_response)

    # Block with the main exceptions
    except (aiohttp.ClientError, TimeoutError,
            googlemaps.exceptions.ApiError) as e:
        logger.error(f"Error: {e}")
        return web.json_response(
            {"error": "Error fetching or processing route data"}, status=500)

    except geopy.exc.GeocoderTimedOut:
        logger.error("Geocoding service timed out")
        return web.json_response({"error": "Error fetching geocoding data"},
                                 status=500)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return web.json_response({"error": "Internal server error"},
                                 status=500)


# The common error handler
def _create_error_response(message: str, status: int = 400) -> web.Response:
    logger.error(message)
    return web.json_response({"error": message}, status=status)
