# handlers/start.py
"""Language selection and welcome handler"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send language selection menu on /start"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am")]
    ])
    await update.message.reply_text(
        "🌐 Select your language / ቋንቋ ይምረጡ:",
        reply_markup=keyboard
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection callback"""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split("_")[1]
    telegram_id = query.from_user.id
    
    user = await Database.get_user(telegram_id)
    if not user:
        await Database.create_user(
            telegram_id, 
            query.from_user.username or "",
            query.from_user.first_name or "",
            query.from_user.last_name or "",
            "",
            lang
        )
    else:
        await Database.update_user(telegram_id, lang=lang)
    
    await query.edit_message_text(
        TEXTS[lang]['welcome'], 
        parse_mode='Markdown'
    )
    await query.message.reply_text(
        "👇 Choose an option:",
        reply_markup=menu(lang)
    )