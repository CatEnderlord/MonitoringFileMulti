import os

class Config:
    """Configuration class for Flask application."""
    API_SECRET_KEY = "SuperSecretKey123!"
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
    HOST = '0.0.0.0'  # Works for both local and Azure