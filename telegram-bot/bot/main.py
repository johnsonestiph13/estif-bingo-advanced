# main.py - FIXED for Render
import asyncio
import logging
import threading
import sys
from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, CallbackQueryHandler
)

load_dotenv()

from .config import BOT_TOKEN, FLASK_PORT, LOG_LEVEL, LOG_FORMAT
from .db.database import Database
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

logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL, logging.INFO)
)
logger = logging.getLogger(__name__)


def run_flask():
    """Run Flask API server in separate thread."""
    try:
        from .api import create_flask_app
        app = create_flask_app()
        # Bind to all interfaces, use PORT from environment or default 8080
        port = int(os.environ.get("FLASK_PORT", 8080))
        app.run(host='0.0.0.0', port=port, threaded=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")


async def play(update, context):
    try:
        from .handlers.register import play as play_handler
        await play_handler(update, context)
    except Exception as e:
        logger.error(f"Play handler error: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")


async def handle_all_text(update, context):
    try:
        if await handle_deposit_amount(update, context):
            return
        if await handle_cashout_amount(update, context):
            return
        if await handle_cashout_account(update, context):
            return
        
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


async def main():
    # Initialize database
    await Database.init_pool()
    logger.info("✅ Database initialized")
    
    # Start Flask API in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"Flask API starting on port {FLASK_PORT}")
    
    # Create bot application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("bingo", bingo_otp))
    application.add_handler(CommandHandler("approve_deposit", approve_deposit))
    application.add_handler(CommandHandler("reject_deposit", reject_deposit))
    application.add_handler(CommandHandler("approve_cashout", approve_cashout))
    application.add_handler(CommandHandler("reject_cashout", reject_cashout))
    
    application.add_handler(MessageHandler(filters.PHOTO, handle_deposit_screenshot))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    application.add_handler(MessageHandler(filters.Regex("🎮 Play|🎮 ጨዋታ"), play))
    application.add_handler(MessageHandler(filters.Regex("📝 Register|📝 ተመዝገብ"), register))
    application.add_handler(MessageHandler(filters.Regex("💰 Deposit|💰 ገንዘብ አስገባ"), deposit))
    application.add_handler(MessageHandler(filters.Regex("💳 Cash Out|💳 ገንዘብ አውጣ"), cashout))
    application.add_handler(MessageHandler(filters.Regex("📞 Contact Center|📞 ደንበኛ አገልግሎት"), contact_center))
    application.add_handler(MessageHandler(filters.Regex("🎉 Invite|🎉 ጋብዝ"), invite))
    application.add_handler(MessageHandler(filters.Regex("🔐 Bingo Code|🔐 የቢንጎ ኮድ"), bingo_otp))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text))
    
    application.add_handler(CallbackQueryHandler(language_callback, pattern="lang_"))
    application.add_handler(CallbackQueryHandler(deposit_callback, pattern="dep_"))
    application.add_handler(CallbackQueryHandler(cashout_callback, pattern="cash_"))
    
    logger.info("🤖 Estif Bingo Bot started successfully!")
    
    # Start polling
    await application.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)