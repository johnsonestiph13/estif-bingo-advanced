# telegram-bot/bot/texts/__init__.py
# Estif Bingo 24/7 - Complete Texts Module Exports
# Includes: Main texts, Game texts, Error messages, Emoji mappings

from .locales import TEXTS, get_text, get_supported_languages, get_language_name

# ==================== GAME TEXTS ====================
from .game_texts import (
    GAME_TEXTS,
    GAME_MESSAGES,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    INFO_MESSAGES,
    ADMIN_MESSAGES,
    TRANSFER_MESSAGES
)

# ==================== EMOJIS ====================
from .emojis import EMOJIS, get_emoji

# ==================== HELPER FUNCTIONS ====================

def get_game_text(key: str, lang: str = 'en', **kwargs) -> str:
    """Get game-specific localized text"""
    try:
        text = GAME_TEXTS.get(lang, GAME_TEXTS['en']).get(key, GAME_TEXTS['en'].get(key, f"Missing game text: {key}"))
        if kwargs:
            text = text.format(**kwargs)
        return text
    except Exception:
        return f"Missing game text: {key}"


def get_error_message(error_type: str, lang: str = 'en', **kwargs) -> str:
    """Get localized error message"""
    try:
        text = ERROR_MESSAGES.get(lang, ERROR_MESSAGES['en']).get(error_type, ERROR_MESSAGES['en']['default'])
        if kwargs:
            text = text.format(**kwargs)
        return text
    except Exception:
        return ERROR_MESSAGES.get('en', {}).get('default', "An error occurred")


def get_success_message(success_type: str, lang: str = 'en', **kwargs) -> str:
    """Get localized success message"""
    try:
        text = SUCCESS_MESSAGES.get(lang, SUCCESS_MESSAGES['en']).get(success_type, SUCCESS_MESSAGES['en']['default'])
        if kwargs:
            text = text.format(**kwargs)
        return text
    except Exception:
        return SUCCESS_MESSAGES.get('en', {}).get('default', "Operation successful")


def format_with_emoji(text: str, emoji_key: str = None) -> str:
    """Format text with emoji prefix"""
    if emoji_key:
        emoji = get_emoji(emoji_key)
        return f"{emoji} {text}"
    return text


# ==================== TEXT CONSTANTS ====================

class TextConstants:
    """Centralized text constants for common messages"""
    
    # Common prefixes
    ERROR_PREFIX = f"{get_emoji('error')} Error:"
    WARNING_PREFIX = f"{get_emoji('warning')} Warning:"
    SUCCESS_PREFIX = f"{get_emoji('success')} Success:"
    INFO_PREFIX = f"{get_emoji('info')} Info:"
    
    # Common buttons
    BUTTON_BACK = f"{get_emoji('back')} Back"
    BUTTON_CANCEL = f"{get_emoji('error')} Cancel"
    BUTTON_CONFIRM = f"{get_emoji('success')} Confirm"
    BUTTON_REFRESH = f"{get_emoji('refresh')} Refresh"
    BUTTON_HELP = f"{get_emoji('help')} Help"
    BUTTON_SETTINGS = f"{get_emoji('settings')} Settings"
    
    # Game status
    GAME_ACTIVE = f"{get_emoji('active')} Game Active"
    GAME_PAUSED = f"{get_emoji('pause')} Game Paused"
    GAME_ENDED = f"{get_emoji('stop')} Game Ended"
    
    # Financial
    CURRENCY = "ETB"
    CURRENCY_SYMBOL = "Br"
    
    # Time formats
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_ONLY_FORMAT = "%H:%M:%S"


# ==================== VALIDATION ====================

def validate_texts() -> bool:
    """Validate that all required text keys exist"""
    required_keys = [
        'welcome', 'register_prompt', 'register_success',
        'deposit_select', 'balance', 'contact', 'invite'
    ]
    
    missing_keys = []
    for lang in get_supported_languages():
        for key in required_keys:
            if key not in TEXTS.get(lang, {}):
                missing_keys.append(f"{lang}.{key}")
    
    if missing_keys:
        print(f"⚠️ Missing text keys: {missing_keys}")
        return False
    return True


# ==================== EXPORTS ====================
__all__ = [
    # Main texts
    'TEXTS',
    
    # Game texts
    'GAME_TEXTS',
    'GAME_MESSAGES',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    'INFO_MESSAGES',
    'ADMIN_MESSAGES',
    'TRANSFER_MESSAGES',
    
    # Emojis
    'EMOJIS',
    'get_emoji',
    
    # Helper functions
    'get_text',
    'get_game_text',
    'get_error_message',
    'get_success_message',
    'format_with_emoji',
    'get_supported_languages',
    'get_language_name',
    
    # Constants
    'TextConstants',
    
    # Validation
    'validate_texts',
]