from loguru import logger
import os

# Create logs directory automatically
os.makedirs("logs", exist_ok=True)

# Configure logger
logger.add(
    "logs/app.log",
    rotation="5 MB",
    retention="10 days",
    level="INFO",
    enqueue=True
)

logger.add(
    "logs/error.log",
    rotation="5 MB",
    retention="10 days",
    level="ERROR",
    enqueue=True
)

logger.info("Logger initialized successfully")