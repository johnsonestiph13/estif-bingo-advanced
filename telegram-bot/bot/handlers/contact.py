# handlers/contact.py
"""Contact center handler with working channel and group buttons"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu
from ..config import SUPPORT_CHANNEL_LINK, SUPPORT_GROUP_LINK

logger = logging.getLogger(__name__)


async def contact_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show contact and support information with clickable buttons"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    # Create inline keyboard with channel and group buttons
    keyboard = []
    
    if SUPPORT_CHANNEL_LINK:
        keyboard.append([InlineKeyboardButton("📢 Official Channel", url=SUPPORT_CHANNEL_LINK)])
    else:
        logger.warning("SUPPORT_CHANNEL_LINK not set")
    
    if SUPPORT_GROUP_LINK:
        keyboard.append([InlineKeyboardButton("👥 Support Group", url=SUPPORT_GROUP_LINK)])
    else:
        logger.warning("SUPPORT_GROUP_LINK not set")
    
    # If both links are missing, show a fallback message
    if not keyboard:
        await update.message.reply_text(
            "📞 *Contact Center*\n\n"
            "For support, please contact the admin directly.\n"
            "We will add official channels soon.",
            parse_mode='Markdown',
            reply_markup=menu(lang)
        )
        return
    
    await update.message.reply_text(
        TEXTS[lang]['contact'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )