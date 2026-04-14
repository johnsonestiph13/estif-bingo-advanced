# telegram-bot/bot/keyboards/menu.py
# Estif Bingo 24/7 - Complete Keyboard Menu System
# Includes: Main menu, Deposit, Cashout, Transfer, Game, Admin, Language, Help, About

from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from bot.texts.emojis import get_emoji
from typing import Optional, Dict, Any, List


# ==================== REPLY KEYBOARDS (Main Menu) ====================

def menu(lang: str = 'en'):
    """Return main menu keyboard based on language (Reply Keyboard)"""
    if lang == 'am':
        return ReplyKeyboardMarkup([
            ["🎮 ጨዋታ"],  # Play button on its own row at the top
            ["📝 ተመዝገብ", "💰 ገንዘብ አስገባ"],
            ["💳 ገንዘብ አውጣ", "📞 ደንበኛ አገልግሎት"],
            ["🎉 ጋብዝ", "💸 ገንዘብ አስተላልፍ", "🔐 የቢንጎ ኮድ"],
            ["🎁 የዕለት ቦነስ", "❓ እርዳታ", "ℹ️ ስለ"]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            ["🎮 Play"],  # Play button on its own row at the top
            ["📝 Register", "💰 Deposit"],
            ["💳 Cash Out", "📞 Contact Center"],
            ["🎉 Invite", "💸 Transfer", "🔐 Bingo Code"],
            ["🎁 Daily Bonus", "❓ Help", "ℹ️ About"]
        ], resize_keyboard=True)


# ==================== INLINE MAIN MENU ====================

def main_menu_inline(user: Optional[Dict] = None):
    """Create inline main menu keyboard (for callback queries)"""
    lang = user.get('lang', 'en') if user else 'en'
    
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('game')} ጨዋታ", callback_data="play")],
            [InlineKeyboardButton(f"{get_emoji('register')} ተመዝገብ", callback_data="register")],
            [InlineKeyboardButton(f"{get_emoji('deposit')} ገንዘብ አስገባ", callback_data="deposit")],
            [InlineKeyboardButton(f"{get_emoji('withdraw')} ገንዘብ አውጣ", callback_data="cashout")],
            [InlineKeyboardButton(f"{get_emoji('transfer')} ገንዘብ አስተላልፍ", callback_data="transfer")],
            [InlineKeyboardButton(f"{get_emoji('support')} ደንበኛ አገልግሎት", callback_data="contact")],
            [InlineKeyboardButton(f"{get_emoji('invite')} ጋብዝ", callback_data="invite")],
            [InlineKeyboardButton(f"{get_emoji('bingo')} የቢንጎ ኮድ", callback_data="bingo")],
            [InlineKeyboardButton(f"{get_emoji('gift')} የዕለት ቦነስ", callback_data="daily_bonus")],
            [InlineKeyboardButton(f"{get_emoji('help')} እርዳታ", callback_data="help")],
            [InlineKeyboardButton(f"{get_emoji('info')} ስለ", callback_data="about")],
            [InlineKeyboardButton(f"{get_emoji('language')} ቋንቋ ቀይር", callback_data="change_lang")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('game')} Play", callback_data="play")],
            [InlineKeyboardButton(f"{get_emoji('register')} Register", callback_data="register")],
            [InlineKeyboardButton(f"{get_emoji('deposit')} Deposit", callback_data="deposit")],
            [InlineKeyboardButton(f"{get_emoji('withdraw')} Cash Out", callback_data="cashout")],
            [InlineKeyboardButton(f"{get_emoji('transfer')} Transfer", callback_data="transfer")],
            [InlineKeyboardButton(f"{get_emoji('support')} Contact Center", callback_data="contact")],
            [InlineKeyboardButton(f"{get_emoji('invite')} Invite", callback_data="invite")],
            [InlineKeyboardButton(f"{get_emoji('bingo')} Bingo Code", callback_data="bingo")],
            [InlineKeyboardButton(f"{get_emoji('gift')} Daily Bonus", callback_data="daily_bonus")],
            [InlineKeyboardButton(f"{get_emoji('help')} Help", callback_data="help")],
            [InlineKeyboardButton(f"{get_emoji('info')} About", callback_data="about")],
            [InlineKeyboardButton(f"{get_emoji('language')} Change Language", callback_data="change_lang")]
        ]
    
    return InlineKeyboardMarkup(keyboard)


# ==================== ALIAS FOR BACKWARD COMPATIBILITY ====================
main_menu = main_menu_inline


# ==================== NAVIGATION BUTTONS ====================

def back_button(target: str = "main"):
    """Create a back button for navigation"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data=target)]
    ])


def confirm_keyboard():
    """Create confirm/cancel keyboard for transfers and actions"""
    keyboard = [
        [
            InlineKeyboardButton(f"{get_emoji('success')} Confirm", callback_data="confirm"),
            InlineKeyboardButton(f"{get_emoji('error')} Cancel", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== DEPOSIT METHODS ====================

def deposit_methods_keyboard(lang: str = 'en'):
    """Create deposit methods selection keyboard"""
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('bank')} ንግድ ባንክ (CBE)", callback_data="deposit_cbe")],
            [InlineKeyboardButton(f"{get_emoji('bank')} አቢሲኒያ ባንክ", callback_data="deposit_abyssinia")],
            [InlineKeyboardButton(f"{get_emoji('phone')} ቴሌ ብር", callback_data="deposit_telebirr")],
            [InlineKeyboardButton(f"{get_emoji('phone')} ኤም-ፔሳ (M-Pesa)", callback_data="deposit_mpesa")],
            [InlineKeyboardButton(f"{get_emoji('back')} ተመለስ", callback_data="main")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('bank')} Commercial Bank (CBE)", callback_data="deposit_cbe")],
            [InlineKeyboardButton(f"{get_emoji('bank')} Abyssinia Bank", callback_data="deposit_abyssinia")],
            [InlineKeyboardButton(f"{get_emoji('phone')} TeleBirr", callback_data="deposit_telebirr")],
            [InlineKeyboardButton(f"{get_emoji('phone')} M-Pesa", callback_data="deposit_mpesa")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="main")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== CASHOUT METHODS ====================

def cashout_methods_keyboard(lang: str = 'en'):
    """Create cashout methods selection keyboard"""
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('bank')} ንግድ ባንክ (CBE)", callback_data="cashout_cbe")],
            [InlineKeyboardButton(f"{get_emoji('bank')} አቢሲኒያ ባንክ", callback_data="cashout_abyssinia")],
            [InlineKeyboardButton(f"{get_emoji('phone')} ቴሌ ብር", callback_data="cashout_telebirr")],
            [InlineKeyboardButton(f"{get_emoji('phone')} ኤም-ፔሳ (M-Pesa)", callback_data="cashout_mpesa")],
            [InlineKeyboardButton(f"{get_emoji('back')} ተመለስ", callback_data="main")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('bank')} Commercial Bank (CBE)", callback_data="cashout_cbe")],
            [InlineKeyboardButton(f"{get_emoji('bank')} Abyssinia Bank", callback_data="cashout_abyssinia")],
            [InlineKeyboardButton(f"{get_emoji('phone')} TeleBirr", callback_data="cashout_telebirr")],
            [InlineKeyboardButton(f"{get_emoji('phone')} M-Pesa", callback_data="cashout_mpesa")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="main")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== LANGUAGE SELECTION ====================

def language_keyboard():
    """Create language selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am")],
        [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== ADMIN PANEL ====================

def admin_keyboard():
    """Create admin panel keyboard"""
    keyboard = [
        [InlineKeyboardButton(f"{get_emoji('stats')} Dashboard", callback_data="admin_dashboard")],
        [InlineKeyboardButton(f"{get_emoji('users')} Users", callback_data="admin_users")],
        [InlineKeyboardButton(f"{get_emoji('pending')} Pending Deposits", callback_data="admin_deposits")],
        [InlineKeyboardButton(f"{get_emoji('pending')} Pending Withdrawals", callback_data="admin_withdrawals")],
        [InlineKeyboardButton(f"{get_emoji('stats')} Reports", callback_data="admin_reports")],
        [InlineKeyboardButton(f"{get_emoji('settings')} Settings", callback_data="admin_settings")],
        [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== HELP & ABOUT KEYBOARDS ====================

def help_keyboard(lang: str = 'en'):
    """Create help menu keyboard"""
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('game')} የጨዋታ ህጎች", callback_data="help_game")],
            [InlineKeyboardButton(f"{get_emoji('deposit')} ተቀማጭ ገንዘብ", callback_data="help_deposit")],
            [InlineKeyboardButton(f"{get_emoji('withdraw')} ገንዘብ ማውጣት", callback_data="help_cashout")],
            [InlineKeyboardButton(f"{get_emoji('transfer')} ገንዘብ ማስተላለፍ", callback_data="help_transfer")],
            [InlineKeyboardButton(f"{get_emoji('question')} ተደጋጋሚ ጥያቄዎች", callback_data="help_faq")],
            [InlineKeyboardButton(f"{get_emoji('support')} ደጋፊ", callback_data="help_support")],
            [InlineKeyboardButton(f"{get_emoji('back')} ተመለስ", callback_data="main")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('game')} Game Rules", callback_data="help_game")],
            [InlineKeyboardButton(f"{get_emoji('deposit')} Deposit Guide", callback_data="help_deposit")],
            [InlineKeyboardButton(f"{get_emoji('withdraw')} Withdrawal Guide", callback_data="help_cashout")],
            [InlineKeyboardButton(f"{get_emoji('transfer')} Transfer Guide", callback_data="help_transfer")],
            [InlineKeyboardButton(f"{get_emoji('question')} FAQ", callback_data="help_faq")],
            [InlineKeyboardButton(f"{get_emoji('support')} Support", callback_data="help_support")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="main")]
        ]
    return InlineKeyboardMarkup(keyboard)


def about_keyboard(lang: str = 'en'):
    """Create about menu keyboard"""
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('info')} ስለ ቦት", callback_data="about_bot")],
            [InlineKeyboardButton(f"{get_emoji('developer')} ገንቢ", callback_data="about_developer")],
            [InlineKeyboardButton(f"{get_emoji('version')} ስሪት", callback_data="about_version")],
            [InlineKeyboardButton(f"{get_emoji('terms')} ውሎች", callback_data="about_terms")],
            [InlineKeyboardButton(f"{get_emoji('privacy')} ግላዊነት", callback_data="about_privacy")],
            [InlineKeyboardButton(f"{get_emoji('back')} ተመለስ", callback_data="main")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('info')} About Bot", callback_data="about_bot")],
            [InlineKeyboardButton(f"{get_emoji('developer')} Developer", callback_data="about_developer")],
            [InlineKeyboardButton(f"{get_emoji('version')} Version", callback_data="about_version")],
            [InlineKeyboardButton(f"{get_emoji('terms')} Terms & Conditions", callback_data="about_terms")],
            [InlineKeyboardButton(f"{get_emoji('privacy')} Privacy Policy", callback_data="about_privacy")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="main")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== GAME KEYBOARDS (Quick Access) ====================

def game_control_keyboard():
    """Create game control keyboard for active game"""
    keyboard = [
        [
            InlineKeyboardButton(f"{get_emoji('cartela')} Buy Cartela", callback_data="buy_cartela"),
            InlineKeyboardButton(f"{get_emoji('stats')} Game Stats", callback_data="game_stats")
        ],
        [
            InlineKeyboardButton(f"{get_emoji('leaderboard')} Leaderboard", callback_data="game_leaderboard"),
            InlineKeyboardButton(f"{get_emoji('settings')} Settings", callback_data="game_settings")
        ],
        [
            InlineKeyboardButton(f"{get_emoji('back')} Main Menu", callback_data="main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== DAILY BONUS KEYBOARD ====================

def daily_bonus_keyboard(lang: str = 'en'):
    """Create daily bonus keyboard"""
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('gift')} የዕለት ቦነስ ይጠይቁ", callback_data="claim_daily_bonus")],
            [InlineKeyboardButton(f"{get_emoji('info')} የቦነስ መረጃ", callback_data="bonus_info")],
            [InlineKeyboardButton(f"{get_emoji('back')} ተመለስ", callback_data="main")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('gift')} Claim Daily Bonus", callback_data="claim_daily_bonus")],
            [InlineKeyboardButton(f"{get_emoji('info')} Bonus Info", callback_data="bonus_info")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="main")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== REFERRAL KEYBOARD ====================

def referral_keyboard(lang: str = 'en'):
    """Create referral system keyboard"""
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('link')} ሊንክ ያጋሩ", callback_data="share_referral")],
            [InlineKeyboardButton(f"{get_emoji('stats')} የማመሳከሪያ ስታት", callback_data="referral_stats")],
            [InlineKeyboardButton(f"{get_emoji('money')} የማመሳከሪያ ገቢ", callback_data="referral_earnings")],
            [InlineKeyboardButton(f"{get_emoji('back')} ተመለስ", callback_data="main")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(f"{get_emoji('link')} Share Link", callback_data="share_referral")],
            [InlineKeyboardButton(f"{get_emoji('stats')} Referral Stats", callback_data="referral_stats")],
            [InlineKeyboardButton(f"{get_emoji('money')} Referral Earnings", callback_data="referral_earnings")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="main")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== NOTIFICATION KEYBOARD ====================

def notification_keyboard(lang: str = 'en'):
    """Create notification settings keyboard"""
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton("🔔 ማሳወቂያዎችን አንቃ", callback_data="enable_notifications")],
            [InlineKeyboardButton("🔕 ማሳወቂያዎችን አጥፋ", callback_data="disable_notifications")],
            [InlineKeyboardButton(f"{get_emoji('back')} ተመለስ", callback_data="main")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🔔 Enable Notifications", callback_data="enable_notifications")],
            [InlineKeyboardButton("🔕 Disable Notifications", callback_data="disable_notifications")],
            [InlineKeyboardButton(f"{get_emoji('back')} Back", callback_data="main")]
        ]
    return InlineKeyboardMarkup(keyboard)


# ==================== HELPER FUNCTIONS ====================

def get_keyboard_by_name(name: str, **kwargs):
    """Get keyboard by name for dynamic loading"""
    keyboards = {
        'main': lambda: menu(kwargs.get('lang', 'en')),
        'main_inline': lambda: main_menu_inline(kwargs.get('user')),
        'back': lambda: back_button(kwargs.get('target', 'main')),
        'confirm': lambda: confirm_keyboard(),
        'deposit': lambda: deposit_methods_keyboard(kwargs.get('lang', 'en')),
        'cashout': lambda: cashout_methods_keyboard(kwargs.get('lang', 'en')),
        'language': lambda: language_keyboard(),
        'admin': lambda: admin_keyboard(),
        'help': lambda: help_keyboard(kwargs.get('lang', 'en')),
        'about': lambda: about_keyboard(kwargs.get('lang', 'en')),
        'game_control': lambda: game_control_keyboard(),
        'daily_bonus': lambda: daily_bonus_keyboard(kwargs.get('lang', 'en')),
        'referral': lambda: referral_keyboard(kwargs.get('lang', 'en')),
        'notification': lambda: notification_keyboard(kwargs.get('lang', 'en')),
    }
    
    keyboard_func = keyboards.get(name)
    if keyboard_func:
        return keyboard_func()
    return None


# ==================== KEYBOARD INFO ====================
KEYBOARDS_INFO = {
    'main': 'Main reply menu with all options',
    'main_inline': 'Inline main menu for callbacks',
    'back': 'Simple back button',
    'confirm': 'Confirm/Cancel buttons',
    'deposit': 'Deposit payment methods',
    'cashout': 'Cashout withdrawal methods',
    'language': 'Language selection (English/Amharic)',
    'admin': 'Admin panel controls',
    'help': 'Help menu with guides',
    'about': 'About bot information',
    'game_control': 'Game control buttons',
    'daily_bonus': 'Daily bonus claim menu',
    'referral': 'Referral system menu',
    'notification': 'Notification settings menu',
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


# ==================== EXPORTS ====================
__all__ = [
    # Reply keyboards
    'menu',
    
    # Inline keyboards
    'main_menu_inline',
    'main_menu',
    'back_button',
    'confirm_keyboard',
    'deposit_methods_keyboard',
    'cashout_methods_keyboard',
    'language_keyboard',
    'admin_keyboard',
    'help_keyboard',
    'about_keyboard',
    'game_control_keyboard',
    'daily_bonus_keyboard',
    'referral_keyboard',
    'notification_keyboard',
    
    # Helper functions
    'get_keyboard_by_name',
    
    # Info
    'KEYBOARDS_INFO',
    'KEYBOARD_STYLES',
]