# telegram-bot/bot/utils/__init__.py
# Estif Bingo 24/7 - Complete Utilities Module Exports
# Includes: OTP, Logger, Security, and Helper Utilities

# ==================== OTP UTILITIES ====================
from .otp import (
    # Generation
    generate_numeric_otp,
    generate_alphanumeric_otp,
    generate_secure_token,
    generate_bingo_auth_code,
    generate_phone_verification_code,
    
    # Hashing
    hash_otp,
    verify_hashed_otp,
    hash_with_salt,
    verify_salted_otp,
    
    # TOTP
    TOTPGenerator,
    
    # Storage
    OTPStore,
    OTPRecord,
    OTPManager,
    
    # Validation
    is_valid_numeric_otp,
    is_valid_alphanumeric_otp,
    is_valid_bingo_auth_code,
    
    # Formatting
    format_otp_for_display,
    mask_otp,
    get_otp_expiry_message,
    
    # Logging
    log_otp_generation,
    log_otp_verification,
    
    # Manager
    get_otp_manager,
    
    # Constants
    DEFAULT_OTP_LENGTH,
    DEFAULT_OTP_EXPIRY_SECONDS,
    MAX_OTP_ATTEMPTS,
    OTP_RATE_LIMIT_SECONDS,
    OTP_RATE_LIMIT_MAX
)

# ==================== LOGGER UTILITIES ====================
from .logger import (
    # Main logger
    logger,
    setup_logger,
    LogLevel,
    LogLevelManager,
    
    # Structured logging
    log_event,
    log_user_action,
    log_error,
    log_api_call,
    log_database_query,
    log_bot_command,
    log_game_event,
    log_transfer,
    log_security_event,
    
    # Performance
    PerformanceLogger,
    RequestLogger,
    BatchLogger,
    
    # Decorators
    log_function_call,
    log_performance,
    log_error_handler,
    
    # Cleanup
    cleanup_old_logs,
    
    # Classes
    LogEvent,
)

# ==================== SECURITY UTILITIES ====================
from .security import (
    # JWT
    generate_jwt_token,
    verify_jwt_token,
    generate_refresh_token,
    refresh_jwt_token,
    
    # Password
    hash_password,
    verify_password,
    hash_sha256,
    hash_hmac,
    
    # API Keys
    generate_api_key,
    validate_api_key,
    require_api_key,
    
    # Validation
    is_valid_phone,
    normalize_phone,
    is_valid_amount,
    is_valid_email,
    is_valid_telegram_id,
    is_valid_username,
    sanitize_input,
    sanitize_username,
    validate_transaction_id,
    
    # Rate Limiting
    AdvancedRateLimiter,
    otp_limiter,
    deposit_limiter,
    cashout_limiter,
    api_limiter,
    game_limiter,
    
    # CSRF
    generate_csrf_token,
    validate_csrf_token,
    
    # IP Validation
    get_client_ip,
    is_private_ip,
    is_ip_blocked,
    ip_in_cidr,
    
    # Encryption
    EncryptionManager,
    simple_encrypt,
    simple_decrypt,
    
    # Masking
    mask_phone,
    mask_email,
    mask_bank_account,
    
    # Constants
    JWT_EXPIRY_HOURS,
    JWT_REFRESH_EXPIRY_DAYS,
    BCRYPT_ROUNDS,
)

# ==================== HELPER FUNCTIONS ====================

def get_utils_info() -> dict:
    """Get information about available utilities"""
    return {
        "otp": {
            "available": True,
            "generators": ["numeric", "alphanumeric", "bingo_auth", "phone_verification"],
            "totp_support": True,
            "storage": "in-memory"
        },
        "logger": {
            "available": True,
            "handlers": ["console", "file", "error_file", "daily"],
            "json_format": True,
            "color_output": True
        },
        "security": {
            "available": True,
            "jwt_support": JWT_AVAILABLE if 'JWT_AVAILABLE' in dir() else False,
            "bcrypt_support": BCRYPT_AVAILABLE if 'BCRYPT_AVAILABLE' in dir() else False,
            "crypto_support": CRYPTO_AVAILABLE if 'CRYPTO_AVAILABLE' in dir() else False,
            "rate_limiters": ["otp", "deposit", "cashout", "api", "game"]
        }
    }


def setup_all_utils():
    """Initialize all utility modules"""
    # Cleanup old logs
    try:
        cleanup_old_logs()
    except Exception as e:
        logger.warning(f"Failed to cleanup logs: {e}")
    
    # Log initialization
    logger.info("🛠️ Utilities initialized successfully")
    logger.info(f"   - OTP Manager: Available")
    logger.info(f"   - Security: Available")
    logger.info(f"   - Rate Limiters: Active")
    
    return True


# ==================== VERSION ====================
__version__ = "1.0.0"
__author__ = "Estif Bingo Team"
__all__ = [
    # OTP exports
    'generate_numeric_otp',
    'generate_alphanumeric_otp',
    'generate_secure_token',
    'generate_bingo_auth_code',
    'generate_phone_verification_code',
    'hash_otp',
    'verify_hashed_otp',
    'hash_with_salt',
    'verify_salted_otp',
    'TOTPGenerator',
    'OTPStore',
    'OTPRecord',
    'OTPManager',
    'is_valid_numeric_otp',
    'is_valid_alphanumeric_otp',
    'is_valid_bingo_auth_code',
    'format_otp_for_display',
    'mask_otp',
    'get_otp_expiry_message',
    'log_otp_generation',
    'log_otp_verification',
    'get_otp_manager',
    'DEFAULT_OTP_LENGTH',
    'DEFAULT_OTP_EXPIRY_SECONDS',
    'MAX_OTP_ATTEMPTS',
    'OTP_RATE_LIMIT_SECONDS',
    'OTP_RATE_LIMIT_MAX',
    
    # Logger exports
    'logger',
    'setup_logger',
    'LogLevel',
    'LogLevelManager',
    'log_event',
    'log_user_action',
    'log_error',
    'log_api_call',
    'log_database_query',
    'log_bot_command',
    'log_game_event',
    'log_transfer',
    'log_security_event',
    'PerformanceLogger',
    'RequestLogger',
    'BatchLogger',
    'log_function_call',
    'log_performance',
    'log_error_handler',
    'cleanup_old_logs',
    'LogEvent',
    
    # Security exports
    'generate_jwt_token',
    'verify_jwt_token',
    'generate_refresh_token',
    'refresh_jwt_token',
    'hash_password',
    'verify_password',
    'hash_sha256',
    'hash_hmac',
    'generate_api_key',
    'validate_api_key',
    'require_api_key',
    'is_valid_phone',
    'normalize_phone',
    'is_valid_amount',
    'is_valid_email',
    'is_valid_telegram_id',
    'is_valid_username',
    'sanitize_input',
    'sanitize_username',
    'validate_transaction_id',
    'AdvancedRateLimiter',
    'otp_limiter',
    'deposit_limiter',
    'cashout_limiter',
    'api_limiter',
    'game_limiter',
    'generate_csrf_token',
    'validate_csrf_token',
    'get_client_ip',
    'is_private_ip',
    'is_ip_blocked',
    'ip_in_cidr',
    'EncryptionManager',
    'simple_encrypt',
    'simple_decrypt',
    'mask_phone',
    'mask_email',
    'mask_bank_account',
    'JWT_EXPIRY_HOURS',
    'JWT_REFRESH_EXPIRY_DAYS',
    'BCRYPT_ROUNDS',
    
    # Helper functions
    'get_utils_info',
    'setup_all_utils',
    
    # Version
    '__version__',
    '__author__'
]

# ==================== AUTO-INITIALIZATION ====================
# Auto-setup utilities when imported (unless in test mode)
import os
if not os.environ.get('TESTING', False):
    try:
        setup_all_utils()
    except Exception as e:
        # Fallback to basic logging if setup fails
        import logging
        basic_logger = logging.getLogger(__name__)
        basic_logger.warning(f"Failed to setup utilities: {e}")