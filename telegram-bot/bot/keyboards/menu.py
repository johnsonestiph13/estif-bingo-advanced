# keyboards/menu.py
from telegram import ReplyKeyboardMarkup

def menu(lang='en'):
    """Return main menu keyboard based on language"""
    if lang == 'am':
        return ReplyKeyboardMarkup([
            ["🎮 ጨዋታ", "📝 ተመዝገብ", "💰 ገንዘብ አስገባ"],
            ["💳 ገንዘብ አውጣ", "📞 ደንበኛ አገልግሎት", "🎉 ጋብዝ"],
            ["🔐 የቢንጎ ኮድ"]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            ["🎮 Play", "📝 Register", "💰 Deposit"],
            ["💳 Cash Out", "📞 Contact Center", "🎉 Invite"],
            ["🔐 Bingo Code"]
        ], resize_keyboard=True)