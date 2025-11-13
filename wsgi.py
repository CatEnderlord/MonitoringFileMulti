from app import create_app
from app.database import init_db
from config import Config
from utils.logger import setup_logger

logger = setup_logger()

# Initialize database on startup
try:
    logger.info("Initializing database for production...")
    init_db()
    logger.info("Database initialization complete")
except Exception as e:
    logger.error(f"Database initialization failed: {str(e)}")

# Create the Flask app instance
app = create_app()

if __name__ == "__main__":
    # This allows running with: python wsgi.py
    app.run(host=Config.HOST, port=Config.PORT)