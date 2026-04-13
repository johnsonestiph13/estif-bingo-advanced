# telegram-bot/bot/utils/security.py
# Estif Bingo 24/7 - Complete Security Utilities
# Includes: JWT, Password hashing, Rate limiting, CSRF, Encryption, Input validation

import re
import secrets
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any, Union, Callable
from functools import wraps
from collections import defaultdict
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

# Flask imports - handle gracefully if not available
try:
    from flask import request as flask_request, jsonify, Response, make_response
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    flask_request = None
    
    class Response:
        def __init__(self, response, status=None, headers=None):
            self.response = response
            self.status = status
            self.headers = headers or {}
    
    def jsonify(*args, **kwargs):
        return {"error": "Flask not available"}
    
    def make_response(data, status=200):
        return {"data": data, "status": status}

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

# Try to import cryptography for advanced encryption
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None

# ==================== CONSTANTS ====================
JWT_EXPIRY_HOURS = 2
JWT_REFRESH_EXPIRY_DAYS = 7
BCRYPT_ROUNDS = 12
CSRF_TOKEN_LENGTH = 32
API_KEY_LENGTH = 32

# ==================== JWT TOKEN MANAGEMENT ====================

def generate_jwt_token(telegram_id: int, username: str, balance: float,
                       secret: str, expires_hours: int = JWT_EXPIRY_HOURS) -> Optional[str]:
    """Generate JWT token for game server authentication"""
    if not JWT_AVAILABLE or jwt is None:
        logger.error("JWT not available - cannot generate token")
        return None
    
    try:
        payload = {
            "telegram_id": telegram_id,
            "username": username,
            "balance": float(balance),
            "exp": datetime.utcnow() + timedelta(hours=expires_hours),
            "iat": datetime.utcnow(),
            "iss": "estif-bingo-bot",
            "aud": "estif-bingo-game"
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        logger.debug(f"JWT token generated for user {telegram_id}")
        return token
    except Exception as e:
        logger.error(f"JWT generation error: {e}")
        return None


def verify_jwt_token(token: str, secret: str) -> Optional[dict]:
    """Verify JWT token and return payload if valid"""
    if not JWT_AVAILABLE or jwt is None:
        logger.error("JWT not available - cannot verify token")
        return None
    
    try:
        payload = jwt.decode(
            token, 
            secret, 
            algorithms=["HS256"],
            audience="estif-bingo-game",
            issuer="estif-bingo-bot"
        )
        logger.debug(f"JWT token verified for user {payload.get('telegram_id')}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


def generate_refresh_token(telegram_id: int, secret: str) -> Optional[str]:
    """Generate refresh token for JWT"""
    if not JWT_AVAILABLE or jwt is None:
        return None
    
    payload = {
        "telegram_id": telegram_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRY_DAYS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def refresh_jwt_token(refresh_token: str, secret: str, username: str, balance: float) -> Optional[str]:
    """Refresh JWT token using refresh token"""
    payload = verify_jwt_token(refresh_token, secret)
    if not payload or payload.get('type') != 'refresh':
        return None
    
    telegram_id = payload.get('telegram_id')
    if not telegram_id:
        return None
    
    return generate_jwt_token(telegram_id, username, balance, secret)


# ==================== PASSWORD HASHING ====================

def hash_password(password: str, rounds: int = BCRYPT_ROUNDS) -> Optional[str]:
    """Hash password using bcrypt with specified rounds"""
    if not BCRYPT_AVAILABLE or bcrypt is None:
        logger.error("bcrypt not available - cannot hash password")
        return None
    
    if not password or len(password) < 6:
        logger.warning("Password too short for hashing")
        return None
    
    try:
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        return None


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash with timing attack protection"""
    if not BCRYPT_AVAILABLE or bcrypt is None:
        logger.error("bcrypt not available - cannot verify password")
        return False
    
    if not password or not hashed:
        return False
    
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def hash_sha256(data: str) -> str:
    """Generate SHA-256 hash of data"""
    return hashlib.sha256(data.encode()).hexdigest()


def hash_hmac(data: str, key: str) -> str:
    """Generate HMAC-SHA256 of data"""
    return hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()


# ==================== API KEY MANAGEMENT ====================

def generate_api_key() -> str:
    """Generate secure API key"""
    return secrets.token_urlsafe(API_KEY_LENGTH)


def validate_api_key(req, api_secret: str) -> bool:
    """Validate API key from request headers"""
    if not FLASK_AVAILABLE or req is None:
        return False
    
    api_key = req.headers.get('X-API-Key')
    if not api_key:
        api_key = req.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not api_key:
        return False
    
    return hmac.compare_digest(api_key, api_secret)


def require_api_key(api_secret: str) -> Callable:
    """Decorator to require API key for Flask routes"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not FLASK_AVAILABLE or flask_request is None:
                return make_response(jsonify({"error": "Flask not available"}), 500)
            
            if not validate_api_key(flask_request, api_secret):
                return make_response(jsonify({"error": "Invalid or missing API key"}), 401)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==================== INPUT VALIDATION ====================

def is_valid_phone(phone: str) -> bool:
    """Validate Ethiopian phone number format"""
    if not phone or not isinstance(phone, str):
        return False
    
    # Support multiple formats: 09XXXXXXXX, 07XXXXXXXX, +2519XXXXXXXX
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    patterns = [
        r'^(09|07)[0-9]{8}$',           # Local: 09XXXXXXXX or 07XXXXXXXX
        r'^\+251[79][0-9]{8}$',         # International: +2519XXXXXXXX
        r'^251[79][0-9]{8}$'            # Without plus: 2519XXXXXXXX
    ]
    
    for pattern in patterns:
        if re.match(pattern, phone):
            return True
    return False


def normalize_phone(phone: str) -> str:
    """Normalize phone number to standard format (09XXXXXXXX)"""
    if not phone:
        return ""
    
    # Remove non-digits
    phone = re.sub(r'\D', '', phone)
    
    # Handle international format
    if phone.startswith('251') and len(phone) == 12:
        phone = '0' + phone[3:]
    elif phone.startswith('251') and len(phone) == 11:
        phone = '0' + phone[2:]
    elif phone.startswith('+251'):
        phone = '0' + phone[4:]
    
    # Validate length
    if len(phone) == 10 and phone.startswith(('09', '07')):
        return phone
    
    return ""


def is_valid_amount(amount: Union[str, float, int], min_amount: float = 10, max_amount: float = 100000) -> bool:
    """Validate amount is positive and within bounds"""
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return False
        if amount_float < min_amount:
            return False
        if amount_float > max_amount:
            return False
        # Check for 2 decimal places max
        if isinstance(amount, str) and '.' in amount:
            decimal_places = len(amount.split('.')[1])
            if decimal_places > 2:
                return False
        return True
    except (ValueError, TypeError):
        return False


def is_valid_email(email: str) -> bool:
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False
    
    # RFC 5322 compliant email regex (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False
    
    # Additional checks
    if len(email) > 254:  # Max email length
        return False
    
    local_part = email.split('@')[0]
    if len(local_part) > 64:  # Max local part length
        return False
    
    return True


def is_valid_telegram_id(telegram_id: Union[str, int]) -> bool:
    """Validate Telegram ID format (positive integer)"""
    try:
        tid = int(telegram_id)
        return tid > 0 and tid <= 2**63 - 1  # Telegram ID range
    except (ValueError, TypeError):
        return False


def is_valid_username(username: str) -> bool:
    """Validate Telegram username format"""
    if not username:
        return False
    
    # Telegram username rules: 5-32 chars, alphanumeric + underscore
    if len(username) < 5 or len(username) > 32:
        return False
    
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$'
    return bool(re.match(pattern, username))


def sanitize_input(text: str, max_length: int = 1000, allow_html: bool = False) -> str:
    """Sanitize user input to prevent injection"""
    if not text:
        return ""
    
    # Convert to string
    text = str(text)
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove HTML if not allowed
    if not allow_html:
        text = re.sub(r'<[^>]*>', '', text)
    
    # Remove dangerous characters
    text = re.sub(r'[<>\"\'`;]', '', text)
    
    # Trim whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def sanitize_username(username: str, default: str = "Player") -> str:
    """Sanitize username (alphanumeric + underscore, max 32 chars)"""
    if not username:
        return default
    
    # Keep only valid characters
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', str(username))
    
    # Ensure it starts with letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'u' + sanitized
    
    # Limit length
    if len(sanitized) > 32:
        sanitized = sanitized[:32]
    
    # Return default if empty
    return sanitized if sanitized else default


def validate_transaction_id(transaction_id: str) -> bool:
    """Validate transaction ID format"""
    if not transaction_id:
        return False
    
    # Format: TXN-YYYYMMDD-XXXXXX
    pattern = r'^TXN-\d{8}-[A-F0-9]{6}$'
    return bool(re.match(pattern, transaction_id))


# ==================== ADVANCED RATE LIMITING ====================

@dataclass
class RateLimitRecord:
    """Rate limit record for a key"""
    requests: List[float] = field(default_factory=list)
    blocked_until: Optional[float] = None
    violation_count: int = 0


class AdvancedRateLimiter:
    """Advanced rate limiter with sliding window and blocklist"""
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 60, 
                 block_seconds: int = 300, max_violations: int = 3):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_seconds = block_seconds
        self.max_violations = max_violations
        self._records: Dict[str, RateLimitRecord] = {}
    
    def is_allowed(self, key: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed
        Returns (is_allowed, retry_after_seconds)
        """
        now = datetime.utcnow().timestamp()
        
        # Get or create record
        if key not in self._records:
            self._records[key] = RateLimitRecord()
        
        record = self._records[key]
        
        # Check if blocked
        if record.blocked_until and now < record.blocked_until:
            retry_after = int(record.blocked_until - now)
            return False, retry_after
        
        # Clean old requests
        window_start = now - self.window_seconds
        record.requests = [ts for ts in record.requests if ts > window_start]
        
        # Check rate limit
        if len(record.requests) >= self.max_requests:
            record.violation_count += 1
            
            # Block if too many violations
            if record.violation_count >= self.max_violations:
                record.blocked_until = now + self.block_seconds
                record.violation_count = 0
                return False, self.block_seconds
            
            return False, self.window_seconds
        
        # Allow request
        record.requests.append(now)
        return True, None
    
    def reset(self, key: str) -> None:
        """Reset rate limit for a key"""
        if key in self._records:
            del self._records[key]
    
    def get_stats(self, key: str) -> Optional[Dict]:
        """Get rate limit statistics for a key"""
        if key not in self._records:
            return None
        
        record = self._records[key]
        now = datetime.utcnow().timestamp()
        window_start = now - self.window_seconds
        active_requests = [ts for ts in record.requests if ts > window_start]
        
        return {
            "active_requests": len(active_requests),
            "max_requests": self.max_requests,
            "violation_count": record.violation_count,
            "is_blocked": record.blocked_until is not None and now < record.blocked_until,
            "blocked_until": record.blocked_until
        }


# Create specialized rate limiters
otp_limiter = AdvancedRateLimiter(max_requests=3, window_seconds=300, block_seconds=900)
deposit_limiter = AdvancedRateLimiter(max_requests=5, window_seconds=600, block_seconds=1800)
cashout_limiter = AdvancedRateLimiter(max_requests=3, window_seconds=600, block_seconds=1800)
api_limiter = AdvancedRateLimiter(max_requests=100, window_seconds=60, block_seconds=300)
game_limiter = AdvancedRateLimiter(max_requests=30, window_seconds=60, block_seconds=120)


# ==================== CSRF PROTECTION ====================

def generate_csrf_token() -> str:
    """Generate secure CSRF token"""
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


def validate_csrf_token(token: str, session_token: str) -> bool:
    """Validate CSRF token using constant-time comparison"""
    if not token or not session_token:
        return False
    return hmac.compare_digest(token, session_token)


# ==================== IP VALIDATION ====================

def get_client_ip(req) -> str:
    """Get client IP address from request (handles proxies)"""
    if not FLASK_AVAILABLE or req is None:
        return "0.0.0.0"
    
    # Check CloudFlare header
    if req.headers.get('CF-Connecting-IP'):
        return req.headers.get('CF-Connecting-IP')
    
    # Check X-Forwarded-For
    if req.headers.get('X-Forwarded-For'):
        return req.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    # Check X-Real-IP
    if req.headers.get('X-Real-IP'):
        return req.headers.get('X-Real-IP')
    
    # Fallback to remote_addr
    return req.remote_addr or '0.0.0.0'


def is_private_ip(ip: str) -> bool:
    """Check if IP is private/internal"""
    private_ranges = [
        r'^10\.',           # 10.0.0.0/8
        r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',  # 172.16.0.0/12
        r'^192\.168\.',     # 192.168.0.0/16
        r'^127\.',          # 127.0.0.0/8
        r'^0\.',            # 0.0.0.0/8
        r'^169\.254\.',     # 169.254.0.0/16
    ]
    
    for pattern in private_ranges:
        if re.match(pattern, ip):
            return True
    return False


def is_ip_blocked(ip: str, blocked_ips: set) -> bool:
    """Check if IP is blocked (supports CIDR)"""
    if not blocked_ips:
        return False
    
    if ip in blocked_ips:
        return True
    
    # Check CIDR blocks
    for blocked in blocked_ips:
        if '/' in blocked:
            if ip_in_cidr(ip, blocked):
                return True
    
    return False


def ip_in_cidr(ip: str, cidr: str) -> bool:
    """Check if IP is in CIDR range"""
    try:
        import ipaddress
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except (ImportError, ValueError):
        return False


# ==================== ADVANCED ENCRYPTION ====================

class EncryptionManager:
    """Advanced encryption manager using Fernet (symmetric encryption)"""
    
    def __init__(self, key: bytes = None):
        if not CRYPTO_AVAILABLE or Fernet is None:
            logger.warning("Cryptography not available - using simple encryption fallback")
            self.use_fernet = False
            self.key = None
        else:
            self.use_fernet = True
            if key is None:
                key = Fernet.generate_key()
            self.key = key
            self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt data using Fernet"""
        if not data:
            return ""
        
        if self.use_fernet:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        else:
            # Fallback to simple encryption
            return simple_encrypt(data, "fallback_key_2024")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet"""
        if not encrypted_data:
            return ""
        
        if self.use_fernet:
            try:
                decoded = base64.b64decode(encrypted_data)
                decrypted = self.cipher.decrypt(decoded)
                return decrypted.decode()
            except Exception as e:
                logger.error(f"Decryption error: {e}")
                return ""
        else:
            return simple_decrypt(encrypted_data, "fallback_key_2024")
    
    @classmethod
    def from_password(cls, password: str, salt: bytes = None) -> 'EncryptionManager':
        """Create encryption manager from password using PBKDF2"""
        if not CRYPTO_AVAILABLE:
            return cls()
        
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return cls(key)


def simple_encrypt(text: str, key: str) -> str:
    """Simple XOR encryption (fallback when cryptography not available)"""
    if not text or not key:
        return ""
    
    key_bytes = key.encode()
    text_bytes = text.encode()
    result = bytearray()
    
    for i, byte in enumerate(text_bytes):
        result.append(byte ^ key_bytes[i % len(key_bytes)])
    
    # Add key hash for verification
    key_hash = hashlib.md5(key.encode()).hexdigest()[:8]
    return key_hash + result.hex()


def simple_decrypt(hex_text: str, key: str) -> str:
    """Simple XOR decryption (fallback when cryptography not available)"""
    if not hex_text or not key:
        return ""
    
    # Extract key hash if present
    if len(hex_text) > 16:
        stored_hash = hex_text[:8]
        hex_text = hex_text[8:]
        
        # Verify key hash
        key_hash = hashlib.md5(key.encode()).hexdigest()[:8]
        if not hmac.compare_digest(stored_hash, key_hash):
            return ""
    
    try:
        key_bytes = key.encode()
        text_bytes = bytes.fromhex(hex_text)
        result = bytearray()
        
        for i, byte in enumerate(text_bytes):
            result.append(byte ^ key_bytes[i % len(key_bytes)])
        
        return result.decode()
    except (ValueError, UnicodeDecodeError):
        return ""


# ==================== DATA MASKING ====================

def mask_phone(phone: str) -> str:
    """Mask phone number for display (e.g., 09******78)"""
    if not phone or len(phone) < 6:
        return phone
    
    phone = normalize_phone(phone)
    if len(phone) == 10:
        return f"{phone[:2]}******{phone[-2:]}"
    return phone[:3] + "****" + phone[-3:]


def mask_email(email: str) -> str:
    """Mask email for display (e.g., u***r@example.com)"""
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@')
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '***' + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_bank_account(account: str) -> str:
    """Mask bank account number"""
    if not account or len(account) < 8:
        return account
    
    return "****" + account[-4:]


# ==================== EXPORTS ====================

__all__ = [
    # JWT
    'generate_jwt_token',
    'verify_jwt_token',
    'generate_refresh_token',
    'refresh_jwt_token',
    
    # Password
    'hash_password',
    'verify_password',
    'hash_sha256',
    'hash_hmac',
    
    # API Keys
    'generate_api_key',
    'validate_api_key',
    'require_api_key',
    
    # Validation
    'is_valid_phone',
    'normalize_phone',
    'is_valid_amount',
    'is_valid_email',
    'is_valid_telegram_id',
    'is_valid_username',
    'sanitize_input',
    'sanitize_username',
    'validate_transaction_id',
    
    # Rate Limiting
    'AdvancedRateLimiter',
    'otp_limiter',
    'deposit_limiter',
    'cashout_limiter',
    'api_limiter',
    'game_limiter',
    
    # CSRF
    'generate_csrf_token',
    'validate_csrf_token',
    
    # IP Validation
    'get_client_ip',
    'is_private_ip',
    'is_ip_blocked',
    'ip_in_cidr',
    
    # Encryption
    'EncryptionManager',
    'simple_encrypt',
    'simple_decrypt',
    
    # Masking
    'mask_phone',
    'mask_email',
    'mask_bank_account',
    
    # Constants
    'JWT_EXPIRY_HOURS',
    'JWT_REFRESH_EXPIRY_DAYS',
    'BCRYPT_ROUNDS',
]

# ==================== INITIALIZATION ====================
# Create default encryption manager
default_encryption = EncryptionManager()