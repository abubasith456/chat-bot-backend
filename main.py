import logging
import sys
import uvicorn
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("chatbot.log"), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    """Main application function"""
    try:
        # Validate configuration
        settings.validate()

        logger.info("Starting FastAPI chatbot server...")

        # Start server with Uvicorn
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
