# bot/handlers/start.py
# Estif Bingo 24/7 - Enhanced Language Selection Handler
# Features: Always shows language options, welcome bonus, user tracking

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.database import Database
from bot.texts.locales import TEXTS
from bot.keyboards.menu import menu
from bot.texts.emojis import get_emoji

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send language selection menu on /start - Always shows language options"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or ""
        first_name = update.effective_user.first_name or ""
        last_name = update.effective_user.last_name or ""
        
        logger.info(f"Start command from user: {user_id} (@{username})")
        
        # Update user's last seen timestamp
        await Database.update_last_seen(user_id)
        
        # Show language selection keyboard (ALWAYS)
        logger.info(f"Showing language selection for user: {user_id}")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am")]
        ])
        
        # Send language selection message
        await update.message.reply_text(
            f"{get_emoji('language')} *Select your language / ቋንቋ ይምረጡ:*\n\n"
            f"Choose your preferred language to continue using the bot.\n\n"
            f"*English* - Full bot features\n"
            f"*አማርኛ* - ሙሉ የቦት አገልግሎቶች",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        logger.info(f"Language selection sent to user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error in start command for user {update.effective_user.id}: {e}")
        await update.message.reply_text(
            f"{get_emoji('error')} *An error occurred.*\n\n"
            f"Please try again later. If the problem persists, contact support.\n\n"
            f"Support: @temarineh",
            parse_mode='Markdown'
        )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection callback with enhanced user setup"""
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.username or ""
    first_name = query.from_user.first_name or ""
    last_name = query.from_user.last_name or ""
    
    try:
        await query.answer()
        
        lang = query.data.split("_")[1]  # "lang_en" -> "en", "lang_am" -> "am"
        logger.info(f"Language selected: {lang} for user: {user_id} (@{username})")
        
        # Check if user exists
        user = await Database.get_user(user_id)
        is_new_user = False
        
        if not user:
            # Create new user
            logger.info(f"Creating new user: {user_id}")
            await Database.create_user(
                user_id, username, first_name, last_name, "", lang
            )
            is_new_user = True
            
            # Log user creation
            await Database.log_audit(
                user_id=user_id,
                action="user_created",
                entity_type="user",
                entity_id=str(user_id),
                new_value={"username": username, "first_name": first_name, "last_name": last_name, "lang": lang}
            )
        else:
            # Update existing user's language
            logger.info(f"Updating language for existing user: {user_id}")
            await Database.update_user(user_id, lang=lang)
            
            # Log language change
            await Database.log_audit(
                user_id=user_id,
                action="language_changed",
                entity_type="user",
                entity_id=str(user_id),
                old_value={"lang": user.get("lang")},
                new_value={"lang": lang}
            )
        
        # Get updated user data
        user_data = await Database.get_user(user_id)
        balance = float(user_data.get("balance", 0)) if user_data else 0
        
        # Edit the original message to show welcome text
        welcome_text = TEXTS[lang]['welcome']
        if is_new_user:
            welcome_text += f"\n\n{get_emoji('gift')} *Welcome Bonus!*\nYou received a welcome bonus of 30 ETB!"
        
        await query.edit_message_text(
            welcome_text,
            parse_mode='Markdown'
        )
        
        # Send personalized welcome message with balance
        await query.message.reply_text(
            f"{get_emoji('click')} *Choose an option from the menu below:*\n\n"
            f"{get_emoji('money')} Your balance: *{balance:.2f} ETB*\n"
            f"{get_emoji('game')} Ready to play? Click /play to start!",
            reply_markup=menu(lang),
            parse_mode='Markdown'
        )
        
        # Send helpful tips for new users
        if is_new_user:
            await query.message.reply_text(
                f"{get_emoji('info')} *Quick Tips:*\n\n"
                f"• Use /play to start the Bingo game\n"
                f"• Use /deposit to add funds\n"
                f"• Use /balance to check your balance\n"
                f"• Use /invite to invite friends and earn bonuses\n"
                f"• Use /daily to claim your daily bonus\n\n"
                f"Need help? Contact our support group: {get_emoji('support')}",
                parse_mode='Markdown'
            )
        
        logger.info(f"Language selection completed successfully for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error in language_callback for user {user_id}: {e}")
        try:
            await query.edit_message_text(
                f"{get_emoji('error')} *An error occurred.*\n\n"
                f"Please try /start again.\n\n"
                f"If the problem persists, contact support.",
                parse_mode='Markdown'
            )
        except Exception as edit_error:
            logger.error(f"Could not edit message: {edit_error}")
            await query.message.reply_text(
                f"{get_emoji('error')} *An error occurred.*\n\n"
                f"Please try /start again.",
                parse_mode='Markdown'
            )


# Optional: Add a help command to show available commands
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available commands and help information"""
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    help_text = f"""
{get_emoji('help')} *ESTIF BINGO 24/7 - HELP CENTER* {get_emoji('help')}

*🎮 Game Commands:*
• /play - Start playing Bingo
• /bingo - Get OTP code for game login
• /verify <code> - Verify OTP code

*💰 Financial Commands:*
• /balance - Check your balance
• /deposit - Add funds to your account
• /cashout - Withdraw your winnings
• /transfer - Send money to another player

*👤 Account Commands:*
• /register - Register your phone number
• /invite - Get your referral link
• /daily - Claim daily bonus

*📞 Support:*
• /contact - Contact support
• /help - Show this help message

*👑 Admin Commands:*
• /admin - Admin panel
• /stats - Bot statistics
• /setwin <percentage> - Set win percentage

{get_emoji('info')} *Need more help?* Join our support group: {get_emoji('support')}
    """
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=menu(lang)
    )


# Optional: Command to show bot information
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot information and version"""
    user_id = update.effective_user.id
    user = await Database.get_user(user_id)
    lang = user.get('lang', 'en') if user else 'en'
    
    about_text = f"""
{get_emoji('game')} *ESTIF BINGO 24/7* {get_emoji('game')}

*Version:* 4.0.0
*Developer:* Estif Bingo Team
*Platform:* Telegram Bot + Web App

*Features:*
• Real-time multiplayer Bingo game
• Secure deposit and withdrawal system
• Instant balance transfers
• Referral program with bonuses
• Daily bonus rewards
• Multi-language support (English/Amharic)
• 24/7 customer support

*Game Statistics:*
• Win rates up to 80%
• 1000+ unique cartelas
• Real-time number drawing
• Multiple winning patterns

*Links:*
• Support Channel: https://t.me/temarineh
• Support Group: https://t.me/presectionA

*Thank you for playing with us!* 🎉
    """
    
    await update.message.reply_text(
        about_text,
        parse_mode='Markdown',
        reply_markup=menu(lang)
    )


# Export all handlers
__all__ = [
    'start',
    'language_callback',
    'help_command',
    'about_command'
]