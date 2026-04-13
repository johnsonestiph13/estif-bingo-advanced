# telegram-bot/bot/handlers/register.py
# Estif Bingo 24/7 - User Registration Handler with Phone Verification

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.db.database import Database
from bot.texts.locales import TEXTS
from bot.keyboards.menu import menu
from bot.config import config
from bot.utils import logger, is_valid_phone, normalize_phone
from bot.texts.emojis import get_emoji

logger = logging.getLogger(__name__)

# Conversation states
PHONE = 1

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
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(f"{get_emoji('phone')} Share Contact", request_contact=True)]],
        resize_keyboard=True
    )
    await update.message.reply_text(
        f"{get_emoji('info')} {TEXTS[lang]['register_prompt']}",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    return PHONE


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process contact sharing, complete registration, and give welcome bonus"""
    try:
        contact = update.message.contact
        
        if not contact:
            await update.message.reply_text(
                f"{get_emoji('error')} No contact received. Please use the share contact button.",
                parse_mode='Markdown'
            )
            return PHONE
        
        telegram_id = update.effective_user.id
        user = update.effective_user
        phone_number = contact.phone_number
        
        # Validate phone number
        if not is_valid_phone(phone_number):
            phone_number = normalize_phone(phone_number)
        
        existing = await Database.get_user(telegram_id)
        lang = existing.get('lang', 'en') if existing else 'en'
        
        if existing:
            # Update existing user
            await Database.update_user(
                telegram_id,
                phone=phone_number,
                registered=True,
                joined_group=True
            )
            
            # Give welcome bonus if balance is zero
            current_balance = await Database.get_balance(telegram_id)
            if current_balance == 0:
                await Database.add_balance(telegram_id, WELCOME_BONUS_AMOUNT, "welcome_bonus")
                await update.message.reply_text(
                    f"{get_emoji('gift')} <b>Welcome Bonus!</b>\n\n"
                    f"You received {WELCOME_BONUS_AMOUNT} ETB welcome bonus!",
                    parse_mode='Markdown'
                )
        else:
            # Create new user
            await Database.create_user(
                telegram_id,
                user.username or "",
                user.first_name or "",
                user.last_name or "",
                phone_number,
                lang
            )
            await Database.add_balance(telegram_id, WELCOME_BONUS_AMOUNT, "welcome_bonus")
        
        # Send success message
        new_balance = await Database.get_balance(telegram_id)
        await update.message.reply_text(
            f"{get_emoji('success')} <b>Registration Successful!</b>\n\n"
            f"{get_emoji('phone')} Phone: <code>{phone_number}</code>\n"
            f"{get_emoji('money')} Balance: <code>{new_balance:.2f} ETB</code>\n\n"
            f"{get_emoji('game')} Use /play to start playing!",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        
        # Notify admin
        await context.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID,
            text=f"{get_emoji('new')} <b>NEW REGISTRATION</b>\n"
                 f"{get_emoji('user')} Name: {user.first_name} {user.last_name or ''}\n"
                 f"{get_emoji('phone')} Phone: {phone_number}\n"
                 f"{get_emoji('id')} ID: <code>{telegram_id}</code>\n"
                 f"{get_emoji('gift')} Welcome Bonus: {WELCOME_BONUS_AMOUNT} ETB",
            parse_mode='Markdown'
        )
        
        logger.info(f"New user registered: {telegram_id} - {user.first_name} - {phone_number}")
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in handle_contact: {e}")
        await update.message.reply_text(
            f"{get_emoji('error')} Error processing registration. Please try again.",
            parse_mode='Markdown'
        )
        return PHONE


async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process phone number input (manual entry without contact button)"""
    telegram_id = update.effective_user.id
    user = update.effective_user
    phone = update.message.text.strip()
    
    # Validate phone format
    if not is_valid_phone(phone):
        await update.message.reply_text(
            f"{get_emoji('error')} Invalid phone number format.\n\n"
            f"Please enter a valid Ethiopian phone number (09XXXXXXXX or 07XXXXXXXX):\n\n"
            f"Or use the share contact button for automatic entry.",
            parse_mode='Markdown'
        )
        return PHONE
    
    phone = normalize_phone(phone)
    
    existing = await Database.get_user(telegram_id)
    lang = existing.get('lang', 'en') if existing else 'en'
    
    if existing:
        await Database.update_user(
            telegram_id,
            phone=phone,
            registered=True,
            joined_group=True
        )
        
        current_balance = await Database.get_balance(telegram_id)
        if current_balance == 0:
            await Database.add_balance(telegram_id, WELCOME_BONUS_AMOUNT, "welcome_bonus")
            await update.message.reply_text(
                f"{get_emoji('gift')} <b>Welcome Bonus!</b>\n\n"
                f"You received {WELCOME_BONUS_AMOUNT} ETB welcome bonus!",
                parse_mode='Markdown'
            )
    else:
        await Database.create_user(
            telegram_id,
            user.username or "",
            user.first_name or "",
            user.last_name or "",
            phone,
            lang
        )
        await Database.add_balance(telegram_id, WELCOME_BONUS_AMOUNT, "welcome_bonus")
    
    new_balance = await Database.get_balance(telegram_id)
    await update.message.reply_text(
        f"{get_emoji('success')} <b>Registration Successful!</b>\n\n"
        f"{get_emoji('phone')} Phone: <code>{phone}</code>\n"
        f"{get_emoji('money')} Balance: <code>{new_balance:.2f} ETB</code>\n\n"
        f"{get_emoji('game')} Use /play to start playing!",
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    
    await context.bot.send_message(
        chat_id=config.ADMIN_CHAT_ID,
        text=f"{get_emoji('new')} <b>NEW REGISTRATION</b>\n"
             f"{get_emoji('user')} Name: {user.first_name} {user.last_name or ''}\n"
             f"{get_emoji('phone')} Phone: {phone}\n"
             f"{get_emoji('id')} ID: <code>{telegram_id}</code>\n"
             f"{get_emoji('gift')} Welcome Bonus: {WELCOME_BONUS_AMOUNT} ETB",
        parse_mode='Markdown'
    )
    
    logger.info(f"New user registered: {telegram_id} - {user.first_name} - {phone}")
    
    return ConversationHandler.END


async def register_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel registration"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    await update.message.reply_text(
        f"{get_emoji('warning')} Registration cancelled. Use /register to try again.",
        reply_markup=menu(lang),
        parse_mode='Markdown'
    )
    return ConversationHandler.END


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send game link with authentication code"""
    telegram_id = update.effective_user.id
    user = await Database.get_user(telegram_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    if not user or not user.get('registered'):
        await update.message.reply_text(
            f"{get_emoji('error')} Please register first using /register",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        return
    
    try:
        code = await Database.create_auth_code(telegram_id)
        game_url = f"{config.GAME_WEB_URL}?code={code}&telegram_id={telegram_id}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{get_emoji('game')} Play Now {get_emoji('game')}", url=game_url)]
        ])
        
        await update.message.reply_text(
            f"{get_emoji('game')} <b>Click the button below to start playing!</b>\n\n"
            f"{get_emoji('link')} Or copy this link:\n<code>{game_url}</code>",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Play error: {e}")
        await update.message.reply_text(
            f"{get_emoji('error')} Failed to generate game link. Please try again later.",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )


# ==================== BACKWARD COMPATIBILITY ====================
# Alias for older code that expects 'handle_contact'
# handle_contact is already defined above, so no alias needed


# Export all
__all__ = [
    'register',
    'handle_contact',      # ← This is the main function for contact sharing
    'register_phone',      # For manual phone entry
    'register_cancel',
    'play',
    'PHONE',
]