# handlers/register.py
"""User registration handler with phone number and automatic welcome bonus"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu
from ..config import ADMIN_CHAT_ID, GAME_WEB_URL

logger = logging.getLogger(__name__)

# Welcome bonus amount in ETB
WELCOME_BONUS_AMOUNT = 30


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start registration process"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    if user and user.get('registered'):
        await update.message.reply_text(
            TEXTS[lang]['already_registered'],
            reply_markup=menu(lang)
        )
        return
    
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Share Contact", request_contact=True)]],
        resize_keyboard=True
    )
    await update.message.reply_text(
        TEXTS[lang]['register_prompt'],
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process contact sharing, complete registration, and give welcome bonus"""
    contact = update.message.contact
    user = update.effective_user
    telegram_id = user.id
    
    existing = await Database.get_user(telegram_id)
    lang = existing.get('lang', 'en') if existing else 'en'
    
    if existing:
        # Update existing user
        await Database.update_user(
            telegram_id,
            phone=contact.phone_number,
            registered=True,
            joined_group=True
        )
        # If user was already registered but missing bonus, add it
        if existing.get('balance', 0) == 0:
            await Database.add_balance(telegram_id, WELCOME_BONUS_AMOUNT, "welcome_bonus")
            await update.message.reply_text(
                f"🎉 *Welcome Bonus!*\n\nYou received {WELCOME_BONUS_AMOUNT} ETB welcome bonus!",
                parse_mode='Markdown'
            )
    else:
        # Create new user
        await Database.create_user(
            telegram_id,
            user.username or "",
            user.first_name or "",
            user.last_name or "",
            contact.phone_number,
            lang
        )
        
        # Add welcome bonus for new user
        new_balance = await Database.add_balance(telegram_id, WELCOME_BONUS_AMOUNT, "welcome_bonus")
        logger.info(f"Welcome bonus of {WELCOME_BONUS_AMOUNT} ETB added to user {telegram_id}")
        
        # Send welcome bonus message
        await update.message.reply_text(
            f"🎉 *Welcome to Estif Bingo!*\n\n"
            f"You received a welcome bonus of *{WELCOME_BONUS_AMOUNT} ETB*!\n"
            f"💰 Your balance: *{new_balance} ETB*",
            parse_mode='Markdown'
        )
    
    # Send registration success message with game link
    await update.message.reply_text(
        TEXTS[lang]['register_success'].format(contact.phone_number, GAME_WEB_URL),
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    
    # Notify admin about new registration
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"🆕 NEW REGISTRATION\n"
             f"👤 Name: {user.first_name} {user.last_name or ''}\n"
             f"📱 Phone: {contact.phone_number}\n"
             f"🆔 ID: `{telegram_id}`\n"
             f"🎁 Welcome Bonus: {WELCOME_BONUS_AMOUNT} ETB",
        parse_mode='Markdown'
    )
    
    logger.info(f"New user registered: {telegram_id} - {user.first_name} - Bonus: {WELCOME_BONUS_AMOUNT} ETB")