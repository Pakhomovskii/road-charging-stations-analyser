import requests

url = "http://localhost:8080/calculate_route"

data = {
    "city1": "Москва",
    "city2": "Санкт-Петербург",
    "road": "",
    "user_current_distance": 100,
    "user_max_distance": 800
}

response = requests.post(url, json=data)

if response.status_code == 200:
    print("Successful request!")
    data = response.json()
    print(data)
else:
    print(f"Error: {response.status_code}")
    print(response.json())



