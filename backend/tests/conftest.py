import pytest
import pytest_asyncio
import motor.motor_asyncio
from httpx import AsyncClient, ASGITransport
from beanie import init_beanie

from app.main import app
from app.models import User, Message

# Usamos una base de datos de test
TEST_MONGO_URI = "mongodb://localhost:27017"
TEST_DB_NAME = "comunicarlos_test_db"

@pytest_asyncio.fixture(scope="session")
async def db_client():
    client = motor.motor_asyncio.AsyncIOMotorClient(TEST_MONGO_URI)
    database = client[TEST_DB_NAME]
    await init_beanie(database=database, document_models=[User, Message])
    yield client
    # Limpiamos la base de datos de test después de todos los tests
    await client.drop_database(TEST_DB_NAME)
    client.close()

@pytest_asyncio.fixture(scope="function")
async def clean_db(db_client):
    # Limpia las colecciones antes de cada test para aislamientos
    await User.delete_all()
    await Message.delete_all()
    yield

@pytest_asyncio.fixture(scope="session")
async def async_client():
    # Usamos ASGITransport para testear la app FastAPI sin levantar un servidor real
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
