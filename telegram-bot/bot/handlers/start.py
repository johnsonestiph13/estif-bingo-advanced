# telegram-bot/bot/handlers/start.py
# Estif Bingo 24/7 - Language Selection and Welcome Handler

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.database import Database
from bot.texts.locales import TEXTS
from bot.keyboards.menu import menu
from bot.texts.emojis import get_emoji
from bot.utils import logger

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send language selection menu on /start"""
    telegram_id = update.effective_user.id
    
    # Check if user already exists and has language preference
    user = await Database.get_user(telegram_id)
    
    if user and user.get('lang'):
        # User already has language set, show welcome message directly
        lang = user.get('lang', 'en')
        await update.message.reply_text(
            TEXTS[lang]['welcome'],
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return
    
    # Show language selection keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am")]
    ])
    
    await update.message.reply_text(
        f"{get_emoji('language')} Select your language / ቋንቋ ይምረጡ:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection callback"""
    query = update.callback_query
    await query.answer()
    
    try:
        lang = query.data.split("_")[1]  # "lang_en" -> "en", "lang_am" -> "am"
        telegram_id = query.from_user.id
        username = query.from_user.username or ""
        first_name = query.from_user.first_name or ""
        last_name = query.from_user.last_name or ""
        
        # Check if user exists
        user = await Database.get_user(telegram_id)
        
        if not user:
            # Create new user with selected language
            await Database.create_user(
                telegram_id,
                username,
                first_name,
                last_name,
                "",  # Phone number will be added during registration
                lang
            )
            logger.info(f"New user created: {telegram_id} - {first_name} {last_name} (Language: {lang})")
        else:
            # Update existing user's language
            await Database.update_user(telegram_id, lang=lang)
            logger.info(f"Language updated for user {telegram_id}: {lang}")
        
        # Send welcome message in selected language
        welcome_text = TEXTS[lang]['welcome']
        
        await query.edit_message_text(
            welcome_text,
            parse_mode='Markdown'
        )
        
        # Send menu options
        await query.message.reply_text(
            f"{get_emoji('click')} Choose an option from the menu below:",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        
    except KeyError as e:
        logger.error(f"Language callback key error: {e}")
        await query.edit_message_text(
            f"{get_emoji('error')} An error occurred. Please try again with /start",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Language callback error: {e}")
        await query.edit_message_text(
            f"{get_emoji('error')} An error occurred. Please try again later.",
            parse_mode='Markdown'
        )


# Export all
__all__ = [
    'start',
    'language_callback',
]