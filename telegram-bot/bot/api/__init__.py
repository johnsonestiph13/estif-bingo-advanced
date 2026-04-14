# telegram-bot/bot/api/__init__.py
# Estif Bingo 24/7 - API Blueprints Initialization
# All API endpoints for Telegram bot

from flask import Flask, jsonify
from flask_cors import CORS

# Import all blueprints
from .auth import auth_bp
from .balance_ops import balance_bp
from .commission import commission_bp
from .game_api import game_api_bp
from .webhooks import webhook_bp

# ==================== BLUEPRINT REGISTRATION ====================

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


# ==================== FLASK APP FACTORY ====================

def create_flask_app() -> Flask:
    """Create and configure Flask application"""
    from bot.config import config
    
    app = Flask(__name__)
    
    # Configure app
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    
    # Enable CORS for all routes
    CORS(app, origins=config.CORS_ORIGINS if config.CORS_ORIGINS else "*")
    
    # Register all blueprints
    register_blueprints(app)
    
    # Add a simple root endpoint
    @app.route('/')
    def index():
        return jsonify({
            "name": "Estif Bingo 24/7 Bot API",
            "version": "3.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "healthz": "/healthz",
                "ready": "/ready",
                "game_api": "/api/...",
                "webhooks": "/api/webhook/..."
            }
        })
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "service": "telegram-bot-api",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        })
    
    # Healthz endpoint (Kubernetes style)
    @app.route('/healthz')
    def healthz():
        return jsonify({"status": "alive"}), 200
    
    # Readiness endpoint
    @app.route('/ready')
    def ready():
        return jsonify({"status": "ready"}), 200
    
    # Add a catch-all for debugging (optional)
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "error": "Internal server error"}), 500
    
    return app


# ==================== BLUEPRINT LIST ====================

BLUEPRINTS = {
    'auth': auth_bp,
    'balance_ops': balance_bp,
    'commission': commission_bp,
    'game_api': game_api_bp,
    'webhooks': webhook_bp,
}


def get_blueprint(name: str):
    """Get a blueprint by name"""
    return BLUEPRINTS.get(name)


def list_blueprints() -> list:
    """List all registered blueprint names"""
    return list(BLUEPRINTS.keys())


# ==================== EXPORTS ====================

__all__ = [
    # Blueprints
    'auth_bp',
    'balance_bp', 
    'commission_bp',
    'game_api_bp',
    'webhook_bp',
    
    # Blueprint management
    'BLUEPRINTS',
    'get_blueprint',
    'list_blueprints',
    
    # App factory
    'register_blueprints',
    'create_flask_app',
]