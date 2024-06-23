import random
import time
from concurrent.futures import ThreadPoolExecutor  # Исправленный импорт

import requests

cities_and_roads = {
    "Berlin": ["A2", "A9", "A10"],
    "Wolfsburg": ["A2"],
    "Munich": ["A9", "A92", "A96"],
    "Hamburg": ["A7", "A1", "A24"],
    "Dresden": ["A4"],
    "Leipzig": ["A9", "A14"],
    "Cologne": ["A4", "A1", "A3"],
    "Frankfurt": ["A3", "A5"],
    "Stuttgart": ["A8", "A81"],
    "Nuremberg": ["A9", "A6"],
    "Hanover": ["A2", "A7"],
    "Bremen": ["A1", "A27"],
    "Dortmund": ["A1", "A2", "A45"],
    "Essen": ["A40", "A52"],
    "Dusseldorf": ["A3", "A46", "A57"],
    "Bonn": ["A555", "A565"],
    "Mannheim": ["A6", "A656"],
    "Karlsruhe": ["A5", "A8"],
    "Freiburg": ["A5"],
    "Heidelberg": ["A5", "A656"],
    "Augsburg": ["A8"],
    "Regensburg": ["A3", "A93"],
    "Wurzburg": ["A3", "A7"],
    "Ulm": ["A8", "A7"],
    "Kiel": ["A215"],
    "Lubeck": ["A1", "A20"],
    "Rostock": ["A19", "A20"],
    "Magdeburg": ["A2", "A14"],
    "Erfurt": ["A4", "A71"],
    "Kassel": ["A7", "A44"],
    "Göttingen": ["A7"],
    "Braunschweig": ["A2", "A391"],
    "Chemnitz": ["A4", "A72"],
    "Halle": ["A14"],
    "Saarbrucken": ["A1", "A6"],
    "Mainz": ["A60", "A63"],
    "Wiesbaden": ["A66", "A643"],
    "Koblenz": ["A48", "A61"],
    "Trier": ["A1", "A64"],
    "Osnabruck": ["A1", "A30"],
    "Oldenburg": ["A28", "A29"],
    "Potsdam": ["A10", "A115"],
    "Schwerin": ["A14", "A24"],
    "Bielefeld": ["A2", "A33"],
    "Bamberg": ["A70", "A73"],
    "Bayreuth": ["A9"],
    "Cottbus": ["A15"],
    "Jena": ["A4"],
    "Gera": ["A4", "A9"],
    "Zwickau": ["A4", "A72"],
    "Darmstadt": ["A5", "A67"],
    "Offenburg": ["A5"],
}


def send_post_request(url, json):
    response = requests.post(url, json=json)
    return response.json()


def generate_requests(base_url, num_requests=10):
    responses = []
    cities = list(cities_and_roads.keys())

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for _ in range(num_requests):
            valid_road_found = False
            while not valid_road_found:
                city1, city2 = random.sample(cities, 2)
                common_roads = list(
                    set(cities_and_roads[city1])
                    & set(cities_and_roads[city2]))
                if common_roads:
                    valid_road_found = True
                    road = random.choice(common_roads)
                    json_data = {
                        "city1": city1,
                        "city2": city2,
                        "road": road,
                        "user_current_distance": random.randint(100, 300),
                        "user_max_distance": random.randint(350, 600),
                    }
                    futures.append(
                        executor.submit(send_post_request, base_url,
                                        json_data))

        for future in futures:
            responses.append(future.result())

    return responses


base_url = "http://localhost:8081/calculate_route"
num_requests = 500
responses = generate_requests(base_url, num_requests)
