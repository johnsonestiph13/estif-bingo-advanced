# api/auth.py - COMPLETE UPDATED VERSION WITH ENHANCED ERROR HANDLING
import jwt
import logging
import traceback
import asyncio
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, abort
from ..db.database import Database
from ..config import API_SECRET, JWT_SECRET

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


def api_key_required(f):
    """Decorator to require valid API key for bot-to-server calls"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            logger.warning(f"Missing API key from {request.remote_addr}")
            abort(401, description="Missing API key")
        if api_key != API_SECRET:
            logger.warning(f"Invalid API key from {request.remote_addr}: {api_key[:10]}...")
            abort(401, description="Invalid API key")
        return f(*args, **kwargs)
    return decorated


def run_async(coro):
    """Run async coroutine in a new event loop (safe for Flask)"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"run_async error: {e}")
        raise
    finally:
        try:
            loop.close()
        except Exception:
            pass


@auth_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Render"""
    try:
        db_healthy = False
        if Database._pool:
            db_healthy = run_async(Database.health_check())
        
        return jsonify({
            "status": "alive",
            "database": "connected" if db_healthy else "disconnected",
            "service": "telegram-bot-api",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "alive",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@auth_bp.route('/api/verify-token', methods=['POST'])
@api_key_required
def verify_token():
    """Verify JWT token from game server"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"valid": False, "message": "Invalid request body"}), 400
        
        token = data.get('token')
        if not token:
            return jsonify({"valid": False, "message": "Missing token"}), 400
        
        # Decode and verify JWT
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            logger.warning(f"Token expired: {token[:20]}...")
            return jsonify({"valid": False, "message": "Token expired"}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return jsonify({"valid": False, "message": "Invalid token"}), 401
        
        telegram_id = payload.get("telegram_id")
        if not telegram_id:
            return jsonify({"valid": False, "message": "Invalid token payload"}), 401
        
        # Get user from database
        user = run_async(Database.get_user(telegram_id))
        if not user:
            return jsonify({"valid": False, "message": "User not found"}), 404
        
        if not user.get("registered"):
            return jsonify({"valid": False, "message": "User not registered"}), 403
        
        return jsonify({
            "valid": True,
            "telegram_id": telegram_id,
            "username": user.get("username") or f"User{telegram_id}",
            "balance": float(user.get("balance", 0))
        })
        
    except Exception as e:
        logger.exception(f"Token verification error: {e}")
        return jsonify({"valid": False, "message": f"Internal server error"}), 500


@auth_bp.route('/api/exchange-code', methods=['POST'])
@api_key_required
def exchange_code():
    """Exchange one-time code for JWT token (called by game server)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid request body"}), 400
        
        code = data.get('code')
        if not code:
            return jsonify({"success": False, "message": "Missing code"}), 400
        
        # Verify and consume auth code
        telegram_id = run_async(Database.consume_auth_code(code))
        if not telegram_id:
            logger.warning(f"Invalid or expired code: {code[:10]}...")
            return jsonify({"success": False, "message": "Invalid or expired code"}), 401
        
        # Get user from database
        user = run_async(Database.get_user(telegram_id))
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        if not user.get("registered"):
            return jsonify({"success": False, "message": "User not registered"}), 403
        
        # Generate JWT token for game server
        token = jwt.encode(
            {
                "telegram_id": telegram_id,
                "username": user.get("username") or f"User{telegram_id}",
                "balance": float(user.get("balance", 0)),
                "exp": datetime.utcnow() + timedelta(hours=2),
                "iat": datetime.utcnow()
            },
            JWT_SECRET,
            algorithm="HS256"
        )
        
        logger.info(f"✅ Code exchanged for user {telegram_id}")
        
        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "telegram_id": telegram_id,
                "username": user.get("username") or f"User{telegram_id}",
                "balance": float(user.get("balance", 0))
            }
        })
        
    except Exception as e:
        logger.exception(f"Exchange code error: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@auth_bp.route('/api/create-auth-code', methods=['POST'])
@api_key_required
def create_auth_code():
    """Create a new auth code for a user (called by bot when player clicks Play)"""
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        
        if not telegram_id:
            return jsonify({"success": False, "message": "Missing telegram_id"}), 400
        
        # Create auth code
        code = run_async(Database.create_auth_code(telegram_id))
        
        logger.info(f"✅ Auth code created for user {telegram_id}")
        
        return jsonify({
            "success": True,
            "code": code,
            "expires_in": 300  # 5 minutes
        })
        
    except Exception as e:
        logger.exception(f"Create auth code error: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@auth_bp.route('/api/get-user/<int:telegram_id>', methods=['GET'])
@api_key_required
def get_user(telegram_id):
    """Get user details by Telegram ID"""
    try:
        user = run_async(Database.get_user(telegram_id))
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Convert Decimal to float for JSON serialization
        user_data = dict(user)
        if 'balance' in user_data:
            user_data['balance'] = float(user_data['balance'])
        if 'total_deposited' in user_data:
            user_data['total_deposited'] = float(user_data['total_deposited'])
        
        return jsonify({
            "success": True,
            "user": user_data
        })
        
    except Exception as e:
        logger.exception(f"Get user error: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@auth_bp.route('/api/balance/<int:telegram_id>', methods=['GET'])
@api_key_required
def get_balance(telegram_id):
    """Get user balance"""
    try:
        balance = run_async(Database.get_balance, telegram_id)
        
        return jsonify({
            "success": True,
            "balance": balance,
            "can_play": balance >= 10
        })
        
    except Exception as e:
        logger.exception(f"Get balance error: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@auth_bp.route('/api/balance', methods=['POST'])
@api_key_required
def get_balance_post():
    """Get user balance (POST method)"""
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        
        if not telegram_id:
            return jsonify({"success": False, "message": "Missing telegram_id"}), 400
        
        balance = run_async(Database.get_balance, telegram_id)
        
        return jsonify({
            "success": True,
            "balance": balance,
            "can_play": balance >= 10
        })
        
    except Exception as e:
        logger.exception(f"Get balance error: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@auth_bp.route('/api/adjust-balance', methods=['POST'])
@api_key_required
def adjust_balance():
    """Adjust user balance (admin action)"""
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        amount = data.get('amount')
        reason = data.get('reason', 'Admin adjustment')
        
        if not telegram_id or amount is None:
            return jsonify({"success": False, "message": "Missing telegram_id or amount"}), 400
        
        if amount >= 0:
            new_balance = run_async(Database.add_balance, telegram_id, amount, reason)
        else:
            new_balance = run_async(Database.deduct_balance, telegram_id, -amount, reason)
        
        logger.info(f"Balance adjusted for user {telegram_id}: {amount} ETB. New balance: {new_balance}")
        
        return jsonify({
            "success": True,
            "new_balance": new_balance,
            "message": f"Balance adjusted by {amount} ETB"
        })
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        logger.exception(f"Adjust balance error: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@auth_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({"success": False, "message": str(error.description)}), 401


@auth_bp.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "message": str(error.description)}), 400


@auth_bp.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Endpoint not found"}), 404


@auth_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"success": False, "message": "Internal server error"}), 500