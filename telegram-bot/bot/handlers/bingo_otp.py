# telegram-bot/bot/handlers/bingo_otp.py
# Estif Bingo 24/7 - Bingo OTP Handler (Complete Working Version)

import random
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.database import Database
from bot.keyboards.menu import menu
from bot.config import config
from bot.texts.emojis import get_emoji

logger = logging.getLogger(__name__)


async def bingo_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send OTP for Bingo game login"""
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
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
    
    try:
        # Store OTP in database
        await Database.store_otp(user_id, otp)
        logger.info(f"OTP generated for user {user_id}: {otp}")
    except Exception as e:
        logger.error(f"Failed to store OTP for user {user_id}: {e}")
        await update.message.reply_text(
            f"{get_emoji('error')} Failed to generate OTP. Please try again later.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return
    
    # Create keyboard with copy button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{get_emoji('copy')} Copy OTP: {otp}", callback_data=f"copy_otp_{otp}")],
        [InlineKeyboardButton(f"{get_emoji('game')} Play Now", callback_data="play")]
    ])
    
    # Send OTP message
    await update.message.reply_text(
        f"{get_emoji('lock')} *Your Bingo Code*\n\n"
        f"```\n{otp}\n```\n\n"
        f"{get_emoji('clock')} Valid for {config.OTP_EXPIRY_MINUTES} minutes.\n"
        f"{get_emoji('info')} One-time use only.\n\n"
        f"Enter this code on the Bingo website to login.",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def verify_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify OTP entered by user"""
    # Check if user provided an OTP
    if not context.args:
        await update.message.reply_text(
            f"{get_emoji('info')} *Verify OTP*\n\n"
            f"Usage: `/verify OTP_CODE`\n\n"
            f"Example: `/verify 123456`",
            parse_mode='Markdown'
        )
        return
    
    user_id = update.effective_user.id
    otp = context.args[0]
    
    # Validate OTP format
    if not otp.isdigit() or len(otp) != 6:
        await update.message.reply_text(
            f"{get_emoji('error')} Invalid OTP format!\n\n"
            f"OTP must be a 6-digit number.\n\n"
            f"Example: `/verify 123456`",
            parse_mode='Markdown'
        )
        return
    
    # Verify OTP from database
    if await Database.verify_otp(user_id, otp):
        await update.message.reply_text(
            f"{get_emoji('success')} OTP verified! You can now login.",
            parse_mode='Markdown'
        )
        logger.info(f"OTP verified for user {user_id}")
    else:
        await update.message.reply_text(
            f"{get_emoji('error')} Invalid or expired OTP.\n\n"
            f"Please generate a new code using /bingo",
            parse_mode='Markdown'
        )


# Export all
__all__ = ['bingo_otp', 'verify_otp']