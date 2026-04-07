# handlers/contact.py
"""Contact center handler with working channel/group links"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu
from ..config import SUPPORT_GROUP_LINK, SUPPORT_CHANNEL_LINK

logger = logging.getLogger(__name__)


async def contact_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show contact and support information with working links"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    # Log the links being used (for debugging)
    logger.info(f"Contact center: channel={SUPPORT_CHANNEL_LINK}, group={SUPPORT_GROUP_LINK}")
    
    # Create keyboard with channel and group links
    keyboard_buttons = []
    
    if SUPPORT_CHANNEL_LINK and SUPPORT_CHANNEL_LINK != "https://t.me/temarineh":
        keyboard_buttons.append([InlineKeyboardButton("📢 Official Channel", url=SUPPORT_CHANNEL_LINK)])
    
    if SUPPORT_GROUP_LINK and SUPPORT_GROUP_LINK != "https://t.me/presectionA":
        keyboard_buttons.append([InlineKeyboardButton("👥 Support Group", url=SUPPORT_GROUP_LINK)])
    
    # If no custom links set, show default message
    if not keyboard_buttons:
        await update.message.reply_text(
            "📞 *Contact Center*\n\n"
            "For support, please contact admin directly.\n"
            f"Admin ID: `{7160486597}`",
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )
        return
    
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    await update.message.reply_text(
        TEXTS[lang]['contact'],
        reply_markup=keyboard,
        parse_mode='Markdown'
    )