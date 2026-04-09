# main.py - UPDATED VERSION WITH GAME API BLUEPRINT

import asyncio
import logging
import sys
import threading
from dotenv import load_dotenv

load_dotenv()

from .config import BOT_TOKEN, FLASK_PORT, LOG_LEVEL, LOG_FORMAT
from .db.database import Database

logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)


def run_flask():
    """Run Flask in a separate thread"""
    from .api import create_flask_app
    app = create_flask_app()
    
    # Register game API blueprint
    from .api.game_api import game_api_bp
    app.register_blueprint(game_api_bp)
    logger.info("✅ Game API blueprint registered")
    
    app.run(host='0.0.0.0', port=FLASK_PORT, threaded=True, use_reloader=False)


def run_bot():
    """Run Telegram bot in a separate thread"""
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        filters, CallbackQueryHandler
    )
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
    
    async def play(update, context):
        from .handlers.register import play as play_handler
        await play_handler(update, context)
    
    async def handle_all_text(update, context):
        if await handle_deposit_amount(update, context):
            return
        if await handle_cashout_amount(update, context):
            return
        if await handle_cashout_account(update, context):
            return
        from .texts.locales import TEXTS
        from .keyboards.menu import menu
        user = await Database.get_user(update.effective_user.id)
        lang = user.get('lang', 'en') if user else 'en'
        await update.message.reply_text(TEXTS[lang]['use_menu'], reply_markup=menu(lang))
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("bingo", bingo_otp))
    application.add_handler(CommandHandler("approve_deposit", approve_deposit))
    application.add_handler(CommandHandler("reject_deposit", reject_deposit))
    application.add_handler(CommandHandler("approve_cashout", approve_cashout))
    application.add_handler(CommandHandler("reject_cashout", reject_cashout))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_deposit_screenshot))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # Add menu button handlers
    application.add_handler(MessageHandler(filters.Regex("🎮 Play|🎮 ጨዋታ"), play))
    application.add_handler(MessageHandler(filters.Regex("📝 Register|📝 ተመዝገብ"), register))
    application.add_handler(MessageHandler(filters.Regex("💰 Deposit|💰 ገንዘብ አስገባ"), deposit))
    application.add_handler(MessageHandler(filters.Regex("💳 Cash Out|💳 ገንዘብ አውጣ"), cashout))
    application.add_handler(MessageHandler(filters.Regex("📞 Contact Center|📞 ደንበኛ አገልግሎት"), contact_center))
    application.add_handler(MessageHandler(filters.Regex("🎉 Invite|🎉 ጋብዝ"), invite))
    application.add_handler(MessageHandler(filters.Regex("🔐 Bingo Code|🔐 የቢንጎ ኮድ"), bingo_otp))
    
    # Add text handler for unhandled messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text))
    
    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(language_callback, pattern="lang_"))
    application.add_handler(CallbackQueryHandler(deposit_callback, pattern="dep_"))
    application.add_handler(CallbackQueryHandler(cashout_callback, pattern="cash_"))
    
    logger.info("🤖 Estif Bingo Bot started successfully!")
    
    # Run the bot (this blocks)
    application.run_polling()


def main():
    """Main entry point"""
    # Run database init in async loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(Database.init_pool())
    logger.info("✅ Database initialized")
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"🚀 Flask API running on port {FLASK_PORT}")
    logger.info(f"📡 Game API endpoints available at: /api/commission, /api/deduct, /api/add, etc.")
    
    # Run bot in main thread (this blocks)
    run_bot()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)