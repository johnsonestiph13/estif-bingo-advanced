# api/auth.py (Synchronous version - NO async)
"""Authentication API endpoints for game server"""

import jwt
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, abort
from functools import wraps
from ..db.database import Database
from ..config import API_SECRET, JWT_SECRET

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)


def api_key_required(f):
    """Decorator to require API key for endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_SECRET:
            abort(401, description="Invalid or missing API key")
        return f(*args, **kwargs)
    return decorated


def run_async(coro):
    """Helper to run async function in sync context"""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        # Already in async context, create task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        # No running loop, run directly
        return asyncio.run(coro)


@auth_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    db_healthy = run_async(Database.health_check()) if Database._pool else False
    return jsonify({
        "status": "alive",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    })


@auth_bp.route('/api/verify-token', methods=['POST'])
@api_key_required
def verify_token():
    """Verify JWT token and return user info"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({"valid": False, "message": "Missing token"}), 400
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        telegram_id = payload.get("telegram_id")
        
        if not telegram_id:
            return jsonify({"valid": False, "message": "Invalid token"}), 401
        
        user = run_async(Database.get_user(telegram_id))
        if not user or not user.get("registered"):
            return jsonify({"valid": False, "message": "User not registered"}), 404
        
        return jsonify({
            "valid": True,
            "telegram_id": telegram_id,
            "username": user.get("username") or f"User{telegram_id}",
            "balance": float(user["balance"])
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "message": "Invalid token"}), 401
    except Exception as e:
        logger.exception(f"Token verification error: {e}")
        return jsonify({"valid": False, "message": "Internal error"}), 500


@auth_bp.route('/api/exchange-code', methods=['POST'])
@api_key_required
def exchange_code():
    """Exchange one-time code for JWT token"""
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({"success": False, "message": "Missing code"}), 400
    
    telegram_id = run_async(Database.consume_auth_code(code))
    if not telegram_id:
        return jsonify({"success": False, "message": "Invalid or expired code"}), 401
    
    user = run_async(Database.get_user(telegram_id))
    if not user or not user.get("registered"):
        return jsonify({"success": False, "message": "User not registered"}), 404
    
    token = jwt.encode(
        {
            "telegram_id": telegram_id, 
            "username": user.get("username") or f"User{telegram_id}",
            "balance": float(user["balance"]),
            "exp": datetime.utcnow() + timedelta(hours=2),
            "iat": datetime.utcnow()
        },
        JWT_SECRET, 
        algorithm="HS256"
    )
    
    return jsonify({
        "success": True,
        "token": token,
        "telegram_id": telegram_id,
        "username": user.get("username") or f"User{telegram_id}",
        "balance": float(user["balance"])
    })