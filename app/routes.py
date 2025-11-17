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

WHITELIST = {"costindylan@gmail.com","i569540@fontysict.nl", "569540@student.fontys.nl", "ADMIN0525ADMIN"}

# Login required decorator
def login_required(function):
    def wrapper(*args, **kwargs):
        if 'profile' not in session:
            return redirect('/login')
        email = session['profile'].get('email')
        if email not in WHITELIST:
            return "Access Denied: Your email is not authorized", 403
        return function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    return wrapper

def register_routes(app):
    """Register all routes with the Flask app."""
    
    # Ensure secret key is set on the app
    if not app.secret_key:
        app.secret_key = "super-secret-key-for-testing-12345"
        app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
    
    #=================================================================
    # OAuth Setup with Debug Logging
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    logger.info("=" * 60)
    logger.info("OAUTH CONFIGURATION DEBUG")
    logger.info("=" * 60)
    logger.info(f"CLIENT_ID exists: {bool(client_id)}")
    logger.info(f"CLIENT_ID value: {client_id[:20] if client_id else 'NOT SET'}...")
    logger.info(f"CLIENT_SECRET exists: {bool(client_secret)}")
    logger.info(f"CLIENT_SECRET length: {len(client_secret) if client_secret else 0}")
    logger.info("=" * 60)
    
    oauth = OAuth(app)
    google = oauth.register(
        name='google',
        client_id=client_id,
        client_secret=client_secret,
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
        client_kwargs={'scope': 'email profile'},
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
    )
    
    @app.route('/login')
    def login():
        logger.info("=" * 60)
        logger.info("LOGIN ROUTE ACCESSED")
        logger.info("=" * 60)
        
        google = oauth.create_client('google')
        redirect_uri = url_for('authorize', _external=True, _scheme='https')
        
        logger.info(f"Redirect URI: {redirect_uri}")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request Host: {request.host}")
        logger.info("=" * 60)
        
        return google.authorize_redirect(redirect_uri)
    
    @app.route('/authorize')
    def authorize():
        logger.info("=" * 60)
        logger.info("AUTHORIZE CALLBACK RECEIVED")
        logger.info("=" * 60)
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request args: {request.args}")
        logger.info(f"Has 'code' param: {'code' in request.args}")
        logger.info(f"Has 'state' param: {'state' in request.args}")
        logger.info(f"Has 'error' param: {'error' in request.args}")
        
        if 'error' in request.args:
            logger.error(f"OAuth Error: {request.args.get('error')}")
            logger.error(f"Error description: {request.args.get('error_description')}")
            return f"OAuth Error: {request.args.get('error_description', 'Unknown error')}", 400
        
        logger.info(f"CLIENT_ID being used: {os.getenv('GOOGLE_CLIENT_ID')[:20]}...")
        logger.info(f"CLIENT_SECRET exists: {bool(os.getenv('GOOGLE_CLIENT_SECRET'))}")
        logger.info("=" * 60)
        
        try:
            google = oauth.create_client('google')
            logger.info("Attempting to exchange authorization code for token...")
            token = google.authorize_access_token()
            logger.info("✓ Token exchange successful!")
            
            resp = google.get('userinfo')
            user_info = resp.json()
            logger.info(f"✓ User info retrieved: {user_info.get('email')}")
            
            user = oauth.google.userinfo()
            session['profile'] = user_info
            session.permanent = True
            
            logger.info("✓ Session created, redirecting to home")
            logger.info("=" * 60)
            return redirect('/')
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error("AUTHORIZATION FAILED")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error(traceback.format_exc())
            logger.error("=" * 60)
            raise
    
    @app.route('/logout')
    def logout():
        session.pop('profile', None)
        return redirect('/')
    #=================================================================
    
    @app.route('/')
    @login_required
    def verify():
        print('Request for verification page received')
        email = session['profile']['email']
        return render_template('verify.html', email=email)
    
    @app.route('/hello', methods=['POST'])
    @login_required
    def hello():
        name = request.form.get('name')
        if name and name in WHITELIST:
            print(f"Request for hello page received with allowed name={name}")
            return render_template('hello.html', name=name)
        else:
            print(f"Request for hello page received with disallowed or blank name={name} -- redirecting")
            return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
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