# telegram-bot/bot/utils/otp.py
# Estif Bingo 24/7 - Complete OTP (One-Time Password) Utilities
# Includes: Generation, Verification, Hashing, TOTP, Storage, Rate Limiting

import secrets
import hashlib
import hmac
import time
import base64
import re
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, List, Any
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# ==================== CONSTANTS ====================
DEFAULT_OTP_LENGTH = 6
DEFAULT_OTP_EXPIRY_SECONDS = 300  # 5 minutes
MAX_OTP_ATTEMPTS = 3
OTP_RATE_LIMIT_SECONDS = 60  # 1 minute
OTP_RATE_LIMIT_MAX = 5  # Max 5 OTPs per minute

# ==================== OTP GENERATION ====================

def generate_numeric_otp(length: int = DEFAULT_OTP_LENGTH) -> str:
    """
    Generate numeric OTP of specified length
    Example: generate_numeric_otp(6) -> "123456"
    """
    if length < 1:
        raise ValueError("Length must be at least 1")
    if length > 10:
        raise ValueError("Length cannot exceed 10 for numeric OTP")
    
    max_num = 10 ** length
    otp = secrets.randbelow(max_num)
    return str(otp).zfill(length)

def generate_alphanumeric_otp(length: int = 8) -> str:
    """
    Generate alphanumeric OTP (removes similar looking characters)
    Example: generate_alphanumeric_otp(8) -> "A3B9K2M7"
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Removed: 0,1,I,O
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token
    Example: generate_secure_token(32) -> "a1b2c3d4e5f6g7h8i9j0..."
    """
    return secrets.token_urlsafe(length)

def generate_bingo_auth_code() -> str:
    """
    Generate special auth code for Bingo game access
    Format: BINGO-XXXXXX-YYYYYY
    """
    prefix = "BINGO"
    part1 = secrets.token_hex(3).upper()  # 6 chars
    part2 = secrets.token_hex(3).upper()  # 6 chars
    return f"{prefix}-{part1}-{part2}"

def generate_phone_verification_code() -> str:
    """
    Generate 6-digit code for phone verification
    Example: "123456"
    """
    return generate_numeric_otp(6)

# ==================== OTP HASHING ====================

def hash_otp(otp: str, secret: str) -> str:
    """
    Hash OTP with secret for secure storage
    Uses SHA-256 for one-way hashing
    """
    if not otp or not secret:
        raise ValueError("OTP and secret are required")
    combined = f"{otp}:{secret}"
    return hashlib.sha256(combined.encode()).hexdigest()

def verify_hashed_otp(otp: str, hashed: str, secret: str) -> bool:
    """
    Verify OTP against stored hash using constant-time comparison
    Prevents timing attacks
    """
    if not otp or not hashed or not secret:
        return False
    expected = hash_otp(otp, secret)
    return hmac.compare_digest(expected, hashed)

def hash_with_salt(otp: str, salt: bytes = None) -> Tuple[str, str]:
    """
    Hash OTP with random salt for extra security
    Returns (hashed_otp, salt_base64)
    """
    if salt is None:
        salt = secrets.token_bytes(32)
    
    salted_otp = otp.encode() + salt
    hashed = hashlib.pbkdf2_hmac('sha256', salted_otp, salt, 100000)
    return base64.b64encode(hashed).decode(), base64.b64encode(salt).decode()

def verify_salted_otp(otp: str, hashed: str, salt_b64: str) -> bool:
    """Verify salted OTP"""
    salt = base64.b64decode(salt_b64)
    expected, _ = hash_with_salt(otp, salt)
    return hmac.compare_digest(expected, hashed)

# ==================== TIME-BASED OTP (TOTP) ====================

class TOTPGenerator:
    """
    Time-based OTP generator (RFC 6238 compatible)
    Used for 2FA and authenticator apps
    """
    
    def __init__(self, secret: bytes = None, digits: int = 6, interval: int = 30):
        self.secret = secret or secrets.token_bytes(20)
        self.digits = digits
        self.interval = interval
        self._last_used = None
    
    def generate(self, time_offset: int = 0) -> str:
        """Generate TOTP for current time"""
        counter = int((time.time() + time_offset) / self.interval)
        return self._hotp(counter)
    
    def _hotp(self, counter: int) -> str:
        """Generate HOTP for given counter"""
        counter_bytes = counter.to_bytes(8, 'big')
        hmac_hash = hmac.new(self.secret, counter_bytes, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0F
        code = ((hmac_hash[offset] & 0x7F) << 24 |
                (hmac_hash[offset + 1] & 0xFF) << 16 |
                (hmac_hash[offset + 2] & 0xFF) << 8 |
                (hmac_hash[offset + 3] & 0xFF))
        return str(code % (10 ** self.digits)).zfill(self.digits)
    
    def verify(self, otp: str, window: int = 1) -> bool:
        """
        Verify OTP within time window
        window=1 checks current, previous, and next intervals
        """
        # Prevent replay attacks
        current_counter = int(time.time() / self.interval)
        
        for i in range(-window, window + 1):
            counter = current_counter + i
            if self.generate(time_offset=i * self.interval) == otp:
                # Check if this OTP was already used
                if self._last_used == counter:
                    continue
                self._last_used = counter
                return True
        return False
    
    def get_provisioning_uri(self, account_name: str, issuer: str = "EstifBingo") -> str:
        """Get provisioning URI for authenticator app QR code"""
        secret_b32 = base64.b32encode(self.secret).decode().replace('=', '')
        return f"otpauth://totp/{issuer}:{account_name}?secret={secret_b32}&issuer={issuer}"
    
    def get_secret_base32(self) -> str:
        """Get secret as Base32 for authenticator apps"""
        return base64.b32encode(self.secret).decode().replace('=', '')

# ==================== OTP STORAGE (In-Memory) ====================

@dataclass
class OTPRecord:
    """OTP storage record"""
    hashed: str
    expires_at: datetime
    attempts: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


class OTPStore:
    """
    In-memory OTP storage with expiration, rate limiting, and attempt tracking
    """
    
    def __init__(self):
        self._store: Dict[str, OTPRecord] = {}
        self._rate_limiter: Dict[str, List[datetime]] = defaultdict(list)
    
    def store(self, key: str, otp: str, secret: str, expires_seconds: int = DEFAULT_OTP_EXPIRY_SECONDS) -> bool:
        """
        Store OTP with expiration
        Returns True if stored successfully, False if rate limited
        """
        # Check rate limit
        if not self._check_rate_limit(key):
            logger.warning(f"Rate limit exceeded for key: {key}")
            return False
        
        expires_at = datetime.utcnow() + timedelta(seconds=expires_seconds)
        hashed = hash_otp(otp, secret)
        self._store[key] = OTPRecord(hashed=hashed, expires_at=expires_at)
        logger.debug(f"OTP stored for key: {key}, expires at: {expires_at}")
        return True
    
    def verify(self, key: str, otp: str, secret: str) -> Tuple[bool, Optional[str]]:
        """
        Verify and consume OTP
        Returns (is_valid, error_message)
        """
        if key not in self._store:
            return False, "OTP not found or already used"
        
        record = self._store[key]
        
        # Check expiration
        if datetime.utcnow() > record.expires_at:
            del self._store[key]
            return False, "OTP has expired"
        
        # Check attempts
        if record.attempts >= MAX_OTP_ATTEMPTS:
            del self._store[key]
            return False, "Too many failed attempts"
        
        # Verify OTP
        if verify_hashed_otp(otp, record.hashed, secret):
            del self._store[key]
            return True, None
        else:
            record.attempts += 1
            remaining = MAX_OTP_ATTEMPTS - record.attempts
            return False, f"Invalid OTP. {remaining} attempts remaining"
    
    def _check_rate_limit(self, key: str) -> bool:
        """Check if key is rate limited"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=OTP_RATE_LIMIT_SECONDS)
        
        # Clean old entries
        self._rate_limiter[key] = [
            ts for ts in self._rate_limiter[key] if ts > window_start
        ]
        
        if len(self._rate_limiter[key]) >= OTP_RATE_LIMIT_MAX:
            return False
        
        self._rate_limiter[key].append(now)
        return True
    
    def cleanup(self) -> int:
        """Remove expired OTPs and return count"""
        now = datetime.utcnow()
        expired = [k for k, record in self._store.items() if now > record.expires_at]
        for k in expired:
            del self._store[k]
        
        # Clean rate limiter
        window_start = now - timedelta(seconds=OTP_RATE_LIMIT_SECONDS)
        for key in list(self._rate_limiter.keys()):
            self._rate_limiter[key] = [
                ts for ts in self._rate_limiter[key] if ts > window_start
            ]
            if not self._rate_limiter[key]:
                del self._rate_limiter[key]
        
        return len(expired)
    
    def get(self, key: str) -> Optional[OTPRecord]:
        """Get OTP record for key"""
        return self._store.get(key)
    
    def exists(self, key: str) -> bool:
        """Check if OTP exists for key"""
        return key in self._store
    
    def delete(self, key: str) -> bool:
        """Delete OTP for key"""
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics"""
        return {
            'total_otps': len(self._store),
            'rate_limited_keys': len(self._rate_limiter),
            'cleanup_status': 'active'
        }

# ==================== OTP VALIDATION ====================

def is_valid_numeric_otp(otp: str, expected_length: int = DEFAULT_OTP_LENGTH) -> bool:
    """Validate numeric OTP format"""
    if not otp or len(otp) != expected_length:
        return False
    return otp.isdigit()

def is_valid_alphanumeric_otp(otp: str, expected_length: int = 8) -> bool:
    """Validate alphanumeric OTP format"""
    if not otp or len(otp) != expected_length:
        return False
    pattern = r'^[A-HJ-NP-Z2-9]+$'  # Allowed chars only
    return bool(re.match(pattern, otp))

def is_valid_bingo_auth_code(code: str) -> bool:
    """Validate Bingo auth code format"""
    pattern = r'^BINGO-[A-F0-9]{6}-[A-F0-9]{6}$'
    return bool(re.match(pattern, code))

# ==================== OTP FORMATTING ====================

def format_otp_for_display(otp: str, separator: str = ' ') -> str:
    """Format OTP for better readability"""
    if len(otp) == 6:
        return f"{otp[:3]}{separator}{otp[3:]}"
    elif len(otp) == 8:
        return f"{otp[:4]}{separator}{otp[4:]}"
    return otp

def mask_otp(otp: str, visible_chars: int = 2) -> str:
    """Mask OTP for logging (only show last N chars)"""
    if len(otp) <= visible_chars:
        return '*' * len(otp)
    return '*' * (len(otp) - visible_chars) + otp[-visible_chars:]

# ==================== OTP EXPIRY ====================

def get_otp_expiry_message(expiry_seconds: int = DEFAULT_OTP_EXPIRY_SECONDS) -> str:
    """Get user-friendly expiry message"""
    minutes = expiry_seconds // 60
    if minutes < 1:
        return f"{expiry_seconds} seconds"
    elif minutes == 1:
        return "1 minute"
    else:
        return f"{minutes} minutes"

# ==================== OTP LOGGING ====================

def log_otp_generation(key: str, otp: str, context: str = "") -> None:
    """Log OTP generation (masked for security)"""
    masked = mask_otp(otp)
    logger.info(f"OTP generated for {key}: {masked} | Context: {context}")

def log_otp_verification(key: str, success: bool, context: str = "") -> None:
    """Log OTP verification result"""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"OTP verification {status} for {key} | Context: {context}")

# ==================== CONVENIENCE FUNCTIONS ====================

class OTPManager:
    """
    High-level OTP manager for common use cases
    Combines generation, storage, and verification
    """
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.store = OTPStore()
    
    def generate_and_store(self, identifier: str, length: int = DEFAULT_OTP_LENGTH, 
                          expiry_seconds: int = DEFAULT_OTP_EXPIRY_SECONDS) -> Optional[str]:
        """
        Generate OTP and store it
        Returns OTP if successful, None if rate limited
        """
        otp = generate_numeric_otp(length)
        if self.store.store(identifier, otp, self.secret_key, expiry_seconds):
            return otp
        return None
    
    def verify(self, identifier: str, otp: str) -> Tuple[bool, Optional[str]]:
        """Verify OTP and return result"""
        return self.store.verify(identifier, otp, self.secret_key)
    
    def generate_totp(self, account_name: str) -> TOTPGenerator:
        """Generate TOTP for 2FA"""
        totp = TOTPGenerator()
        logger.info(f"TOTP generated for account: {account_name}")
        return totp
    
    def cleanup(self) -> int:
        """Clean up expired OTPs"""
        return self.store.cleanup()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        return self.store.get_stats()

# ==================== GLOBAL INSTANCE ====================
# Use this for application-wide OTP management
_default_otp_manager = None

def get_otp_manager(secret_key: str = None) -> OTPManager:
    """Get or create default OTP manager"""
    global _default_otp_manager
    if _default_otp_manager is None:
        if secret_key is None:
            secret_key = secrets.token_urlsafe(32)
            logger.warning("Using auto-generated secret key for OTP manager")
        _default_otp_manager = OTPManager(secret_key)
    return _default_otp_manager

# ==================== EXPORTS ====================
__all__ = [
    # Generation
    'generate_numeric_otp',
    'generate_alphanumeric_otp',
    'generate_secure_token',
    'generate_bingo_auth_code',
    'generate_phone_verification_code',
    
    # Hashing
    'hash_otp',
    'verify_hashed_otp',
    'hash_with_salt',
    'verify_salted_otp',
    
    # TOTP
    'TOTPGenerator',
    
    # Storage
    'OTPStore',
    'OTPRecord',
    'OTPManager',
    
    # Validation
    'is_valid_numeric_otp',
    'is_valid_alphanumeric_otp',
    'is_valid_bingo_auth_code',
    
    # Formatting
    'format_otp_for_display',
    'mask_otp',
    'get_otp_expiry_message',
    
    # Logging
    'log_otp_generation',
    'log_otp_verification',
    
    # Manager
    'get_otp_manager',
    
    # Constants
    'DEFAULT_OTP_LENGTH',
    'DEFAULT_OTP_EXPIRY_SECONDS',
    'MAX_OTP_ATTEMPTS',
    'OTP_RATE_LIMIT_SECONDS',
    'OTP_RATE_LIMIT_MAX'
]