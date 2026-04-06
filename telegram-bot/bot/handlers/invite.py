# handlers/invite.py
"""Invite friends handler"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu
from ..config import GAME_WEB_URL

logger = logging.getLogger(__name__)

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send invite link to user"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    # Generate referral link (optional - can include user ID)
    referral_link = f"{GAME_WEB_URL}?ref={telegram_id}"
    
    await update.message.reply_text(
        TEXTS[lang]['invite'].format(referral_link),
        parse_mode='Markdown',
        reply_markup=menu(lang),
        disable_web_page_preview=True
    )