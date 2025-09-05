from contextlib import asynccontextmanager
import logging

logger = logging.getLogger("backendservice")


@asynccontextmanager
async def lifespan(app):
    """Application lifespan for startup and shutdown initialization."""
    logger.info("BackendService starting up...")
    try:
        yield
    finally:
        logger.info("BackendService shutting down...")
