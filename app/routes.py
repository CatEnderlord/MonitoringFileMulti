from flask import Flask, redirect, url_for, session, render_template, request, jsonify, send_from_directory
from authlib.integrations.flask_client import OAuth
from functools import wraps
import os
from datetime import timedelta, datetime
import traceback
from app.database import (insert_metric, get_all_metrics, get_client_metrics, get_total_clients, get_total_metrics, get_client_list)
from app.charts import generate_charts
from utils.logger import setup_logger
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger()

WHITELIST = {"costindylan@gmail.com", "i569540@fontysict.nl", "569540@student.fontys.nl"}

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# SESSION AND OAUTH CONFIGURATION - THESE NEED TO BE SET ON THE APP OBJECT
# NOTE: This assumes 'app' is passed into register_routes(app)
# The secret_key and OAuth setup will be done inside register_routes
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# LOGIN DECORATOR - ADDED FOR AUTHENTICATION AND WHITELIST CHECKING
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session:
            return redirect(url_for('login'))
        # Check if user's email is in whitelist
        user_email = session['profile'].get('email')
        if user_email not in WHITELIST:
            return "Access denied. Your email is not authorized.", 403
        return f(*args, **kwargs)
    return decorated
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def register_routes(app):    
    """Register all routes with the Flask app."""
    
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # SESSION AND OAUTH CONFIGURATION - ADDED FOR GOOGLE AUTHENTICATION
    # MUST BE SET FIRST BEFORE ANY ROUTES USE SESSIONS
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    global oauth  # Use the global oauth variable
    
    app.secret_key = "super-secret-key-for-testing-12345"  # HARDCODED FOR TESTING ONLY
    app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    
    # OAuth Setup - Initialize the global oauth object
    oauth = OAuth(app)
    oauth.register(
        name='google',
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    
    # IMPORTANT: Verify your credentials are loaded
    print(f"OAuth Client ID: {os.getenv('GOOGLE_CLIENT_ID')[:20]}..." if os.getenv('GOOGLE_CLIENT_ID') else "WARNING: No Client ID found!")
    print(f"OAuth Client Secret: {'*' * 20}" if os.getenv('GOOGLE_CLIENT_SECRET') else "WARNING: No Client Secret found!")
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # END OAUTH CONFIGURATION
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # MODIFIED - ADDED @login_required DECORATOR AND user_email PARAMETER
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    @app.route('/')
    @login_required
    def verify():
        print('Request for verification page received')
        user_email = session['profile']['email']
        return render_template('verify.html', user_email=user_email)
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # END MODIFICATIONS
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # NEW OAUTH ROUTES - ADDED FOR GOOGLE AUTHENTICATION
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    @app.route('/login')
    def login():
        redirect_uri = url_for('authorize', _external=True)
        return oauth.google.authorize_redirect(redirect_uri)

    @app.route('/authorize')
    def authorize():
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token)
        session['profile'] = user_info
        session.permanent = True
        
        # Check if user is in whitelist
        if user_info.get('email') not in WHITELIST:
            session.clear()
            return "Access denied. Your email is not authorized to access this application.", 403
        
        return redirect('/')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # END NEW OAUTH ROUTES
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # MODIFIED - ADDED @login_required DECORATOR AND logged_in_email PARAMETER
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    @app.route('/hello', methods=['POST'])
    @login_required
    def hello():
        name = request.form.get('name')
        logged_in_email = session['profile']['email']
        
        if name and name in WHITELIST:
            print(f"Request for hello page received with allowed name={name}")
            return render_template('hello.html', name=name, logged_in_email=logged_in_email)
        else:
            print(f"Request for hello page received with disallowed or blank name={name} -- redirecting")
            return redirect(url_for('verify'))
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # END MODIFICATIONS
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # MODIFIED - ADDED @login_required DECORATOR AND user_email PARAMETER
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
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
            user_email = session['profile']['email']
            
            logger.info("✓ Dashboard rendered successfully")
            
            return render_template(
                'dashboard.html',
                metrics=all_metrics,
                latest_metrics=latest,
                charts=charts,
                total_clients=total_clients,
                total_metrics=total_metrics,
                base_url=base_url,
                user_email=user_email
            )
        except Exception as e:
            logger.error(f"✗ Dashboard route failed: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Dashboard Error: {str(e)}", 500
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # END MODIFICATIONS
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
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