import json

import pytest
from unittest.mock import AsyncMock, patch

from app.routing import calculate_route


@pytest.mark.asyncio
async def test_calculate_route_success(valid_data, transaction):
    with patch("app.routing.get_distance", return_value=200), \
            patch("app.routing.get_charging_stations", return_value=[]), \
            patch("app.routing.get_route_coordinates",
                  return_value=[(52.4235, 10.7861), (52.5200, 13.4050)]):

        response = await calculate_route(AsyncMock(json=AsyncMock(return_value=valid_data)))

        assert response.status == 200
        data = json.loads(response.text)
        assert data["status"] == "success"


@pytest.mark.asyncio
async def test_calculate_route_missing_field(invalid_data_missing_field, transaction):
    response = await calculate_route(AsyncMock(json=AsyncMock(return_value=invalid_data_missing_field)))
    assert response.status == 400
    data = json.loads(response.text)
    assert "error" in data
    assert data["error"] == "Missing field: road"
