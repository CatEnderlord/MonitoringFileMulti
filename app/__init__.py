from flask import Flask
from config import Config
from utils.logger import setup_logger

logger = setup_logger()

def create_app(config_class=Config):
    """Flask application factory."""
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Import and register routes
    from app import routes
    routes.register_routes(app)
    
    logger.info("Flask application initialized successfully")
    
    return app