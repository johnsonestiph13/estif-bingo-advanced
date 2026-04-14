# telegram-bot/bot/keyboards/game_keyboards.py
# Estif Bingo 24/7 - Game-Specific Keyboards (Simplified for Bot)
# Note: Cartela selection happens inside the web app, not in Telegram

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from typing import Optional, Dict, Any, List
from bot.texts.emojis import get_emoji


# ==================== MAIN GAME MENU ====================
def game_menu_keyboard(lang: str = 'en', balance: float = 0):
    """Create game main menu keyboard with balance display"""
    
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('money')} ቀሪ ሂሳብ: {balance:.2f} ETB", callback_data="show_balance")],
            [InlineKeyboardButton(f"{get_emoji('game')} ጀምር ጨዋታ", callback_data="play")],
            [InlineKeyboardButton(f"{get_emoji('stats')} የእኔ ስታቲስቲክስ", callback_data="game_stats")],
            [InlineKeyboardButton(f"{get_emoji('trophy')} ከፍተኛ ተጫዋቾች", callback_data="game_leaderboard")],
            [InlineKeyboardButton(f"{get_emoji('settings')} ቅንብሮች", callback_data="game_settings")],
            [InlineKeyboardButton(f"{get_emoji('help')} እንዴት መጫወት", callback_data="game_help")],
            [InlineKeyboardButton(f"{get_emoji('back')} ወደ መጀመሪያ ምናሌ", callback_data="main")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('money')} Balance: {balance:.2f} ETB", callback_data="show_balance")],
            [InlineKeyboardButton(f"{get_emoji('game')} Start Game", callback_data="play")],
            [InlineKeyboardButton(f"{get_emoji('stats')} My Statistics", callback_data="game_stats")],
            [InlineKeyboardButton(f"{get_emoji('trophy')} Leaderboard", callback_data="game_leaderboard")],
            [InlineKeyboardButton(f"{get_emoji('settings')} Settings", callback_data="game_settings")],
            [InlineKeyboardButton(f"{get_emoji('help')} How to Play", callback_data="game_help")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back to Main Menu", callback_data="main")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== GAME STATS KEYBOARD ====================
def game_stats_keyboard(lang: str = 'en'):
    """Create game statistics keyboard"""
    
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('stats')} አጠቃላይ ስታት", callback_data="stats_overall")],
            [InlineKeyboardButton(f"{get_emoji('stats')} የዕለት ስታት", callback_data="stats_daily")],
            [InlineKeyboardButton(f"{get_emoji('trophy')} ሳምንታዊ ስታት", callback_data="stats_weekly")],
            [InlineKeyboardButton(f"{get_emoji('money')} አሸናፊነት/ሽንፈት", callback_data="stats_win_loss")],
            [InlineKeyboardButton(f"{get_emoji('refresh')} አድስ", callback_data="stats_refresh")],
            [InlineKeyboardButton(f"{get_emoji('back')} ተመለስ", callback_data="game_menu")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('stats')} Overall Stats", callback_data="stats_overall")],
            [InlineKeyboardButton(f"{get_emoji('stats')} Daily Stats", callback_data="stats_daily")],
            [InlineKeyboardButton(f"{get_emoji('trophy')} Weekly Stats", callback_data="stats_weekly")],
            [InlineKeyboardButton(f"{get_emoji('money')} Win/Loss Ratio", callback_data="stats_win_loss")],
            [InlineKeyboardButton(f"{get_emoji('refresh')} Refresh", callback_data="stats_refresh")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="game_menu")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== LEADERBOARD KEYBOARD ====================
def game_leaderboard_keyboard(lang: str = 'en'):
    """Create leaderboard navigation keyboard"""
    
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('trophy')} ከፍተኛ 10", callback_data="leaderboard_top10")],
            [InlineKeyboardButton(f"{get_emoji('money')} ከፍተኛ አሸናፊዎች", callback_data="leaderboard_winners")],
            [InlineKeyboardButton(f"{get_emoji('star')} ከፍተኛ የማሸነፊያ መጠን", callback_data="leaderboard_winrate")],
            [InlineKeyboardButton(f"{get_emoji('calendar')} ዛሬ", callback_data="leaderboard_today")],
            [InlineKeyboardButton(f"{get_emoji('search')} የኔ ደረጃ", callback_data="leaderboard_my_rank")],
            [InlineKeyboardButton(f"{get_emoji('refresh')} አድስ", callback_data="leaderboard_refresh")],
            [InlineKeyboardButton(f"{get_emoji('back')} ተመለስ", callback_data="game_menu")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('trophy')} Top 10", callback_data="leaderboard_top10")],
            [InlineKeyboardButton(f"{get_emoji('money')} Top Winners", callback_data="leaderboard_winners")],
            [InlineKeyboardButton(f"{get_emoji('star')} Top Win Rate", callback_data="leaderboard_winrate")],
            [InlineKeyboardButton(f"{get_emoji('calendar')} Today", callback_data="leaderboard_today")],
            [InlineKeyboardButton(f"{get_emoji('search')} My Rank", callback_data="leaderboard_my_rank")],
            [InlineKeyboardButton(f"{get_emoji('refresh')} Refresh", callback_data="leaderboard_refresh")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="game_menu")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== GAME SETTINGS KEYBOARD ====================
def game_settings_keyboard(current_settings: Dict[str, Any] = None, lang: str = 'en'):
    """Create game settings keyboard with toggle buttons"""
    
    if current_settings is None:
        current_settings = {}
    
    sound_status = f"{get_emoji('sound')} ON" if current_settings.get('sound', True) else f"{get_emoji('mute')} OFF"
    notifications_status = f"{get_emoji('notification')} ON" if current_settings.get('notifications', True) else f"{get_emoji('notification_off')} OFF"
    
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{sound_status}", callback_data="toggle_sound")],
            [InlineKeyboardButton(f"{notifications_status}", callback_data="toggle_notifications")],
            [InlineKeyboardButton(f"{get_emoji('language')} ቋንቋ", callback_data="change_lang")],
            [InlineKeyboardButton(f"{get_emoji('refresh')} ነባሪ ቅንብሮች", callback_data="reset_settings")],
            [InlineKeyboardButton(f"{get_emoji('back')} ተመለስ", callback_data="game_menu")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{sound_status}", callback_data="toggle_sound")],
            [InlineKeyboardButton(f"{notifications_status}", callback_data="toggle_notifications")],
            [InlineKeyboardButton(f"{get_emoji('language')} Language", callback_data="change_lang")],
            [InlineKeyboardButton(f"{get_emoji('refresh')} Reset to Default", callback_data="reset_settings")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="game_menu")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== HELP/INFO KEYBOARD ====================
def game_help_keyboard(lang: str = 'en'):
    """Create help/info keyboard for game rules"""
    
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('help')} የጨዋታ ህጎች", callback_data="help_rules")],
            [InlineKeyboardButton(f"{get_emoji('money')} እንዴት ማሸነፍ እንደሚቻል", callback_data="help_win")],
            [InlineKeyboardButton(f"{get_emoji('cartela')} ስለ ካርቴላዎች", callback_data="help_cartelas")],
            [InlineKeyboardButton(f"{get_emoji('deposit')} ክፍያ እና ሽልማት", callback_data="help_payment")],
            [InlineKeyboardButton(f"{get_emoji('question')} ተደጋጋሚ ጥያቄዎች", callback_data="help_faq")],
            [InlineKeyboardButton(f"{get_emoji('support')} ደጋፊ", callback_data="help_support")],
            [InlineKeyboardButton(f"{get_emoji('back')} ተመለስ", callback_data="game_menu")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('help')} Game Rules", callback_data="help_rules")],
            [InlineKeyboardButton(f"{get_emoji('money')} How to Win", callback_data="help_win")],
            [InlineKeyboardButton(f"{get_emoji('cartela')} About Cartelas", callback_data="help_cartelas")],
            [InlineKeyboardButton(f"{get_emoji('deposit')} Payments & Prizes", callback_data="help_payment")],
            [InlineKeyboardButton(f"{get_emoji('question')} FAQ", callback_data="help_faq")],
            [InlineKeyboardButton(f"{get_emoji('support')} Support", callback_data="help_support")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="game_menu")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== REPLY KEYBOARDS (Mobile-Friendly) ====================
def game_reply_keyboard(lang: str = 'en'):
    """Create reply keyboard for game (mobile-friendly)"""
    
    if lang == 'am':
        keyboard = [
            ["🎮 ጀምር", "📊 ስታት"],
            ["🏆 ደረጃ", "⚙️ ቅንብር"],
            ["💰 ሂሳብ", "🔙 ምናሌ"]
        ]
    else:
        keyboard = [
            ["🎮 Play", "📊 Stats"],
            ["🏆 Rank", "⚙️ Settings"],
            ["💰 Balance", "🔙 Menu"]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ==================== UTILITY FUNCTIONS ====================
def get_game_keyboard(name: str, **kwargs):
    """Get game keyboard by name for dynamic loading"""
    
    keyboards = {
        'game_menu': game_menu_keyboard,
        'game_stats': game_stats_keyboard,
        'game_leaderboard': game_leaderboard_keyboard,
        'game_settings': game_settings_keyboard,
        'game_help': game_help_keyboard,
        'game_reply': game_reply_keyboard,
    }
    
    keyboard_func = keyboards.get(name)
    if keyboard_func:
        return keyboard_func(**kwargs)
    return None


# ==================== KEYBOARD PRESETS ====================
GAME_KEYBOARD_PRESETS = {
    'minimal': ['game_menu', 'game_stats', 'game_leaderboard'],
    'full': ['game_menu', 'game_stats', 'game_leaderboard', 'game_settings', 'game_help'],
    'mobile': ['game_reply', 'game_menu'],
}


# ==================== EXPORTS ====================
__all__ = [
    'game_menu_keyboard',
    'game_stats_keyboard',
    'game_leaderboard_keyboard',
    'game_settings_keyboard',
    'game_help_keyboard',
    'game_reply_keyboard',
    'get_game_keyboard',
    'GAME_KEYBOARD_PRESETS',
]