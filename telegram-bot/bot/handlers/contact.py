# handlers/contact.py
"""Contact center handler"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu
from ..config import SUPPORT_GROUP_LINK, SUPPORT_CHANNEL_LINK

logger = logging.getLogger(__name__)

async def contact_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show contact and support information"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Channel", url=SUPPORT_CHANNEL_LINK)],
        [InlineKeyboardButton("👥 Group", url=SUPPORT_GROUP_LINK)]
    ])
    
    await update.message.reply_text(
        TEXTS[lang]['contact'],
        reply_markup=keyboard,
        parse_mode='Markdown'
    )