from flask import Flask, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os
from datetime import timedelta
from flask import (Flask, request, jsonify, redirect, render_template, send_from_directory, url_for)
from datetime import datetime
import traceback
import os
from app.database import (insert_metric, get_all_metrics, get_client_metrics, get_total_clients, get_total_metrics, get_client_list)
from app.charts import generate_charts
from utils.logger import setup_logger
from dotenv import load_dotenv
load_dotenv()
logger = setup_logger()
app = Flask(__name__)
WHITELIST = {"costindylan@gmail.com","i569540@fontysict.nl", "569540@student.fontys.nl", "ADMIN0525ADMIN"}
def register_routes(app):
    @app.route('/')
    def index():
        """Render the index page."""
        return render_template('index.html')
    
    """Register all routes with the Flask app."""
    @app.route('/verify')
    def verify():
        print('Request for verification page received')
        return render_template('verify.html')
    @app.route('/hello', methods=['POST'])
    def hello():
        name = request.form.get('name')
        if name and name in WHITELIST:
            print(f"Request for hello page received with allowed name={name}")
            return render_template('hello.html', name=name)
        else:
            print(f"Request for hello page received with disallowed or blank name={name} -- redirecting")
            return redirect(url_for('index'))
    @app.route('/dashboard')
    def dashboard():
        """Display the metrics dashboard."""
        try:
            logger.info("Dashboard route accessed")
            
            all_metrics = get_all_metrics(limit=50)
            latest = all_metrics[0] if all_metrics else None
            recent_metrics = list(reversed(get_client_metrics(limit=20)))
            charts = generate_charts(recent_metrics)
            total_clients = get_total_clients()
            total_metrics = get_total_metrics()
            base_url = request.url_root.rstrip('/')
            
            logger.info("✓ Dashboard rendered successfully")
            
            return render_template(
                'dashboard.html',
                metrics=all_metrics,
                latest_metrics=latest,
                charts=charts,
                total_clients=total_clients,
                total_metrics=total_metrics,
                base_url=base_url
            )
        except Exception as e:
            logger.error(f"✗ Dashboard route failed: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Dashboard Error: {str(e)}", 500
    
    @app.route('/api/metrics', methods=['POST'])
    def receive_metrics():
        """API endpoint to receive metrics from external monitoring clients."""
        try:
            logger.info(f"POST /api/metrics from {request.remote_addr}")
            
            data = request.get_json()
            
            if not data:
                logger.warning("✗ No data provided in request")
                return jsonify({'error': 'No data provided'}), 400
            
            data['received_at'] = datetime.now().isoformat()
            client_id = data.get('client_name') or data.get('client_id') or request.remote_addr
            
            logger.info(f"Processing metrics from client: {client_id}")
            
            insert_metric(client_id, data)
            
            logger.info(f"✓ Metrics received successfully from {client_id}")
            
            return jsonify({
                'status': 'success',
                'message': 'Metrics received',
                'client_id': client_id
            }), 200
            
        except Exception as e:
            logger.error(f"✗ Receive metrics failed: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/metrics', methods=['GET'])
    def get_metrics():
        """API endpoint to retrieve stored metrics."""
        try:
            logger.info("GET /api/metrics")
            
            all_metrics = get_all_metrics(limit=1000)
            total_clients = get_total_clients()
            
            logger.info("✓ Metrics retrieved successfully")
            
            return jsonify({
                'total_entries': len(all_metrics),
                'total_clients': total_clients,
                'metrics': all_metrics
            }), 200
        except Exception as e:
            logger.error(f"✗ Get metrics API failed: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/clients', methods=['GET'])
    def get_clients():
        """API endpoint to get list of connected clients."""
        try:
            logger.info("GET /api/clients")
            
            clients = get_client_list()
            
            logger.info("✓ Client list retrieved successfully")
            
            return jsonify({
                'total_clients': len(clients),
                'clients': clients
            }), 200
        except Exception as e:
            logger.error(f"✗ Get clients API failed: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    
    @app.route('/health')
    def health():
        """Health check endpoint for Azure."""
        try:
            logger.info("Health check accessed")
            
            total_clients = get_total_clients()
            
            logger.info("✓ Health check passed")
            
            return jsonify({
                'status': 'healthy',
                'clients': total_clients,
                'timestamp': datetime.now().isoformat()
            }), 200
        except Exception as e:
            logger.error(f"✗ Health check failed: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500