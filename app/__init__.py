from flask import Flask, redirect, request
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from utils.logger import setup_logger

logger = setup_logger()

def create_app(config_class=Config):
    """Flask application factory."""
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Add ProxyFix to handle Azure's proxy headers
    # This must come BEFORE routes are registered
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    logger.info("✓ ProxyFix middleware added")
    
    # Force HTTPS redirect
    @app.before_request
    def force_https():
        if request.url.startswith('http://'):
            url = request.url.replace('http://', 'https://', 1)
            logger.info(f"Redirecting HTTP to HTTPS: {url}")
            return redirect(url, code=301)
    
    # Import and register routes (OAuth setup happens here)
    from app import routes
    routes.register_routes(app)
    
    logger.info("Flask application initialized successfully")
    
    return app