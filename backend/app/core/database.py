"""Async MongoDB connection helper using Motor."""


from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import logger


class DatabaseManager:
    """Manages AsyncIOMotorClient instance and database connection lifecycle."""

    client: AsyncIOMotorClient | None = None  # type: ignore[type-arg]
    db: AsyncIOMotorDatabase | None = None    # type: ignore[type-arg]

    @classmethod
    async def connect_to_database(cls) -> None:
        """Initialize Motor client connection."""
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}...")
        try:
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT_MS,
            )
            cls.db = cls.client[settings.MONGODB_DB_NAME]
            logger.info(f"Connected to database: {settings.MONGODB_DB_NAME}")
        except Exception as e:
            logger.warning(f"Initial MongoDB connection attempt warning: {e}")

    @classmethod
    async def close_database_connection(cls) -> None:
        """Close Motor client connection on shutdown."""
        if cls.client:
            logger.info("Closing MongoDB connection...")
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("MongoDB connection closed.")

    @classmethod
    async def ping_database(cls) -> bool:
        """Check if MongoDB server is responsive."""
        if cls.client is None:
            return False
        try:
            # Perform admin command ping to test connection
            await cls.client.admin.command("ping")
            return True
        except Exception as e:
            logger.debug(f"MongoDB ping failed: {e}")
            return False


db_manager = DatabaseManager()
