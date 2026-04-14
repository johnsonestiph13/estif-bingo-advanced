# telegram-bot/bot/handlers/bingo_otp.py
# Estif Bingo 24/7 - Bingo Game OTP Handler (FULLY FIXED)

import logging
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.database import Database
from bot.texts.locales import TEXTS
from bot.keyboards.menu import menu
from bot.config import config
from bot.utils import logger
from bot.texts.emojis import get_emoji

logger = logging.getLogger(__name__)


async def bingo_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send OTP for Bingo game login"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    # Check if user is registered
    if not user or not user.get('registered'):
        await update.message.reply_text(
            f"{get_emoji('error')} Please register first using /register",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return
    
    # Generate 6-digit OTP
    otp = f"{random.randint(0, 999999):06d}"
    
    # Store OTP in database with expiration
    try:
        await Database.store_otp(telegram_id, otp)
        logger.info(f"OTP generated for user {telegram_id}: {otp}")
    except Exception as e:
        logger.error(f"Failed to store OTP for {telegram_id}: {e}")
        await update.message.reply_text(
            f"{get_emoji('error')} Failed to generate OTP. Please try again later.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return
    
    # Create a button to copy the OTP easily
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{get_emoji('copy')} Copy OTP: {otp}", callback_data=f"copy_otp_{otp}")],
        [InlineKeyboardButton(f"{get_emoji('game')} Play Now", callback_data="play")]
    ])
    
    # Send OTP message
    await update.message.reply_text(
        f"{get_emoji('lock')} *Your Bingo Login Code*\n\n"
        f"```\n{otp}\n```\n\n"
        f"{get_emoji('clock')} This code expires in **{config.OTP_EXPIRY_MINUTES} minutes**.\n\n"
        f"{get_emoji('info')} Enter this code on the Bingo website to login.\n\n"
        f"*Note:* Each code can only be used once.",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    # Also send plain text fallback
    await update.message.reply_text(
        f"{get_emoji('info')} Your OTP code is: `{otp}`\n\n"
        f"Use it within {config.OTP_EXPIRY_MINUTES} minutes.",
        parse_mode='Markdown'
    )


async def verify_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify OTP entered by user (can be used as a command or callback)"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    # Check if user sent an OTP
    if not context.args:
        await update.message.reply_text(
            f"{get_emoji('info')} *Verify OTP*\n\n"
            f"Usage: `/verify OTP_CODE`\n\n"
            f"Example: `/verify 123456`\n\n"
            f"Or use the code from /bingo command.",
            parse_mode='Markdown'
        )
        return
    
    otp = context.args[0]
    
    # Verify OTP from database
    is_valid = await Database.verify_otp(telegram_id, otp)
    
    if is_valid:
        await update.message.reply_text(
            f"{get_emoji('success')} *OTP Verified!*\n\n"
            f"You can now login to the Bingo game.\n\n"
            f"Use /play to start playing!",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        logger.info(f"OTP verified for user {telegram_id}")
    else:
        await update.message.reply_text(
            f"{get_emoji('error')} *Invalid OTP*\n\n"
            f"The code you entered is invalid or expired.\n\n"
            f"Please generate a new code using /bingo",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )


# Export all
__all__ = [
    'bingo_otp',
    'verify_otp',
]