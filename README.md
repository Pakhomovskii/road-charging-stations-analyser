### Road E Helper API

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Aiohttp](https://img.shields.io/badge/Aiohttp-3.9.5-green.svg)](https://docs.aiohttp.org/en/stable/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-orange.svg)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.31-green.svg)](https://www.sqlalchemy.org/)

**Road Helper API** is a powerful tool for calculating routes with electric charging stations and analyzing the reachability of destinations for electric vehicles.

### Features

- **Route Calculation:** Determines the optimal route between two cities.
- **Charging Stations:** Locates electric charging stations along the route, taking into account the electric vehicle's range.
- **Reachability Analysis:** Assesses whether the destination is reachable based on the current battery level and maximum range.
- **Database Logging:** Stores information about each request (successful/unsuccessful) and route reachability in a PostgreSQL database for analysis and statistics.

### Technologies

- **Python 3.11:** High-level programming language for backend development.
- **Aiohttp:** Asynchronous framework for building web applications.
- **PostgreSQL:** Robust and reliable relational database for storing information.
- **Asyncpg:** Asynchronous driver for interacting with PostgreSQL.
- **Google Maps API:** Provides route and geolocation data.

### Structure of the project
```yaml
├── app/                   
│   ├── __init__.py        
│   ├── db.py             # Database interaction logic (models)
│   ├── routing.py        # Core route calculation and logic 
├── templates/         
│   ├── __init__.py    
│   ├── constants.py      # Template constants or configurations
├── tests/                 
│   ├── __init__.py
│   ├── conftest.py       # Pytest fixtures and configurations
│   ├── test_routing.py   # Tests for routing logic
├── .gitignore            
├── create_db.sh          # Shell script to create the database
├── generate_data.py      # Script for generating sample data for ML
├── ml_analyzing.py       # Machine learning analysis of the possibility of route
├── README.md             
├── requirements.txt      
├── routes.csv            # Data to analyze
├── server.py             # Main server script to run the application
```
___
### Core Route Calculation
This module is the heart of the Road Helper API, providing the essential logic for calculating routes, finding electric charging stations along the way, and determining if the destination is reachable given the user's electric vehicle's range.

***Functionality:***

*Data Input and Validation:* The calculate_route function receives a request containing the starting city (city1), destination city (city2), highway/road number (road), the user's current distance traveled (user_current_distance), and the maximum range of the vehicle (user_max_distance). It validates this input to ensure data integrity.

Geocoding and Distance Calculation: Using the Geopy library, the function converts city names into geographic coordinates (latitude and longitude). Then, it calculates the total distance between the two cities.

*Fetching Charging Stations:* It fetches data about electric charging stations located along the specified road from an external open source Autobahn API (https://autobahn.api.bund.dev/) 

*Filtering Stations on Route:* The retrieved station data is filtered to keep only those stations that are close to the calculated route.

*Route Coordinates:* Coordinates for the entire route are obtained from the Google Maps API, allowing the system to precisely analyze distances and locations.

*Reachability Analysis:* The core of the algorithm lies in the calculate_reachability function. It checks whether the entire route is reachable by the electric vehicle (with the possibility of charging), taking into account the current battery level and the maximum range. If the route is not entirely reachable, the function identifies specific segments that are beyond the vehicle's range.

*Database Logging:*  A crucial aspect is the interaction with a PostgreSQL database. The function saves information about each route calculation request, including the cities, road, whether the route is reachable, and details of any unreachable segments. This data is valuable for tracking user behavior, identifying popular routes, and analyzing the effectiveness of the system.
___
***Testing:***

This module includes a suite of pytest tests to ensure the correctness and reliability of its functionality.
___
***Error Handling:***

The code includes robust error handling to gracefully handle situations such as invalid input data, and failures in fetching external data. Appropriate error messages and HTTP status codes are returned in such cases.


