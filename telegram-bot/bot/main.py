# main.py - OPTIMIZED VERSION

import asyncio
import logging
import threading
import sys
from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, CallbackQueryHandler
)

# Load environment variables
load_dotenv()

# Import configurations
from .config import BOT_TOKEN, FLASK_PORT, LOG_LEVEL, LOG_FORMAT

# Import database
from .db.database import Database

# Import handlers
from .handlers.start import start, language_callback
from .handlers.register import register, handle_contact
from .handlers.deposit import deposit, deposit_callback, handle_deposit_amount, handle_deposit_screenshot
from .handlers.cashout import cashout, cashout_callback, handle_cashout_amount, handle_cashout_account
from .handlers.balance import balance
from .handlers.invite import invite
from .handlers.contact import contact_center
from .handlers.bingo_otp import bingo_otp
from .handlers.admin_commands import (
    approve_deposit, reject_deposit,
    approve_cashout, reject_cashout
)

# Configure logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL, logging.INFO)
)
logger = logging.getLogger(__name__)


def run_flask():
    """Run Flask API server in separate thread"""
    try:
        from .api import create_flask_app
        app = create_flask_app()
        app.run(host='0.0.0.0', port=FLASK_PORT, threaded=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")


async def play(update, context):
    """Play game handler"""
    try:
        from .handlers.register import play as play_handler
        await play_handler(update, context)
    except Exception as e:
        logger.error(f"Play handler error: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")


async def handle_all_text(update, context):
    """Route text to appropriate flow handler"""
    try:
        # Check deposit flow
        if await handle_deposit_amount(update, context):
            return
        
        # Check cashout flow
        if await handle_cashout_amount(update, context):
            return
        
        if await handle_cashout_account(update, context):
            return
        
        # If no flow matches, show menu prompt
        from .db.database import Database
        from .texts.locales import TEXTS
        from .keyboards.menu import menu
        
        telegram_id = update.effective_user.id
        user = await Database.get_user(telegram_id)
        lang = user.get('lang', 'en') if user else 'en'
        
        await update.message.reply_text(
            TEXTS[lang]['use_menu'],
            reply_markup=menu(lang)
        )
    except Exception as e:
        logger.error(f"Text handler error: {e}")
        await update.message.reply_text("❌ An error occurred. Please use the menu buttons.")


async def start_bot():
    """Start the bot application"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("bingo", bingo_otp))
    application.add_handler(CommandHandler("approve_deposit", approve_deposit))
    application.add_handler(CommandHandler("reject_deposit", reject_deposit))
    application.add_handler(CommandHandler("approve_cashout", approve_cashout))
    application.add_handler(CommandHandler("reject_cashout", reject_cashout))
    
    # Message handlers (order matters - more specific first)
    application.add_handler(MessageHandler(filters.PHOTO, handle_deposit_screenshot))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # Menu button handlers
    application.add_handler(MessageHandler(filters.Regex("🎮 Play|🎮 ጨዋታ"), play))
    application.add_handler(MessageHandler(filters.Regex("📝 Register|📝 ተመዝገብ"), register))
    application.add_handler(MessageHandler(filters.Regex("💰 Deposit|💰 ገንዘብ አስገባ"), deposit))
    application.add_handler(MessageHandler(filters.Regex("💳 Cash Out|💳 ገንዘብ አውጣ"), cashout))
    application.add_handler(MessageHandler(filters.Regex("📞 Contact Center|📞 ደንበኛ አገልግሎት"), contact_center))
    application.add_handler(MessageHandler(filters.Regex("🎉 Invite|🎉 ጋብዝ"), invite))
    application.add_handler(MessageHandler(filters.Regex("🔐 Bingo Code|🔐 የቢንጎ ኮድ"), bingo_otp))
    
    # Flow handlers (catch-all for text)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(language_callback, pattern="lang_"))
    application.add_handler(CallbackQueryHandler(deposit_callback, pattern="dep_"))
    application.add_handler(CallbackQueryHandler(cashout_callback, pattern="cash_"))
    
    logger.info("🤖 Estif Bingo Bot started successfully!")
    
    # Start polling (blocks until stopped)
    await application.run_polling()


async def main_async():
    """Main async entry point"""
    try:
        # Initialize database
        await Database.init_pool()
        logger.info("✅ Database initialized")
        
        # Start Flask API in background thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info(f"Flask API starting on port {FLASK_PORT}")
        
        # Start the bot
        await start_bot()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


def main():
    """Main entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()