# telegram-bot/bot/keyboards/__init__.py
# Estif Bingo 24/7 - Keyboards Module Exports (UPDATED)

# ==================== MAIN KEYBOARDS ====================
from .menu import (
    menu,
    main_menu_inline,
    main_menu,  # Alias for backward compatibility
    back_button,
    confirm_keyboard,
    deposit_methods_keyboard,
    cashout_methods_keyboard,
    language_keyboard,
    admin_keyboard
)

# ==================== GAME KEYBOARDS (Bot-Only) ====================
# Note: Cartela selection, game control, betting, number selection
# happen inside the web app, not in Telegram bot
from .game_keyboards import (
    game_menu_keyboard,
    game_stats_keyboard,
    game_leaderboard_keyboard,
    game_settings_keyboard,
    game_help_keyboard,
    game_reply_keyboard,
    get_game_keyboard,
    GAME_KEYBOARD_PRESETS
)

# ==================== EXPORTS ====================
__all__ = [
    # Main keyboards
    'menu',
    'main_menu_inline',
    'main_menu',
    'back_button',
    'confirm_keyboard',
    'deposit_methods_keyboard',
    'cashout_methods_keyboard',
    'language_keyboard',
    'admin_keyboard',
    
    # Game keyboards (Bot-only)
    'game_menu_keyboard',
    'game_stats_keyboard',
    'game_leaderboard_keyboard',
    'game_settings_keyboard',
    'game_help_keyboard',
    'game_reply_keyboard',
    'get_game_keyboard',
    'GAME_KEYBOARD_PRESETS',
]

# ==================== HELPER FUNCTIONS ====================
def get_keyboard_by_name(name: str, **kwargs):
    """Get keyboard by name for dynamic loading"""
    keyboards = {
        # Main keyboards
        'main': lambda: main_menu_inline(kwargs.get('user')),
        'back': lambda: back_button(kwargs.get('target', 'main')),
        'confirm': lambda: confirm_keyboard(),
        'deposit_methods': lambda: deposit_methods_keyboard(kwargs.get('lang', 'en')),
        'cashout_methods': lambda: cashout_methods_keyboard(kwargs.get('lang', 'en')),
        'language': lambda: language_keyboard(),
        'admin': lambda: admin_keyboard(),
        
        # Game keyboards (Bot-only)
        'game_menu': lambda: game_menu_keyboard(kwargs.get('lang', 'en'), kwargs.get('balance', 0)),
        'game_stats': lambda: game_stats_keyboard(kwargs.get('lang', 'en')),
        'game_leaderboard': lambda: game_leaderboard_keyboard(kwargs.get('lang', 'en')),
        'game_settings': lambda: game_settings_keyboard(kwargs.get('settings', {}), kwargs.get('lang', 'en')),
        'game_help': lambda: game_help_keyboard(kwargs.get('lang', 'en')),
        'game_reply': lambda: game_reply_keyboard(kwargs.get('lang', 'en')),
    }
    
    keyboard_func = keyboards.get(name)
    if keyboard_func:
        return keyboard_func()
    return None


# ==================== KEYBOARD INFO ====================
KEYBOARDS_INFO = {
    # Main keyboards
    'main': 'Main menu with all options',
    'back': 'Simple back button for navigation',
    'confirm': 'Confirm/Cancel buttons for actions',
    'deposit_methods': 'Payment methods for deposit',
    'cashout_methods': 'Payment methods for cashout',
    'language': 'Language selection (English/Amharic)',
    'admin': 'Admin panel controls',
    
    # Game keyboards (Bot-only)
    'game_menu': 'Game main menu with Start Game button',
    'game_stats': 'Player statistics view options',
    'game_leaderboard': 'Leaderboard navigation',
    'game_settings': 'User preferences (sound, language)',
    'game_help': 'Game rules and help information',
    'game_reply': 'Mobile-friendly reply keyboard for game',
}


# ==================== KEYBOARD STYLES ====================
KEYBOARD_STYLES = {
    'compact': {
        'row_width': 3,
        'resize_keyboard': True,
        'one_time_keyboard': True
    },
    'full': {
        'row_width': 2,
        'resize_keyboard': True,
        'one_time_keyboard': False
    },
    'inline_compact': {
        'row_width': 4,
    },
    'inline_full': {
        'row_width': 1,
    }
}


# ==================== QUICK ACCESS FUNCTIONS ====================
def get_main_keyboard(user=None, lang='en'):
    """Get main menu keyboard"""
    if user:
        return main_menu_inline(user)
    return menu(lang)


def get_deposit_keyboard(lang='en'):
    """Get deposit methods keyboard"""
    return deposit_methods_keyboard(lang)


def get_cashout_keyboard(lang='en'):
    """Get cashout methods keyboard"""
    return cashout_methods_keyboard(lang)


def get_language_keyboard():
    """Get language selection keyboard"""
    return language_keyboard()


def get_admin_keyboard():
    """Get admin panel keyboard"""
    return admin_keyboard()


def get_game_keyboard_simple(lang='en', balance=0):
    """Get simple game menu keyboard"""
    return game_menu_keyboard(lang, balance)


# ==================== VERSION INFO ====================
KEYBOARDS_VERSION = "3.0.0"
KEYBOARDS_AUTHOR = "Estif Bingo Team"