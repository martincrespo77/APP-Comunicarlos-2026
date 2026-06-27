import motor.motor_asyncio
from beanie import init_beanie
from app.models import User, Message

# Default to local MongoDB for development
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "comunicarlos_db"

async def init_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    database = client[DB_NAME]
    await init_beanie(database=database, document_models=[User, Message])
