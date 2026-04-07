# handlers/register.py
"""User registration handler with phone number and play function"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..db.database import Database
from ..texts.locales import TEXTS
from ..keyboards.menu import menu
from ..config import ADMIN_CHAT_ID, GAME_WEB_URL

logger = logging.getLogger(__name__)

# Welcome bonus amount
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
        await Database.update_user(
            telegram_id,
            phone=contact.phone_number,
            registered=True,
            joined_group=True
        )
        if existing.get('balance', 0) == 0:
            await Database.add_balance(telegram_id, WELCOME_BONUS_AMOUNT, "welcome_bonus")
            await update.message.reply_text(
                f"🎉 *Welcome Bonus!*\n\nYou received {WELCOME_BONUS_AMOUNT} ETB welcome bonus!",
                parse_mode='Markdown'
            )
    else:
        await Database.create_user(
            telegram_id,
            user.username or "",
            user.first_name or "",
            user.last_name or "",
            contact.phone_number,
            lang
        )
        new_balance = await Database.add_balance(telegram_id, WELCOME_BONUS_AMOUNT, "welcome_bonus")
        await update.message.reply_text(
            f"🎉 *Welcome to Estif Bingo!*\n\n"
            f"You received a welcome bonus of *{WELCOME_BONUS_AMOUNT} ETB*!\n"
            f"💰 Your balance: *{new_balance} ETB*",
            parse_mode='Markdown'
        )
    
    await update.message.reply_text(
        TEXTS[lang]['register_success'].format(contact.phone_number, GAME_WEB_URL),
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"🆕 NEW REGISTRATION\n"
             f"👤 Name: {user.first_name} {user.last_name or ''}\n"
             f"📱 Phone: {contact.phone_number}\n"
             f"🆔 ID: `{telegram_id}`\n"
             f"🎁 Welcome Bonus: {WELCOME_BONUS_AMOUNT} ETB",
        parse_mode='Markdown'
    )
    
    logger.info(f"New user registered: {telegram_id} - {user.first_name}")


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send game link with authentication code"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    if not user or not user.get('registered'):
        await update.message.reply_text(
            "❌ Please register first using /register",
            reply_markup=menu(lang)
        )
        return
    
    # Generate one-time auth code
    try:
        code = await Database.create_auth_code(telegram_id)
        game_url = f"{GAME_WEB_URL}?code={code}"
        
        # Create inline keyboard with the game link
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Play Now", url=game_url)]
        ])
        
        await update.message.reply_text(
            f"🎮 *Click the button below to start playing!*\n\n"
            f"🔗 Or copy this link:\n`{game_url}`",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Play error: {e}")
        await update.message.reply_text(
            "❌ Failed to generate game link. Please try again later.",
            reply_markup=menu(lang)
        )