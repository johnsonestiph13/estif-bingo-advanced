# api/__init__.py
"""Flask app factory for API endpoints"""

from flask import Flask
from .auth import auth_bp
from .balance_ops import balance_bp
from .commission import commission_bp
from .webhooks import webhook_bp

def create_flask_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(balance_bp)
    app.register_blueprint(commission_bp)
    app.register_blueprint(webhook_bp)
    
    return app