# handlers/bingo_otp.py
"""Bingo game OTP handler"""

import logging
import secrets
from telegram import Update
from telegram.ext import ContextTypes
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu
from ..config import OTP_EXPIRY_MINUTES

logger = logging.getLogger(__name__)

async def bingo_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send OTP for Bingo game login"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    if not user or not user.get('registered'):
        await update.message.reply_text(
            "❌ Please register first using /register",
            reply_markup=menu(lang)
        )
        return
    
    # Generate 6-digit OTP
    otp = f"{secrets.randbelow(1000000):06d}"
    await Database.store_otp(telegram_id, otp)
    
    await update.message.reply_text(
        TEXTS[lang]['bingo_otp'].format(otp, OTP_EXPIRY_MINUTES),
        parse_mode='Markdown',
        reply_markup=menu(lang)
    )
    
    logger.info(f"OTP generated for user {telegram_id}")