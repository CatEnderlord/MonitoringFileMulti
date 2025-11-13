import pyodbc
import json
import traceback
from datetime import datetime
from config import Config
from utils.logger import setup_logger

logger = setup_logger()

def get_db_connection():
    """Get a database connection to Azure SQL."""
    try:
        logger.info("Attempting database connection...")
        conn = pyodbc.connect(Config.CONNECTION_STRING)
        logger.info("✓ Database connection successful")
        return conn
    except Exception as e:
        logger.error(f"✗ Database connection failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def init_db():
    """Initialize the Azure SQL database tables."""
    try:
        logger.info("Starting database initialization...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Creating metrics table if not exists...")
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='metrics' AND xtype='U')
            CREATE TABLE metrics (
                id INT IDENTITY(1,1) PRIMARY KEY,
                client_id NVARCHAR(255) NOT NULL,
                client_name NVARCHAR(255),
                timestamp NVARCHAR(50) NOT NULL,
                received_at NVARCHAR(50) NOT NULL,
                cpu_percent FLOAT,
                gpu_percent FLOAT,
                ram_json NVARCHAR(MAX),
                ping_ms FLOAT,
                internet_connected BIT,
                raw_data NVARCHAR(MAX),
                created_at DATETIME2 DEFAULT GETDATE()
            )
        ''')
        logger.info("✓ Metrics table created/verified")
        
        logger.info("Creating index on client_id...")
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_client_id' AND object_id = OBJECT_ID('metrics'))
            CREATE INDEX idx_client_id ON metrics(client_id)
        ''')
        logger.info("✓ Index idx_client_id created/verified")
        
        logger.info("Creating index on timestamp...")
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_timestamp' AND object_id = OBJECT_ID('metrics'))
            CREATE INDEX idx_timestamp ON metrics(timestamp DESC)
        ''')
        logger.info("✓ Index idx_timestamp created/verified")
        
        conn.commit()
        conn.close()
        logger.info("✓ Database initialization complete")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def insert_metric(client_id, data):
    """Insert a metric into the database."""
    try:
        logger.info(f"Inserting metric for client: {client_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Extract fields
        client_name = data.get('client_name')
        timestamp = data.get('timestamp')
        received_at = data.get('received_at')
        cpu_percent = data.get('cpu_percent')
        gpu_percent = data.get('gpu_percent')
        ram = data.get('ram')
        ping_ms = data.get('ping_ms')
        internet_connected = data.get('internet_connected')
        
        ram_json = json.dumps(ram) if ram else None
        raw_data = json.dumps(data)
        
        logger.info(f"Data - CPU: {cpu_percent}%, RAM: {ram.get('percent') if ram else 'N/A'}%")
        
        cursor.execute('''
            INSERT INTO metrics 
            (client_id, client_name, timestamp, received_at, cpu_percent, gpu_percent, 
                ram_json, ping_ms, internet_connected, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (client_id, client_name, timestamp, received_at, cpu_percent, gpu_percent,
                ram_json, ping_ms, internet_connected, raw_data))
        
        conn.commit()
        conn.close()
        logger.info(f"✓ Metric inserted for client: {client_id}")
    except Exception as e:
        logger.error(f"✗ Insert metric failed for client {client_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_all_metrics(limit=50):
    """Get all metrics from database."""
    try:
        logger.info(f"Fetching all metrics (limit: {limit})...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT TOP (?) * FROM metrics 
            ORDER BY timestamp DESC
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        metrics = []
        for row in rows:
            metric = json.loads(row.raw_data)
            metric['client_id'] = row.client_id
            metrics.append(metric)
        
        logger.info(f"✓ Retrieved {len(metrics)} metrics")
        return metrics
    except Exception as e:
        logger.error(f"✗ Get all metrics failed: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def get_client_metrics(client_id=None, limit=20):
    """Get metrics for a specific client or all clients."""
    try:
        logger.info(f"Fetching metrics for client: {client_id or 'all'} (limit: {limit})")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if client_id:
            cursor.execute('''
                SELECT TOP (?) * FROM metrics 
                WHERE client_id = ?
                ORDER BY timestamp DESC
            ''', (limit, client_id))
        else:
            cursor.execute('''
                SELECT TOP (?) * FROM metrics 
                ORDER BY timestamp DESC
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        metrics = []
        for row in rows:
            metric = json.loads(row.raw_data)
            metric['client_id'] = row.client_id
            metrics.append(metric)
        
        logger.info(f"✓ Retrieved {len(metrics)} client metrics")
        return metrics
    except Exception as e:
        logger.error(f"✗ Get client metrics failed: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def get_total_clients():
    """Get count of unique clients."""
    try:
        logger.info("Counting total clients...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(DISTINCT client_id) as count FROM metrics')
        count = cursor.fetchone()[0]
        
        conn.close()
        logger.info(f"✓ Total clients: {count}")
        return count
    except Exception as e:
        logger.error(f"✗ Get total clients failed: {str(e)}")
        logger.error(traceback.format_exc())
        return 0

def get_total_metrics():
    """Get total count of metrics."""
    try:
        logger.info("Counting total metrics...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM metrics')
        count = cursor.fetchone()[0]
        
        conn.close()
        logger.info(f"✓ Total metrics: {count}")
        return count
    except Exception as e:
        logger.error(f"✗ Get total metrics failed: {str(e)}")
        logger.error(traceback.format_exc())
        return 0

def get_client_list():
    """Get list of all clients with their info."""
    try:
        logger.info("Fetching client list...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                client_id,
                client_name,
                MAX(timestamp) as last_seen,
                COUNT(*) as metric_count
            FROM metrics
            GROUP BY client_id, client_name
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        clients = []
        for row in rows:
            clients.append({
                'client_id': row.client_id,
                'client_name': row.client_name or row.client_id,
                'last_seen': row.last_seen,
                'metric_count': row.metric_count
            })
        
        logger.info(f"✓ Retrieved {len(clients)} clients")
        return clients
    except Exception as e:
        logger.error(f"✗ Get client list failed: {str(e)}")
        logger.error(traceback.format_exc())
        return []