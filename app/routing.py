import json
import logging
import geopy
import googlemaps
import aiohttp
from googlemaps import Client, convert
from aiohttp import web, ClientSession
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

logger = logging.getLogger(__name__)


def is_valid_float(str_value):
    try:
        float(str_value)
        return True
    except ValueError:
        return False


def are_points_on_route(point1, point2, route_coordinates, distance_threshold=5):
    """
    Checks if two points are within a specified distance of a route.

    Args:
        point1: Tuple (latitude, longitude) of the first point.
        point2: Tuple (latitude, longitude) of the second point.
        route_coordinates: List of tuples (latitude, longitude) representing the route coordinates.
        distance_threshold: Maximum distance (in kilometers) from the route to consider a point "on the route".

    Returns:
        True if both points are within the distance threshold of the route, False otherwise.
    """
    for point in [point1, point2]:
        is_on_route = any(
            geodesic(point, route_coord).kilometers <= distance_threshold for route_coord in route_coordinates)
        if not is_on_route:
            return False
    return True


async def calculate_route(request: web.Request):
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
        if field in ["user_current_distance", "user_max_distance"] and value < 0:
            return _create_error_response(f"Field '{field}' must be non-negative")
        if isinstance(value, str) and not value.strip():
            return _create_error_response(f"Field '{field}' cannot be empty")

    city1, city2, road_name = data["city1"], data["city2"], data["road"]

    try:
        geolocator = Nominatim(user_agent="route_calculator")
        location1 = geolocator.geocode(city1)
        location2 = geolocator.geocode(city2)
        distance = geodesic((location1.latitude, location1.longitude),
                            (location2.latitude, location2.longitude)).km
        logger.info(f"The distance between cities is {distance}")


        async with ClientSession() as session:
            url = f'https://verkehr.autobahn.de/o/autobahn/{road_name}/services/electric_charging_station'
            headers = {'accept': 'application/json'}
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                stations_data = await response.json()
                stations = stations_data.get('electric_charging_station', [])


                filtered_stations = [station for station in stations if road_name in station['title']]


        gmaps = Client(key="")
        directions_result = gmaps.directions(origin=city1, destination=city2, mode="driving")

        if not directions_result:
            return _create_error_response("Unable to get route from Google Maps API", status=500)

        route_polyline = directions_result[0]['overview_polyline']['points']
        route_coordinates = convert.decode_polyline(route_polyline)


        route_coordinates = [(point["lat"], point["lng"]) for point in route_coordinates]

        stations_on_route = []
        nearest_station = ""
        min_distance = float('inf')
        for station in filtered_stations:
            try:

                coordinate = station.get('coordinate')
                if isinstance(coordinate, dict):
                    lat_str = coordinate.get('lat')
                    long_str = coordinate.get('long')
                elif isinstance(coordinate, str):
                    lat_str, long_str = coordinate.split(',')
                else:
                    raise ValueError("Invalid coordinate format")


                logger.info(
                    f"Trying to convert coordinates: lat_str={repr(lat_str)}, long_str={repr(long_str)}")


                lat = float(lat_str.replace("'", "").replace("\"", "").strip())
                long = float(long_str.replace("'", "").replace("\"", "").strip())

                station_coords = (lat, long)

                is_on_route = any(
                    geodesic(station_coords, route_coord).kilometers <= 5 for route_coord in route_coordinates)
                if is_on_route:
                    stations_on_route.append(station)

                for station_n in stations_on_route:
                    station_coords = (float(station_n["coordinate"]["lat"]), float(station_n["coordinate"]["long"]))

                    distance = geodesic(city1, station_coords).kilometers
                    if distance < min_distance:
                        min_distance = distance
                        nearest_station = station_n

            except (KeyError, ValueError, TypeError) as e:
                logger.error(f"Error converting coordinates for station: {station}. Error: {e}")
                continue


        success_response = {
            "status": "success",
            "message": "Route calculation successful!",
            "route_details": "details info",
            "distance": distance,
            "stations_on_route": stations_on_route,
            "nearest_station": nearest_station
        }
        logger.info(success_response)
        return web.json_response(success_response)


    except (aiohttp.ClientError, TimeoutError, googlemaps.exceptions.ApiError) as e:
        logger.error(f"Error: {e}")
        return web.json_response({"error": "Error fetching or processing route data"}, status=500)

    except geopy.exc.GeocoderTimedOut:
        logger.error("Geocoding service timed out")
        return web.json_response({"error": "Error fetching geocoding data"}, status=500)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


def _create_error_response(message: str, status: int = 400) -> web.Response:
    logger.error(message)
    return web.json_response({"error": message}, status=status)
