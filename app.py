import os
import traceback
from app import create_app
from app.database import init_db
from config import Config
from utils.logger import setup_logger

logger = setup_logger()

if __name__ == '__main__':
    try:
        logger.info("="*60)
        logger.info("STARTING FLASK APPLICATION")
        logger.info("="*60)
        logger.info(f"Environment: {'Azure' if Config.IS_AZURE else 'Local'}")
        logger.info(f"Database Server: {Config.DB_SERVER}")
        logger.info(f"Database Name: {Config.DB_NAME}")
        logger.info(f"Database User: {Config.DB_USER}")
        logger.info(f"Debug Mode: {Config.DEBUG}")
        
        # Initialize database
        init_db()
        
        # Create Flask app
        app = create_app()
        
        logger.info(f"Starting Flask server on {Config.HOST}:{Config.PORT}")
        
        # Run with appropriate settings
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
        
    except Exception as e:
        logger.critical(f"✗✗✗ APPLICATION STARTUP FAILED ✗✗✗")
        logger.critical(f"Error: {str(e)}")
        logger.critical(traceback.format_exc())
        raise