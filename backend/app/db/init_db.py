"""Database initialization and schema migration script for Q-Optimize."""

import asyncio
from backend.app.core.logging import logger
from backend.app.db.mongodb import db_manager
from backend.app.services.auth_service import AuthService


async def init_database() -> None:
    """Initialize MongoDB collections, build indexes, and seed admin user."""
    logger.info("Initializing Q-Optimize Database Engine...")
    connected = await db_manager.connect_to_database()
    if connected:
        logger.info("Connected to MongoDB successfully.")
    else:
        logger.info("Operating in in-memory resilience mode.")

    # Provision indexes
    indexes = await db_manager.create_indexes()
    for coll, idx_list in indexes.items():
        logger.info(f"Collection '{coll}' indexed with {len(idx_list)} keys.")

    # Seed Admin User
    admin = await AuthService.seed_default_admin_if_needed()
    if admin:
        logger.info(f"Default admin account verified: {admin.username} ({admin.email})")

    status = await db_manager.get_db_status()
    logger.info(f"Database readiness report: {status}")

    await db_manager.close_database_connection()
    logger.info("Database initialization routine completed successfully.")


if __name__ == "__main__":
    asyncio.run(init_database())

