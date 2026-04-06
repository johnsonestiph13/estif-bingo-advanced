# handlers/balance.py
"""Balance inquiry handler"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu

logger = logging.getLogger(__name__)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's current balance"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    if not user or not user.get('registered'):
        await update.message.reply_text(
            "❌ Please register first using /register",
            reply_markup=menu(lang)
        )
        return
    
    # Add small delay for better UX (shows thinking)
    await update.message.reply_chat_action(action="typing")
    
    await update.message.reply_text(
        TEXTS[lang]['balance'].format(user['balance'], user['total_deposited']),
        parse_mode='Markdown',
        reply_markup=menu(lang)
    )