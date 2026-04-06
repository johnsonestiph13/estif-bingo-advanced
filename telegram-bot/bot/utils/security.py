# utils/security.py
"""Security utilities for authentication, encryption, and validation"""

import re
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any, Union, Callable
from functools import wraps

# Flask imports - handle gracefully if not available
try:
    from flask import request as flask_request, jsonify, Response
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    flask_request = None
    
    # Create a mock Response class when Flask is not available
    class Response:
        def __init__(self, response, status=None, headers=None):
            self.response = response
            self.status = status
            self.headers = headers or {}
    
    def jsonify(*args, **kwargs):
        """Mock jsonify function when Flask is not available"""
        return {"error": "Flask not available"}

# Try to import jwt
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None

# Try to import bcrypt
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    bcrypt = None


# ==================== JWT TOKEN MANAGEMENT ====================

def generate_jwt_token(telegram_id: int, username: str, balance: float,
                       secret: str, expires_hours: int = 2) -> Optional[str]:
    """Generate JWT token for game server authentication"""
    if not JWT_AVAILABLE or jwt is None:
        print("⚠️ JWT not available - cannot generate token")
        return None
    
    payload = {
        "telegram_id": telegram_id,
        "username": username,
        "balance": balance,
        "exp": datetime.utcnow() + timedelta(hours=expires_hours),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_jwt_token(token: str, secret: str) -> Optional[dict]:
    """Verify JWT token and return payload if valid"""
    if not JWT_AVAILABLE or jwt is None:
        print("⚠️ JWT not available - cannot verify token")
        return None
    
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ==================== PASSWORD HASHING ====================

def hash_password(password: str) -> Optional[str]:
    """Hash password using bcrypt"""
    if not BCRYPT_AVAILABLE or bcrypt is None:
        print("⚠️ bcrypt not available - cannot hash password")
        return None
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    if not BCRYPT_AVAILABLE or bcrypt is None:
        print("⚠️ bcrypt not available - cannot verify password")
        return False
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ==================== API KEY VALIDATION ====================

def validate_api_key(req, api_secret: str) -> bool:
    """Validate API key from request headers"""
    if not FLASK_AVAILABLE or req is None:
        return False
    api_key = req.headers.get('X-API-Key')
    if not api_key:
        return False
    return hmac.compare_digest(api_key, api_secret)


def require_api_key(api_secret: str) -> Callable:
    """Decorator to require API key for Flask routes"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not FLASK_AVAILABLE or flask_request is None:
                if FLASK_AVAILABLE:
                    from flask import make_response
                    return make_response(jsonify({"error": "Flask not available"}), 500)
                return {"error": "Flask not available"}, 500
            
            if not validate_api_key(flask_request, api_secret):
                if FLASK_AVAILABLE:
                    from flask import make_response
                    return make_response(jsonify({"error": "Invalid or missing API key"}), 401)
                return {"error": "Invalid or missing API key"}, 401
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==================== INPUT VALIDATION ====================

def is_valid_phone(phone: str) -> bool:
    """Validate Ethiopian phone number format"""
    if not phone:
        return False
    pattern = r'^(09|07)[0-9]{8}$'
    return bool(re.match(pattern, phone))


def is_valid_amount(amount: Union[str, float, int], min_amount: float = 10, max_amount: float = 100000) -> bool:
    """Validate amount is positive and within bounds"""
    try:
        amount_float = float(amount)
        return min_amount <= amount_float <= max_amount
    except (ValueError, TypeError):
        return False


def is_valid_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_telegram_id(telegram_id: Union[str, int]) -> bool:
    """Validate Telegram ID format (positive integer)"""
    try:
        return int(telegram_id) > 0
    except (ValueError, TypeError):
        return False


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection"""
    if not text:
        return ""
    sanitized = re.sub(r'[<>"\']', '', str(text))
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized.strip()


def sanitize_username(username: str) -> str:
    """Sanitize username (alphanumeric + underscore, max 32 chars)"""
    if not username:
        return "Player"
    sanitized = re.sub(r'[^a-zA-Z0-9_ ]', '', str(username))
    if len(sanitized) > 32:
        sanitized = sanitized[:32]
    return sanitized.strip() or "Player"


# ==================== RATE LIMITING ====================

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow().timestamp()
        window_start = now - self.window_seconds
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [ts for ts in self.requests[key] if ts > window_start]
        
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        self.requests[key].append(now)
        return True
    
    def reset(self, key: str) -> None:
        """Reset rate limit for a key"""
        if key in self.requests:
            del self.requests[key]


# Create rate limiters
otp_limiter = RateLimiter(max_requests=3, window_seconds=300)
deposit_limiter = RateLimiter(max_requests=5, window_seconds=600)
cashout_limiter = RateLimiter(max_requests=3, window_seconds=600)


# ==================== CSRF PROTECTION ====================

def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, session_token: str) -> bool:
    """Validate CSRF token"""
    if not token or not session_token:
        return False
    return hmac.compare_digest(token, session_token)


# ==================== IP VALIDATION ====================

def get_client_ip(req) -> str:
    """Get client IP address from request"""
    if not FLASK_AVAILABLE or req is None:
        return "0.0.0.0"
    if req.headers.get('X-Forwarded-For'):
        return req.headers.get('X-Forwarded-For').split(',')[0]
    if req.headers.get('X-Real-IP'):
        return req.headers.get('X-Real-IP')
    return req.remote_addr or '0.0.0.0'


def is_ip_blocked(ip: str, blocked_ips: set) -> bool:
    """Check if IP is blocked"""
    if not blocked_ips:
        return False
    return ip in blocked_ips


# ==================== DATA ENCRYPTION (Simple - for demo only) ====================

def simple_encrypt(text: str, key: str) -> str:
    """Simple XOR encryption (not for production - use proper encryption)"""
    if not text or not key:
        return ""
    key_bytes = key.encode()
    text_bytes = text.encode()
    result = bytearray()
    for i, byte in enumerate(text_bytes):
        result.append(byte ^ key_bytes[i % len(key_bytes)])
    return result.hex()


def simple_decrypt(hex_text: str, key: str) -> str:
    """Simple XOR decryption"""
    if not hex_text or not key:
        return ""
    key_bytes = key.encode()
    try:
        text_bytes = bytes.fromhex(hex_text)
    except ValueError:
        return ""
    result = bytearray()
    for i, byte in enumerate(text_bytes):
        result.append(byte ^ key_bytes[i % len(key_bytes)])
    return result.decode()


# ==================== EXPORTS ====================

__all__ = [
    'generate_jwt_token',
    'verify_jwt_token',
    'hash_password',
    'verify_password',
    'validate_api_key',
    'require_api_key',
    'is_valid_phone',
    'is_valid_amount',
    'is_valid_email',
    'is_valid_telegram_id',
    'sanitize_input',
    'sanitize_username',
    'RateLimiter',
    'otp_limiter',
    'deposit_limiter',
    'cashout_limiter',
    'generate_csrf_token',
    'validate_csrf_token',
    'get_client_ip',
    'is_ip_blocked',
    'simple_encrypt',
    'simple_decrypt'
]