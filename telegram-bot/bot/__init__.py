# telegram-bot/bot/__init__.py
# Estif Bingo 24/7 - Main Bot Package Initialization
# Exports all major bot components and provides version info

import sys
import asyncio
from typing import Optional, Dict, Any

# ==================== VERSION INFORMATION ====================
__version__ = "3.0.0"
__author__ = "Estif Bingo Team"
__license__ = "Proprietary"
__description__ = "Estif Bingo 24/7 - Telegram Bot for Bingo Game Management"

# ==================== PACKAGE EXPORTS ====================

# Core modules
from bot.config import Config, config, get_env_info, is_production, is_development
from bot.db.database import Database, database

# API modules
from bot.api.game_api import game_api_bp
from bot.api.webhooks import webhook_bp

# Keyboard modules
from bot.keyboards.menu import (
    menu, main_menu_inline, back_button, confirm_keyboard,
    deposit_methods_keyboard, cashout_methods_keyboard,
    language_keyboard, admin_keyboard
)
from bot.keyboards.game_keyboards import (
    game_menu_keyboard, quick_play_keyboard, cartela_selection_keyboard,
    game_control_keyboard, game_settings_keyboard, game_stats_keyboard,
    game_leaderboard_keyboard, in_game_keyboard, betting_keyboard,
    number_selection_keyboard, game_reply_keyboard, game_help_keyboard,
    get_game_keyboard, GAME_KEYBOARD_PRESETS
)

# Text modules
from bot.texts.locales import TEXTS
from bot.texts.game_texts import (
    GAME_TEXTS, GAME_MESSAGES, ERROR_MESSAGES,
    SUCCESS_MESSAGES, INFO_MESSAGES, ADMIN_MESSAGES, TRANSFER_MESSAGES
)
from bot.texts import (
    get_text, get_game_text, get_error_message, get_success_message,
    format_with_emoji, get_supported_languages, get_language_name,
    TextConstants, EMOJIS, validate_texts
)

# Utility modules
from bot.utils import (
    # OTP utilities
    generate_numeric_otp, generate_alphanumeric_otp, generate_secure_token,
    generate_bingo_auth_code, generate_phone_verification_code,
    TOTPGenerator, OTPStore, OTPManager, get_otp_manager,
    is_valid_numeric_otp, format_otp_for_display, mask_otp,
    
    # Logger utilities
    logger, setup_logger, log_event, log_user_action, log_error,
    log_api_call, log_database_query, log_bot_command, log_game_event,
    log_transfer, log_security_event, PerformanceLogger, RequestLogger,
    log_function_call, log_performance, log_error_handler,
    
    # Security utilities
    generate_jwt_token, verify_jwt_token, generate_refresh_token,
    hash_password, verify_password, generate_api_key, validate_api_key,
    require_api_key, is_valid_phone, normalize_phone, is_valid_amount,
    is_valid_email, sanitize_input, sanitize_username,
    AdvancedRateLimiter, otp_limiter, deposit_limiter, cashout_limiter,
    generate_csrf_token, validate_csrf_token, get_client_ip,
    EncryptionManager, mask_phone, mask_email, mask_bank_account,
)

# Handler modules (lazy imports to avoid circular dependencies)
_HANDLERS = None

def get_handlers():
    """Lazy import handlers to avoid circular dependencies"""
    global _HANDLERS
    if _HANDLERS is None:
        from bot.handlers import (
            start, register, deposit, cashout, balance, invite,
            contact_center, bingo_otp, admin_commands, transfer,
            play_command, game_callback, quick_play_callback,
            stats_callback, leaderboard_callback, back_to_game_callback
        )
        _HANDLERS = {
            'start': start,
            'register': register,
            'deposit': deposit,
            'cashout': cashout,
            'balance': balance,
            'invite': invite,
            'contact_center': contact_center,
            'bingo_otp': bingo_otp,
            'admin_commands': admin_commands,
            'transfer': transfer,
            'play_command': play_command,
            'game_callback': game_callback,
            'quick_play_callback': quick_play_callback,
            'stats_callback': stats_callback,
            'leaderboard_callback': leaderboard_callback,
            'back_to_game_callback': back_to_game_callback,
        }
    return _HANDLERS

# ==================== BOT INITIALIZATION ====================

class BotInitializer:
    """Manages bot initialization and lifecycle"""
    
    _instance: Optional['BotInitializer'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self) -> bool:
        """Initialize all bot components"""
        if self._initialized:
            logger.warning("Bot already initialized")
            return True
        
        try:
            # Initialize database
            await Database.init_pool()
            logger.info("✅ Database initialized")
            
            # Validate texts
            validate_texts()
            logger.info("✅ Texts validated")
            
            # Start OTP manager cleanup task
            otp_manager = get_otp_manager()
            asyncio.create_task(self._cleanup_otp_task(otp_manager))
            
            # Initialize game handlers background tasks
            handlers = get_handlers()
            if 'play_command' in handlers:
                from bot.handlers.game import start_game_handlers
                await start_game_handlers()
                logger.info("✅ Game handlers initialized")
            
            self._initialized = True
            logger.info("🚀 Bot initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Bot initialization failed: {e}")
            return False
    
    async def _cleanup_otp_task(self, otp_manager):
        """Background task to clean up expired OTPs"""
        while True:
            try:
                await asyncio.sleep(60)  # Clean every minute
                cleaned = otp_manager.cleanup()
                if cleaned > 0:
                    logger.debug(f"Cleaned up {cleaned} expired OTPs")
            except Exception as e:
                logger.error(f"OTP cleanup error: {e}")
    
    async def shutdown(self):
        """Graceful shutdown of all components"""
        logger.info("🛑 Shutting down bot...")
        
        try:
            # Close database pool
            await Database.close_pool()
            logger.info("✅ Database pool closed")
            
            self._initialized = False
            logger.info("✅ Bot shutdown complete")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized


# Global initializer instance
bot_initializer = BotInitializer()

# ==================== CONVENIENCE FUNCTIONS ====================

def get_bot_info() -> Dict[str, Any]:
    """Get information about the bot"""
    return {
        "name": "Estif Bingo 24/7",
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "environment": "production" if is_production() else "development",
        "initialized": bot_initializer.is_initialized,
        "features": {
            "game": True,
            "transfer": True,
            "deposit": True,
            "cashout": True,
            "referral": config.ENABLE_REFERRAL,
            "tournament": config.ENABLE_TOURNAMENT,
            "daily_bonus": config.ENABLE_DAILY_BONUS
        },
        "config": get_env_info()
    }


def get_status() -> Dict[str, Any]:
    """Get bot status for health checks"""
    return {
        "status": "alive" if bot_initializer.is_initialized else "initializing",
        "version": __version__,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
        "database": "connected" if Database._pool else "disconnected",
        "active_sessions": getattr(bot_initializer, '_active_sessions', 0)
    }


# ==================== FASTAPI COMPATIBILITY (if needed) ====================

def create_fastapi_app():
    """Create FastAPI app for API endpoints (optional)"""
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(
            title="Estif Bingo API",
            description="Bingo Game API for Telegram Bot",
            version=__version__
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Health check endpoint
        @app.get("/health")
        async def health_check():
            return get_status()
        
        return app
        
    except ImportError:
        logger.debug("FastAPI not installed - skipping FastAPI app creation")
        return None


# ==================== EXPORTS ====================

__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__license__',
    '__description__',
    
    # Core
    'Config',
    'config',
    'Database',
    'database',
    'get_env_info',
    'is_production',
    'is_development',
    
    # API
    'game_api_bp',
    'webhook_bp',
    
    # Keyboards
    'menu',
    'main_menu_inline',
    'back_button',
    'confirm_keyboard',
    'deposit_methods_keyboard',
    'cashout_methods_keyboard',
    'language_keyboard',
    'admin_keyboard',
    'game_menu_keyboard',
    'quick_play_keyboard',
    'cartela_selection_keyboard',
    'game_control_keyboard',
    'game_settings_keyboard',
    'game_stats_keyboard',
    'game_leaderboard_keyboard',
    'in_game_keyboard',
    'betting_keyboard',
    'number_selection_keyboard',
    'game_reply_keyboard',
    'game_help_keyboard',
    'get_game_keyboard',
    'GAME_KEYBOARD_PRESETS',
    
    # Texts
    'TEXTS',
    'GAME_TEXTS',
    'GAME_MESSAGES',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    'INFO_MESSAGES',
    'ADMIN_MESSAGES',
    'TRANSFER_MESSAGES',
    'get_text',
    'get_game_text',
    'get_error_message',
    'get_success_message',
    'format_with_emoji',
    'get_supported_languages',
    'get_language_name',
    'TextConstants',
    'EMOJIS',
    
    # OTP Utilities
    'generate_numeric_otp',
    'generate_alphanumeric_otp',
    'generate_secure_token',
    'generate_bingo_auth_code',
    'generate_phone_verification_code',
    'TOTPGenerator',
    'OTPStore',
    'OTPManager',
    'get_otp_manager',
    'is_valid_numeric_otp',
    'format_otp_for_display',
    'mask_otp',
    
    # Logger Utilities
    'logger',
    'setup_logger',
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
    'log_function_call',
    'log_performance',
    'log_error_handler',
    
    # Security Utilities
    'generate_jwt_token',
    'verify_jwt_token',
    'generate_refresh_token',
    'hash_password',
    'verify_password',
    'generate_api_key',
    'validate_api_key',
    'require_api_key',
    'is_valid_phone',
    'normalize_phone',
    'is_valid_amount',
    'is_valid_email',
    'sanitize_input',
    'sanitize_username',
    'AdvancedRateLimiter',
    'otp_limiter',
    'deposit_limiter',
    'cashout_limiter',
    'generate_csrf_token',
    'validate_csrf_token',
    'get_client_ip',
    'EncryptionManager',
    'mask_phone',
    'mask_email',
    'mask_bank_account',
    
    # Handlers (lazy)
    'get_handlers',
    
    # Initialization
    'BotInitializer',
    'bot_initializer',
    'get_bot_info',
    'get_status',
    'create_fastapi_app',
]

# ==================== AUTO-INITIALIZATION ====================
# Auto-initialize only if not in test mode and not in interactive mode
if not sys.argv[0].endswith('pytest') and not hasattr(sys, 'ps1'):
    # Don't auto-init when importing in interactive shell
    pass  # Let the main.py handle initialization