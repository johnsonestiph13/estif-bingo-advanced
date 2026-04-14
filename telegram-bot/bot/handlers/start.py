# bot/handlers/start.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.database import Database
from bot.texts.locales import TEXTS
from bot.keyboards.menu import menu
from bot.texts.emojis import get_emoji

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send language selection menu on /start"""
    try:
        user_id = update.effective_user.id
        logger.info(f"Start command from user: {user_id}")
        
        user = await Database.get_user(user_id)
        
        if user and user.get('lang'):
            lang = user['lang']
            logger.info(f"User {user_id} already has language: {lang}")
            await update.message.reply_text(
                TEXTS[lang]['welcome'],
                reply_markup=menu(lang),
                parse_mode='Markdown'
            )
            return
        
        # Show language selection keyboard
        logger.info(f"Showing language selection for user: {user_id}")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am")]
        ])
        
        await update.message.reply_text(
            f"{get_emoji('language')} Select your language / ቋንቋ ይምረጡ:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        logger.info(f"Language selection sent to user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text(
            f"{get_emoji('error')} An error occurred. Please try again later.",
            parse_mode='Markdown'
        )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection callback"""
    try:
        query = update.callback_query
        await query.answer()
        
        lang = query.data.split("_")[1]  # "lang_en" -> "en", "lang_am" -> "am"
        user_id = query.from_user.id
        username = query.from_user.username or ""
        first_name = query.from_user.first_name or ""
        last_name = query.from_user.last_name or ""
        
        logger.info(f"Language selected: {lang} for user: {user_id}")
        
        user = await Database.get_user(user_id)
        
        if not user:
            logger.info(f"Creating new user: {user_id}")
            await Database.create_user(
                user_id, username, first_name, last_name, "", lang
            )
        else:
            logger.info(f"Updating language for existing user: {user_id}")
            await Database.update_user(user_id, lang=lang)
        
        # Edit the original message to show welcome text
        await query.edit_message_text(
            TEXTS[lang]['welcome'],
            parse_mode='Markdown'
        )
        
        # Send the menu as a new message
        await query.message.reply_text(
            f"{get_emoji('click')} Choose an option from the menu below:",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        
        logger.info(f"Language selection completed for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error in language_callback: {e}")
        await query.edit_message_text(
            f"{get_emoji('error')} An error occurred. Please try /start again.",
            parse_mode='Markdown'
        )

__all__ = ['start', 'language_callback']