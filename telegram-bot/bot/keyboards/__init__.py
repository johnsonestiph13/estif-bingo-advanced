# telegram-bot/bot/keyboards/__init__.py
# Estif Bingo 24/7 - Keyboards Module Exports

# ==================== MAIN KEYBOARDS ====================
from .menu import (
    menu,
    main_menu_inline,
    back_button,
    confirm_keyboard,
    deposit_methods_keyboard,
    cashout_methods_keyboard,
    language_keyboard,
    admin_keyboard
)

# ==================== GAME KEYBOARDS (NEW) ====================
from .game_keyboards import (
    game_menu_keyboard,
    quick_play_keyboard,
    game_control_keyboard,
    cartela_selection_keyboard,
    game_settings_keyboard,
    game_stats_keyboard,
    game_leaderboard_keyboard
)

# ==================== EXPORTS ====================
__all__ = [
    # Main keyboards
    'menu',
    'main_menu_inline',
    'back_button',
    'confirm_keyboard',
    'deposit_methods_keyboard',
    'cashout_methods_keyboard',
    'language_keyboard',
    'admin_keyboard',
    
    # Game keyboards
    'game_menu_keyboard',
    'quick_play_keyboard',
    'game_control_keyboard',
    'cartela_selection_keyboard',
    'game_settings_keyboard',
    'game_stats_keyboard',
    'game_leaderboard_keyboard',
]

# ==================== HELPER FUNCTIONS ====================
def get_keyboard_by_name(name: str, **kwargs):
    """Get keyboard by name for dynamic loading"""
    keyboards = {
        'main': lambda: main_menu_inline(kwargs.get('user')),
        'back': lambda: back_button(kwargs.get('target', 'main')),
        'confirm': lambda: confirm_keyboard(),
        'deposit_methods': lambda: deposit_methods_keyboard(kwargs.get('lang', 'en')),
        'cashout_methods': lambda: cashout_methods_keyboard(kwargs.get('lang', 'en')),
        'language': lambda: language_keyboard(),
        'admin': lambda: admin_keyboard(),
        'game_menu': lambda: game_menu_keyboard(kwargs.get('lang', 'en')),
        'quick_play': lambda: quick_play_keyboard(),
        'game_control': lambda: game_control_keyboard(kwargs.get('game_state', 'active')),
        'cartela_selection': lambda: cartela_selection_keyboard(kwargs.get('max_cartelas', 4)),
        'game_settings': lambda: game_settings_keyboard(kwargs.get('settings', {})),
        'game_stats': lambda: game_stats_keyboard(),
        'game_leaderboard': lambda: game_leaderboard_keyboard(),
    }
    
    keyboard_func = keyboards.get(name)
    if keyboard_func:
        return keyboard_func()
    return None

# ==================== KEYBOARD INFO ====================
KEYBOARDS_INFO = {
    'main': 'Main menu with all options',
    'back': 'Simple back button for navigation',
    'confirm': 'Confirm/Cancel buttons for actions',
    'deposit_methods': 'Payment methods for deposit',
    'cashout_methods': 'Payment methods for cashout',
    'language': 'Language selection (English/Amharic)',
    'admin': 'Admin panel controls',
    'game_menu': 'Game main menu',
    'quick_play': 'Quick play options (1-4 cartelas)',
    'game_control': 'Game control buttons (start/stop/pause)',
    'cartela_selection': 'Cartela selection buttons',
    'game_settings': 'Game settings options',
    'game_stats': 'Statistics view options',
    'game_leaderboard': 'Leaderboard navigation',
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