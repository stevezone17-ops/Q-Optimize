"""MongoDB connection manager with connection pooling, retry resilience, and automated indexing."""

from typing import Optional, Dict, Any, List
import time
import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.app.core.config import settings
from backend.app.core.logging import logger


class DatabaseManager:
    """Enterprise-grade MongoDB manager with pooling, retries, and in-memory test fallback."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    is_connected: bool = False
    
    # Connection Pool Settings
    MAX_POOL_SIZE: int = 50
    MIN_POOL_SIZE: int = 5
    MAX_IDLE_TIME_MS: int = 30000
    CONNECT_TIMEOUT_MS: int = 5000
    SERVER_SELECTION_TIMEOUT_MS: int = 2000

    # In-memory storage fallback for development and testing
    _memory_store: Dict[str, Dict[str, Dict[str, Any]]] = {
        "users": {},
        "problems": {},
        "formulations": {},
        "experiments": {},
        "executions": {},
        "benchmarks": {},
        "results": {},
        "benchmark_datasets": {},
        "experiment_benchmarks": {},
    }

    # Registered index specifications across collections
    INDEX_DEFINITIONS: Dict[str, List[Dict[str, Any]]] = {
        "users": [
            {"keys": [("username", 1)], "unique": True},
            {"keys": [("email", 1)], "unique": True},
            {"keys": [("role", 1)]},
        ],
        "problems": [
            {"keys": [("owner_id", 1)]},
            {"keys": [("problem_type", 1)]},
            {"keys": [("created_at", -1)]},
            {"keys": [("is_deleted", 1)]},
        ],
        "formulations": [
            {"keys": [("problem_id", 1)]},
            {"keys": [("formulation_type", 1)]},
            {"keys": [("created_at", -1)]},
        ],
        "experiments": [
            {"keys": [("owner_id", 1)]},
            {"keys": [("status", 1)]},
            {"keys": [("problem_type", 1)]},
            {"keys": [("created_at", -1)]},
            {"keys": [("is_deleted", 1)]},
        ],
        "executions": [
            {"keys": [("experiment_id", 1)]},
            {"keys": [("status", 1)]},
            {"keys": [("created_at", -1)]},
        ],
        "benchmarks": [
            {"keys": [("status", 1)]},
            {"keys": [("created_at", -1)]},
        ],
        "benchmark_datasets": [
            {"keys": [("problem_type", 1)]},
            {"keys": [("dataset_id", 1)]},
        ],
    }

    _created_indexes: Dict[str, List[str]] = {}

    async def connect_to_database(self) -> bool:
        """Attempt connection with automatic retry and exponential backoff."""
        return await self.connect_with_retry(max_retries=2, initial_delay=0.3)

    async def connect_with_retry(self, max_retries: int = 3, initial_delay: float = 0.5) -> bool:
        """Connect to MongoDB with exponential backoff on transient errors."""
        delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempting MongoDB connection ({attempt}/{max_retries}) at {settings.MONGODB_URI}...")
                self.client = AsyncIOMotorClient(
                    settings.MONGODB_URI,
                    maxPoolSize=self.MAX_POOL_SIZE,
                    minPoolSize=self.MIN_POOL_SIZE,
                    maxIdleTimeMS=self.MAX_IDLE_TIME_MS,
                    connectTimeoutMS=self.CONNECT_TIMEOUT_MS,
                    serverSelectionTimeoutMS=self.SERVER_SELECTION_TIMEOUT_MS,
                    retryWrites=True,
                )
                # Verify server ping
                await self.client.admin.command("ping")
                self.db = self.client[settings.MONGODB_DATABASE]
                self.is_connected = True
                logger.info(f"Connected to MongoDB database '{settings.MONGODB_DATABASE}' with pool size {self.MAX_POOL_SIZE}")
                
                # Auto-initialize indexes
                await self.create_indexes()
                return True
            except Exception as e:
                logger.warning(f"MongoDB connection attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2

        logger.warning("MongoDB unavailable after retries. Operating in in-memory resilience mode.")
        self.is_connected = False
        self.db = None
        # Initialize in-memory indexes
        await self.create_indexes()
        return False

    async def create_indexes(self) -> Dict[str, List[str]]:
        """Provision all required indexes across database collections."""
        results: Dict[str, List[str]] = {}
        for coll_name, index_specs in self.INDEX_DEFINITIONS.items():
            results[coll_name] = []
            if self.is_connected and self.db is not None:
                try:
                    for spec in index_specs:
                        keys = spec["keys"]
                        unique = spec.get("unique", False)
                        name = await self.db[coll_name].create_index(keys, unique=unique)
                        results[coll_name].append(name)
                except Exception as e:
                    logger.error(f"Failed to create index on collection '{coll_name}': {e}")
            else:
                # In-memory index registration tracking
                for spec in index_specs:
                    keys = spec["keys"]
                    idx_name = "_".join(f"{k}_{v}" for k, v in keys)
                    results[coll_name].append(idx_name)

        self._created_indexes = results
        logger.info(f"Indexed collections initialized: {list(results.keys())}")
        return results

    async def close_database_connection(self) -> None:
        """Gracefully terminate client connection and close connection pools."""
        if self.client:
            logger.info("Closing MongoDB connection pool...")
            self.client.close()
            self.is_connected = False
            self.db = None
            logger.info("MongoDB connection closed cleanly.")

    async def get_db_status(self) -> Dict[str, Any]:
        """Inspect connectivity, pool stats, latency, and collection status."""
        if self.is_connected and self.client:
            try:
                t0 = time.perf_counter()
                await self.client.admin.command("ping")
                latency_ms = round((time.perf_counter() - t0) * 1000, 2)

                return {
                    "connected": True,
                    "engine": "mongodb",
                    "database": settings.MONGODB_DATABASE,
                    "latency_ms": latency_ms,
                    "pool_config": {
                        "max_pool_size": self.MAX_POOL_SIZE,
                        "min_pool_size": self.MIN_POOL_SIZE,
                        "max_idle_time_ms": self.MAX_IDLE_TIME_MS,
                    },
                    "indexes_active": len(self._created_indexes),
                }
            except Exception as e:
                self.is_connected = False
                logger.warning(f"MongoDB ping check failed: {e}")

        mem_counts = {k: len(v) for k, v in self._memory_store.items()}
        return {
            "connected": False,
            "engine": "in_memory_fallback",
            "message": "Local memory mode active. Start MongoDB on port 27017 for persistent storage.",
            "collection_counts": mem_counts,
            "indexes_registered": len(self._created_indexes),
        }

    # ------------------ Soft-Delete & Data Operations ------------------

    async def soft_delete(
        self,
        collection: str,
        item_id: str,
        deleted_by: Optional[str] = None,
    ) -> bool:
        """Mark an entity as deleted without physical row destruction, preserving audit trail."""
        now = datetime.now(timezone.utc)
        if self.is_connected and self.db is not None:
            try:
                res = await self.db[collection].update_one(
                    {"id": item_id, "is_deleted": {"$ne": True}},
                    {"$set": {"is_deleted": True, "deleted_at": now, "deleted_by": deleted_by}},
                )
                return res.modified_count > 0
            except Exception as e:
                logger.error(f"MongoDB soft_delete on {collection} failed: {e}")
                return False
        else:
            rec = self.memory_get(collection, item_id)
            if rec and not rec.get("is_deleted", False):
                rec["is_deleted"] = True
                rec["deleted_at"] = now
                rec["deleted_by"] = deleted_by
                self.memory_insert(collection, item_id, rec)
                return True
            return False

    # In-memory collection helpers
    def memory_insert(self, collection: str, item_id: str, data: Dict[str, Any]) -> None:
        if collection not in self._memory_store:
            self._memory_store[collection] = {}
        self._memory_store[collection][item_id] = data

    def memory_get(self, collection: str, item_id: str) -> Optional[Dict[str, Any]]:
        return self._memory_store.get(collection, {}).get(item_id)

    def memory_list(self, collection: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        all_items = list(self._memory_store.get(collection, {}).values())
        if include_deleted:
            return all_items
        return [item for item in all_items if not item.get("is_deleted", False)]

    def memory_delete(self, collection: str, item_id: str) -> bool:
        """Hard delete from memory store."""
        if collection in self._memory_store and item_id in self._memory_store[collection]:
            del self._memory_store[collection][item_id]
            return True
        return False


db_manager = DatabaseManager()
