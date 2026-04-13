# api/__init__.py
# Estif Bingo 24/7 - API Blueprints Initialization
# All API endpoints for Telegram bot

from flask import Flask
from flask_cors import CORS

# Import all blueprints
from .auth import auth_bp
from .balance_ops import balance_bp
from .commission import commission_bp
from .game_api import game_api_bp
from .webhooks import webhook_bp


def register_blueprints(app: Flask):
    """Register all API blueprints with the Flask app"""
    
    # Register auth blueprint
    app.register_blueprint(auth_bp)
    
    # Register balance operations blueprint
    app.register_blueprint(balance_bp)
    
    # Register commission blueprint
    app.register_blueprint(commission_bp)
    
    # Register game API blueprint (main game endpoints)
    app.register_blueprint(game_api_bp)
    
    # Register webhook blueprint
    app.register_blueprint(webhook_bp)
    
    # Log registered blueprints
    print("✅ Registered API Blueprints:")
    print("   - auth_bp (authentication)")
    print("   - balance_bp (balance operations)")
    print("   - commission_bp (win percentage)")
    print("   - game_api_bp (game endpoints)")
    print("   - webhook_bp (payment webhooks)")


def create_flask_app() -> Flask:
    """Create and configure Flask application"""
    from ..config import FLASK_PORT
    
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app, origins="*")
    
    # Register all blueprints
    register_blueprints(app)
    
    # Add a simple root endpoint
    @app.route('/')
    def index():
        return {
            "name": "Estif Bingo 24/7 Bot API",
            "version": "3.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "game_api": "/api/...",
                "webhooks": "/api/webhook/..."
            }
        }
    
    # Add a catch-all for debugging (optional)
    @app.errorhandler(404)
    def not_found(error):
        return {"success": False, "error": "Endpoint not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"success": False, "error": "Internal server error"}, 500
    
    return app


# Export all blueprints for direct access
__all__ = [
    'auth_bp',
    'balance_bp', 
    'commission_bp',
    'game_api_bp',
    'webhook_bp',
    'register_blueprints',
    'create_flask_app'
]