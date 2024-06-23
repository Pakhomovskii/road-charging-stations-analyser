import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from templates.constants import DATABASE_URL



@pytest.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest.fixture
async def transaction(async_engine):
    async with async_engine.begin() as conn:
        yield conn
        await conn.rollback()

@pytest.fixture
def valid_data():
    return {
        "city1": "Wolfsburg",
        "city2": "Berlin",
        "road": "A2",
        "user_current_distance": 220,
        "user_max_distance": 400,
    }


@pytest.fixture
def invalid_data_missing_field():
    return {
        "city1": "Wolfsburg",
        "city2": "Berlin",
        "user_current_distance": 220,
        "user_max_distance": 400,
    }
