# keyboards/menu.py
# Estif Bingo 24/7 - Keyboard Menu with Transfer Feature

from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

def menu(lang='en'):
    """Return main menu keyboard based on language (Reply Keyboard)"""
    if lang == 'am':
        return ReplyKeyboardMarkup([
            ["🎮 ጨዋታ", "📝 ተመዝገብ", "💰 ገንዘብ አስገባ"],
            ["💳 ገንዘብ አውጣ", "💸 ገንዘብ አስተላልፍ", "📞 ደንበኛ አገልግሎት"],
            ["🎉 ጋብዝ", "🔐 የቢንጎ ኮድ"]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            ["🎮 Play", "📝 Register", "💰 Deposit"],
            ["💳 Cash Out", "💸 Transfer", "📞 Contact Center"],
            ["🎉 Invite", "🔐 Bingo Code"]
        ], resize_keyboard=True)


def main_menu_inline(user):
    """Create inline main menu keyboard (for callback queries)"""
    lang = user.get('lang', 'en') if user else 'en'
    
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton("🎮 ጨዋታ", callback_data="play")],
            [InlineKeyboardButton("📝 ተመዝገብ", callback_data="register")],
            [InlineKeyboardButton("💰 ገንዘብ አስገባ", callback_data="deposit")],
            [InlineKeyboardButton("💳 ገንዘብ አውጣ", callback_data="cashout")],
            [InlineKeyboardButton("💸 ገንዘብ አስተላልፍ", callback_data="transfer")],
            [InlineKeyboardButton("📞 ደንበኛ አገልግሎት", callback_data="contact")],
            [InlineKeyboardButton("🎉 ጋብዝ", callback_data="invite")],
            [InlineKeyboardButton("🔐 የቢንጎ ኮድ", callback_data="bingo")],
            [InlineKeyboardButton("🌐 ቋንቋ ቀይር", callback_data="change_lang")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎮 Play", callback_data="play")],
            [InlineKeyboardButton("📝 Register", callback_data="register")],
            [InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
            [InlineKeyboardButton("💳 Cash Out", callback_data="cashout")],
            [InlineKeyboardButton("💸 Transfer", callback_data="transfer")],
            [InlineKeyboardButton("📞 Contact Center", callback_data="contact")],
            [InlineKeyboardButton("🎉 Invite", callback_data="invite")],
            [InlineKeyboardButton("🔐 Bingo Code", callback_data="bingo")],
            [InlineKeyboardButton("🌐 Change Language", callback_data="change_lang")]
        ]
    
    return InlineKeyboardMarkup(keyboard)


def back_button(target):
    """Create a back button for navigation"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=target)]
    ])


def confirm_keyboard():
    """Create confirm/cancel keyboard for transfers"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="transfer_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="transfer_cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def deposit_methods_keyboard(lang='en'):
    """Create deposit methods selection keyboard"""
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton("🏦 ንግድ ባንክ (CBE)", callback_data="deposit_cbe")],
            [InlineKeyboardButton("🏦 አቢሲኒያ ባንክ", callback_data="deposit_abyssinia")],
            [InlineKeyboardButton("📱 ቴሌ ብር", callback_data="deposit_telebirr")],
            [InlineKeyboardButton("📱 ኤም-ፔሳ (M-Pesa)", callback_data="deposit_mpesa")],
            [InlineKeyboardButton("🔙 ተመለስ", callback_data="main")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🏦 Commercial Bank (CBE)", callback_data="deposit_cbe")],
            [InlineKeyboardButton("🏦 Abyssinia Bank", callback_data="deposit_abyssinia")],
            [InlineKeyboardButton("📱 TeleBirr", callback_data="deposit_telebirr")],
            [InlineKeyboardButton("📱 M-Pesa", callback_data="deposit_mpesa")],
            [InlineKeyboardButton("🔙 Back", callback_data="main")]
        ]
    return InlineKeyboardMarkup(keyboard)


def cashout_methods_keyboard(lang='en'):
    """Create cashout methods selection keyboard"""
    if lang == 'am':
        keyboard = [
            [InlineKeyboardButton("🏦 ንግድ ባንክ (CBE)", callback_data="cashout_cbe")],
            [InlineKeyboardButton("🏦 አቢሲኒያ ባንክ", callback_data="cashout_abyssinia")],
            [InlineKeyboardButton("📱 ቴሌ ብር", callback_data="cashout_telebirr")],
            [InlineKeyboardButton("📱 ኤም-ፔሳ (M-Pesa)", callback_data="cashout_mpesa")],
            [InlineKeyboardButton("🔙 ተመለስ", callback_data="main")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🏦 Commercial Bank (CBE)", callback_data="cashout_cbe")],
            [InlineKeyboardButton("🏦 Abyssinia Bank", callback_data="cashout_abyssinia")],
            [InlineKeyboardButton("📱 TeleBirr", callback_data="cashout_telebirr")],
            [InlineKeyboardButton("📱 M-Pesa", callback_data="cashout_mpesa")],
            [InlineKeyboardButton("🔙 Back", callback_data="main")]
        ]
    return InlineKeyboardMarkup(keyboard)


def language_keyboard():
    """Create language selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am")],
        [InlineKeyboardButton("🔙 Back", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_keyboard():
    """Create admin panel keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard", callback_data="admin_dashboard")],
        [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
        [InlineKeyboardButton("💰 Pending Deposits", callback_data="admin_deposits")],
        [InlineKeyboardButton("💳 Pending Withdrawals", callback_data="admin_withdrawals")],
        [InlineKeyboardButton("📈 Reports", callback_data="admin_reports")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
        [InlineKeyboardButton("🔙 Back", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)