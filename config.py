import os
import secrets
import time

class Config:
    """Configuration class for Flask application."""
    _api_secret_key = None
    _key_generation_time = None
    _KEY_ROTATION_INTERVAL = 1800  # 30 minutes in seconds
    
    @classmethod
    def _generate_new_key(cls):
        """Generate a new 20-character random string."""
        cls._api_secret_key = secrets.token_urlsafe(15)[:20]  # Generate and truncate to exactly 20 chars
        cls._key_generation_time = time.time()
    
    @classmethod
    @property
    def API_SECRET_KEY(cls):
        """Return API secret key, regenerating if 30 minutes have passed."""
        current_time = time.time()
        
        # Generate new key if none exists or if 30 minutes have passed
        if cls._api_secret_key is None or cls._key_generation_time is None or \
           (current_time - cls._key_generation_time) >= cls._KEY_ROTATION_INTERVAL:
            cls._generate_new_key()
        
        return cls._api_secret_key
    
    # Detect environment (Azure sets WEBSITE_INSTANCE_ID)
    IS_AZURE = os.environ.get('WEBSITE_INSTANCE_ID') is not None
    
    # Database configuration
    DB_SERVER = os.environ.get('DB_SERVER', 'azureserverdatabase.database.windows.net')
    DB_NAME = os.environ.get('DB_NAME', 'databasesqlserver')
    DB_USER = os.environ.get('DB_USER', 'databaseadmin')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Enderlord0525')
    
    CONNECTION_STRING = (
        f'DRIVER={{ODBC Driver 18 for SQL Server}};'
        f'SERVER={DB_SERVER};'
        f'DATABASE={DB_NAME};'
        f'UID={DB_USER};'
        f'PWD={DB_PASSWORD};'
        f'Encrypt=yes;'
        f'TrustServerCertificate=no;'
        f'Connection Timeout=30;'
    )
    
    # Application settings
    MAX_ENTRIES = 100
    
    # Port configuration - Azure uses PORT environment variable
    PORT = int(os.environ.get('PORT', 8000))
    
    # Debug mode - only enabled locally by default
    DEBUG = os.environ.get('DEBUG', 'False' if IS_AZURE else 'True').lower() == 'true'
    
    # Host configuration
    HOST = '0.0.0.0'