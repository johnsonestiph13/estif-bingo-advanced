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
from bot.texts.locales import TEXTS

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
            f"{get_emoji('error')} Failed to generate OTP. Please try again later.\n\n"
            f"Reason: {str(e)}",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return
    
    # Create keyboard with copy button and play button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{get_emoji('copy')} Copy OTP: {otp}", callback_data=f"copy_otp_{otp}")],
        [InlineKeyboardButton(f"{get_emoji('game')} Play Now", callback_data="play")]
    ])
    
    # Send OTP message
    await update.message.reply_text(
        f"{get_emoji('lock')} *Your Bingo Login Code*\n\n"
        f"```\n{otp}\n```\n\n"
        f"{get_emoji('clock')} *Valid for:* {config.OTP_EXPIRY_MINUTES} minutes\n"
        f"{get_emoji('info')} *One-time use only*\n\n"
        f"Enter this code on the Bingo website to login.\n\n"
        f"*Note:* Each code can only be used once and expires after {config.OTP_EXPIRY_MINUTES} minutes.",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    # Also send plain text fallback (in case inline keyboard doesn't work)
    await update.message.reply_text(
        f"{get_emoji('info')} Your OTP code is: `{otp}`\n\n"
        f"Use it within {config.OTP_EXPIRY_MINUTES} minutes.",
        parse_mode='Markdown'
    )


async def verify_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify OTP entered by user"""
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    # Check if user provided an OTP
    if not context.args:
        await update.message.reply_text(
            f"{get_emoji('info')} *Verify OTP*\n\n"
            f"Usage: `/verify OTP_CODE`\n\n"
            f"Example: `/verify 123456`\n\n"
            f"Or use the code from /bingo command.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return
    
    otp = context.args[0]
    
    # Validate OTP format
    if not otp.isdigit() or len(otp) != 6:
        await update.message.reply_text(
            f"{get_emoji('error')} Invalid OTP format!\n\n"
            f"OTP must be a 6-digit number.\n\n"
            f"Example: `/verify 123456`",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return
    
    # Verify OTP from database
    try:
        is_valid = await Database.verify_otp(user_id, otp)
        
        if is_valid:
            await update.message.reply_text(
                f"{get_emoji('success')} *OTP Verified Successfully!*\n\n"
                f"You can now login to the Bingo game.\n\n"
                f"Use /play to start playing! 🎮",
                reply_markup=menu(lang),
                parse_mode='Markdown'
            )
            logger.info(f"OTP verified for user {user_id}")
        else:
            await update.message.reply_text(
                f"{get_emoji('error')} *Invalid or Expired OTP*\n\n"
                f"The code you entered is incorrect or has expired.\n\n"
                f"Please generate a new code using /bingo",
                reply_markup=menu(lang),
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"OTP verification error for user {user_id}: {e}")
        await update.message.reply_text(
            f"{get_emoji('error')} Failed to verify OTP. Please try again later.\n\n"
            f"Use /bingo to generate a new code.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )


# For backward compatibility
__all__ = ['bingo_otp', 'verify_otp']