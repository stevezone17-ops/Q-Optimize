"""MongoDB connection manager with graceful fallback."""

from typing import Optional, Dict, Any, List
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.app.core.config import settings
from backend.app.core.logging import logger


class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    is_connected: bool = False
    
    # In-memory storage fallback for development/testing when MongoDB is not running
    _memory_store: Dict[str, Dict[str, Dict[str, Any]]] = {
        "problems": {},
        "formulations": {},
        "experiments": {},
        "results": {},
    }

    async def connect_to_database(self) -> bool:
        """Attempt to connect to MongoDB with a short timeout to prevent blocking startup."""
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=1500,
            )
            # Ping database to verify connection
            await self.client.admin.command("ping")
            self.db = self.client[settings.MONGODB_DATABASE]
            self.is_connected = True
            logger.info(f"Successfully connected to MongoDB database '{settings.MONGODB_DATABASE}'")
            return True
        except Exception as e:
            logger.warning(
                f"Could not connect to MongoDB ({e}). Falling back to local in-memory storage for Phase 1 development."
            )
            self.is_connected = False
            self.db = None
            return False

    async def close_database_connection(self) -> None:
        """Close MongoDB client connection."""
        if self.client:
            logger.info("Closing MongoDB connection...")
            self.client.close()
            self.is_connected = False
            logger.info("MongoDB connection closed.")

    async def get_db_status(self) -> Dict[str, Any]:
        """Return connectivity status and mode."""
        if self.is_connected and self.client:
            try:
                await self.client.admin.command("ping")
                return {
                    "connected": True,
                    "engine": "mongodb",
                    "database": settings.MONGODB_DATABASE,
                }
            except Exception:
                self.is_connected = False
        return {
            "connected": False,
            "engine": "in_memory_fallback",
            "message": "Local memory mode active. Start MongoDB on port 27017 for persistent storage.",
        }

    # In-memory collection helpers
    def memory_insert(self, collection: str, item_id: str, data: Dict[str, Any]) -> None:
        if collection not in self._memory_store:
            self._memory_store[collection] = {}
        self._memory_store[collection][item_id] = data

    def memory_get(self, collection: str, item_id: str) -> Optional[Dict[str, Any]]:
        return self._memory_store.get(collection, {}).get(item_id)

    def memory_list(self, collection: str) -> List[Dict[str, Any]]:
        return list(self._memory_store.get(collection, {}).values())

    def memory_delete(self, collection: str, item_id: str) -> bool:
        if collection in self._memory_store and item_id in self._memory_store[collection]:
            del self._memory_store[collection][item_id]
            return True
        return False


db_manager = DatabaseManager()
