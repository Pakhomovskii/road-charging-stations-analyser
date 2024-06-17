import json
import logging
import geopy
import googlemaps
import aiohttp
import math
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


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates the distance between two points on the Earth's surface using the Haversine formula."""
    R = 6371  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


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

        gmaps = Client(key="AIzaSyDyit-EusgkAq70lgAO7RXmu8dYrTesynI")
        directions_result = gmaps.directions(origin=city1, destination=city2, mode="driving")

        if not directions_result:
            return _create_error_response("Unable to get route from Google Maps API", status=500)

        route_polyline = directions_result[0]['overview_polyline']['points']
        route_coordinates = convert.decode_polyline(route_polyline)

        route_coordinates = [(point["lat"], point["lng"]) for point in route_coordinates]

        stations_on_route = []
        # Initialize with a large value, assuming no station is farther than this.
        min_distance = float("inf")
        nearest_station = None  # Initialize with None
        point1, point2 = None, None

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

                    distance = geodesic((location1.latitude, location1.longitude), station_coords).kilometers
                    if distance < min_distance:
                        min_distance = distance
                        nearest_station = station

            except (KeyError, ValueError, TypeError) as e:
                logger.error(f"Error converting coordinates for station: {station}. Error: {e}")
                continue

            # Get maximum distance from input data (replace 'max_distance' with the actual key in your input)
            max_distance = data.get("user_max_distance", float("inf"))
            current_distance = data.get("user_current_distance", 0)  # Default to 0 if not provided

            # 2. Calculate Distances and Check for Unreachable Segments
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

                # 3. Check Reachability to Nearest and Farthest Station
                nearest_station_distance = haversine_distance(location1.latitude, location1.longitude,
                                                              float(stations_on_route[0]["coordinate"]["lat"]),
                                                              float(stations_on_route[0]["coordinate"]["long"]))
                farthest_station_distance = haversine_distance(
                    float(stations_on_route[-1]["coordinate"]["lat"]),
                    float(stations_on_route[-1]["coordinate"]["long"]),
                    location2.latitude, location2.longitude
                )

                # Check reachability to the nearest and farthest station
                if nearest_station_distance > current_distance:
                    unreachable_segments.insert(0, {  # Insert at the beginning
                        "start_point": (location1.latitude, location1.longitude),
                        "end_point": (float(stations_on_route[0]["coordinate"]["lat"]),
                                      float(stations_on_route[0]["coordinate"]["long"])),
                        "distance": nearest_station_distance
                    })
                if farthest_station_distance > max_distance - current_distance:
                    unreachable_segments.append({  # Append at the end
                        "start_point": (float(stations_on_route[-1]["coordinate"]["lat"]),
                                        float(stations_on_route[-1]["coordinate"]["long"])),
                        "end_point": (location2.latitude, location2.longitude),
                        "distance": farthest_station_distance
                    })

            # Update is_reachable based on whether there are unreachable segments
            is_reachable = not unreachable_segments

        success_response = {
            "status": "success",
            "message": "Route calculation successful!",
            "route_details": "details info",
            "distance": distance,
            "stations_on_route": stations_on_route,
            "nearest_station_on_highway": nearest_station,
            "is_reachable": is_reachable,
            # "unreachable_segments": unreachable_segments,
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
