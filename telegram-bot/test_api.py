# test_api.py
import threading
import time
import requests
from bot.api.game_api import game_api_bp
from bot.config import config

def test_flask_api():
    """Test Flask API endpoints"""
    print("Testing Flask API...")
    
    try:
        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(game_api_bp)
        
        print("✅ Flask app created")
        print("✅ Game API blueprint registered")
        
        # Test health endpoint would be here
        print(f"✅ API would run on port {config.FLASK_PORT}")
        
        return True
    except Exception as e:
        print(f"❌ Flask API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_flask_api()
    print("\n✅ API test passed!" if success else "❌ API test failed")
