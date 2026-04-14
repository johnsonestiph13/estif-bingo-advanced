# telegram-bot/bot/main.py
# Estif Bingo 24/7 - ULTRA ENHANCED MAIN FILE
# Features: Multi-instance lock, webhook cleanup, health monitoring, auto-recovery

import asyncio
import logging
import sys
import threading
import traceback
import os
import fcntl
import atexit
import time
import signal
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from bot.config import BOT_TOKEN, FLASK_PORT, LOG_LEVEL, LOG_FORMAT
from bot.db.database import Database

# Configure logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/bot.log') if os.path.exists('logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if not exists
os.makedirs('logs', exist_ok=True)

# ==================== SINGLE INSTANCE LOCK ====================
_lock_file = None

def acquire_instance_lock():
    """Acquire a lock to ensure only one bot instance runs"""
    global _lock_file
    try:
        lock_dir = '/tmp' if os.path.exists('/tmp') else os.path.dirname(os.path.abspath(__file__))
        lock_path = os.path.join(lock_dir, 'estif_bingo_bot.lock')
        _lock_file = open(lock_path, 'w')
        fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        atexit.register(release_instance_lock)
        logger.info("✅ Acquired instance lock")
        return True
    except (IOError, OSError):
        logger.error("❌ Another bot instance is already running! Exiting...")
        return False

def release_instance_lock():
    """Release the instance lock"""
    global _lock_file
    if _lock_file:
        try:
            fcntl.flock(_lock_file, fcntl.LOCK_UN)
            _lock_file.close()
            logger.info("✅ Released instance lock")
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")

# ==================== SIGNAL HANDLERS ====================
def setup_signal_handlers():
    """Setup graceful shutdown handlers"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        release_instance_lock()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

# ==================== FLASK API SERVER ====================
def run_flask():
    """Run Flask in a separate thread for Game API"""
    from flask import Flask, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "healthy",
            "bot": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": time.time() - start_time if 'start_time' in dir() else 0
        }), 200
    
    @app.route('/ready', methods=['GET'])
    def ready_check():
        return jsonify({"status": "ready"}), 200
    
    from bot.api.game_api import game_api_bp
    app.register_blueprint(game_api_bp)
    logger.info("✅ Game API blueprint registered")
    
    from bot.api.webhooks import webhook_bp
    app.register_blueprint(webhook_bp)
    logger.info("✅ Webhook blueprint registered")
    
    app.run(host='0.0.0.0', port=FLASK_PORT, threaded=True, use_reloader=False)

# ==================== TELEGRAM BOT ====================
async def cleanup_bot_environment():
    """Clean up any existing bot sessions and webhooks"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Delete webhook
            webhook_response = await client.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
            if webhook_response.status_code == 200:
                logger.info("✅ Webhook deleted")
            
            # Get webhook info to verify
            info_response = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
            if info_response.status_code == 200:
                info = info_response.json()
                if info.get('ok'):
                    logger.info(f"📡 Webhook info: {info.get('result', {})}")
            
            # Clear any pending updates
            await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1&timeout=1")
            logger.info("✅ Cleared pending updates")
            
    except Exception as e:
        logger.warning(f"Cleanup warning: {e}")

def run_bot():
    """Run Telegram bot in the main thread"""
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, ConversationHandler,
        filters, CallbackQueryHandler, Defaults
    )
    from telegram.constants import ParseMode
    
    # Import all handlers
    from bot.handlers.start import start, language_callback
    from bot.handlers.register import register, handle_contact, register_phone, register_cancel, PHONE
    from bot.handlers.deposit import (
        deposit, deposit_callback, 
        deposit_amount, deposit_screenshot, deposit_cancel,
        AMOUNT as DEPOSIT_AMOUNT, SCREENSHOT
    )
    from bot.handlers.cashout import (
        cashout, cashout_callback, 
        cashout_amount, cashout_account, cashout_cancel,
        AMOUNT as CASHOUT_AMOUNT, ACCOUNT
    )
    from bot.handlers.balance import balance
    from bot.handlers.invite import invite
    from bot.handlers.contact import contact_center
    from bot.handlers.bingo_otp import bingo_otp, verify_otp
    from bot.handlers.admin_commands import (
        approve_deposit, reject_deposit,
        approve_cashout, reject_cashout,
        admin_panel, admin_callback,
        set_win_percentage, stats_command
    )
    from bot.handlers.transfer import (
        transfer, transfer_phone, transfer_amount, 
        transfer_confirm, transfer_cancel, transfer_cancel_command,
        transfer_add_amount, transfer_subtract_amount,
        PHONE_NUMBER, AMOUNT as TRANSFER_AMOUNT, CONFIRM
    )
    from bot.handlers.game import (
        play_command, game_callback,
        stats_callback, leaderboard_callback, back_to_game_callback,
        start_game_handlers
    )
    
    async def play(update, context):
        await play_command(update, context)
    
    async def handle_all_text(update, context):
        if await deposit_amount(update, context):
            return
        if await cashout_amount(update, context):
            return
        if await cashout_account(update, context):
            return
        
        from bot.texts.locales import TEXTS
        from bot.keyboards.menu import menu
        user = await Database.get_user(update.effective_user.id)
        lang = user.get('lang', 'en') if user else 'en'
        await update.message.reply_text(
            TEXTS[lang]['use_menu'], 
            reply_markup=menu(lang)
        )
    
    # Optimized defaults
    defaults = Defaults(
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        disable_notification=False,
        protect_content=False
    )
    
    # Create application with optimized settings
    application = Application.builder() \
        .token(BOT_TOKEN) \
        .defaults(defaults) \
        .connect_timeout(20.0) \
        .read_timeout(20.0) \
        .write_timeout(20.0) \
        .get_updates_connect_timeout(20.0) \
        .get_updates_read_timeout(20.0) \
        .get_updates_write_timeout(20.0) \
        .pool_timeout(30.0) \
        .build()
    
    # ==================== COMMAND HANDLERS ====================
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("bingo", bingo_otp))
    application.add_handler(CommandHandler("verify", verify_otp))
    application.add_handler(CommandHandler("invite", invite))
    application.add_handler(CommandHandler("contact", contact_center))
    application.add_handler(CommandHandler("play", play_command))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("setwin", set_win_percentage))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("approve_deposit", approve_deposit))
    application.add_handler(CommandHandler("reject_deposit", reject_deposit))
    application.add_handler(CommandHandler("approve_cashout", approve_cashout))
    application.add_handler(CommandHandler("reject_cashout", reject_cashout))
    
    # ==================== MESSAGE HANDLERS ====================
    application.add_handler(MessageHandler(filters.PHOTO, deposit_screenshot))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # Menu button handlers
    application.add_handler(MessageHandler(filters.Regex("^🎮 Play$|^🎮 ጨዋታ$"), play_command))
    application.add_handler(MessageHandler(filters.Regex("📝 Register|📝 ተመዝገብ"), register))
    application.add_handler(MessageHandler(filters.Regex("💰 Deposit|💰 ገንዘብ አስገባ"), deposit))
    application.add_handler(MessageHandler(filters.Regex("💳 Cash Out|💳 ገንዘብ አውጣ"), cashout))
    application.add_handler(MessageHandler(filters.Regex("💸 Transfer|💸 ገንዘብ አስተላልፍ"), transfer))
    application.add_handler(MessageHandler(filters.Regex("📞 Contact Center|📞 ደንበኛ አገልግሎት"), contact_center))
    application.add_handler(MessageHandler(filters.Regex("🎉 Invite|🎉 ጋብዝ"), invite))
    application.add_handler(MessageHandler(filters.Regex("🔐 Bingo Code|🔐 የቢንጎ ኮድ"), bingo_otp))
    
    # Catch-all text handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text))
    
    # ==================== CALLBACK QUERY HANDLERS ====================
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(deposit_callback, pattern="^deposit_"))
    application.add_handler(CallbackQueryHandler(cashout_callback, pattern="^cashout_"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    
    # Game callbacks
    application.add_handler(CallbackQueryHandler(stats_callback, pattern="^game_stats$"))
    application.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^game_leaderboard$"))
    application.add_handler(CallbackQueryHandler(back_to_game_callback, pattern="^back_to_game$"))
    application.add_handler(CallbackQueryHandler(play_command, pattern="^game_menu$"))
    application.add_handler(CallbackQueryHandler(play_command, pattern="^play$"))
    
    # Transfer callbacks
    application.add_handler(CallbackQueryHandler(transfer_confirm, pattern="^transfer_confirm$"))
    application.add_handler(CallbackQueryHandler(transfer_cancel, pattern="^transfer_cancel$"))
    application.add_handler(CallbackQueryHandler(transfer_add_amount, pattern="^transfer_add_10$"))
    application.add_handler(CallbackQueryHandler(transfer_subtract_amount, pattern="^transfer_sub_10$"))
    
    # ==================== CONVERSATION HANDLERS ====================
    
    transfer_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(transfer, pattern="^transfer$"),
            MessageHandler(filters.Regex("💸 Transfer|💸 ገንዘብ አስተላልፍ"), transfer)
        ],
        states={
            PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_phone)],
            TRANSFER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_amount)],
            CONFIRM: [
                CallbackQueryHandler(transfer_confirm, pattern="^transfer_confirm$"),
                CallbackQueryHandler(transfer_cancel, pattern="^transfer_cancel$"),
                CallbackQueryHandler(transfer_add_amount, pattern="^transfer_add_10$"),
                CallbackQueryHandler(transfer_subtract_amount, pattern="^transfer_sub_10$")
            ]
        },
        fallbacks=[CommandHandler("cancel", transfer_cancel_command)],
        name="transfer_conversation",
        persistent=False,
        allow_reentry=True
    )
    application.add_handler(transfer_conv)
    
    register_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(register, pattern="^register$"),
            MessageHandler(filters.Regex("📝 Register|📝 ተመዝገብ"), register)
        ],
        states={
            PHONE: [
                MessageHandler(filters.CONTACT, register_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)
            ]
        },
        fallbacks=[CommandHandler("cancel", register_cancel)],
        name="register_conversation",
        persistent=False
    )
    application.add_handler(register_conv)
    
    deposit_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(deposit, pattern="^deposit$"),
            MessageHandler(filters.Regex("💰 Deposit|💰 ገንዘብ አስገባ"), deposit)
        ],
        states={
            DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, deposit_screenshot)]
        },
        fallbacks=[CommandHandler("cancel", deposit_cancel)],
        name="deposit_conversation",
        persistent=False
    )
    application.add_handler(deposit_conv)
    
    cashout_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(cashout, pattern="^cashout$"),
            MessageHandler(filters.Regex("💳 Cash Out|💳 ገንዘብ አውጣ"), cashout)
        ],
        states={
            CASHOUT_AMOUNT: [
                CallbackQueryHandler(cashout_callback, pattern="^cashout_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, cashout_amount)
            ],
            ACCOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, cashout_account)
            ],
        },
        fallbacks=[CommandHandler("cancel", cashout_cancel)],
        name="cashout_conversation",
        persistent=False
    )
    application.add_handler(cashout_conv)
    
    # ==================== WEB APP DATA HANDLER ====================
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, game_callback))
    
    # ==================== ERROR HANDLER ====================
    async def error_handler(update, context):
        logger.error(f"Update {update} caused error {context.error}")
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "⚠️ An error occurred. Please try again later."
                )
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    application.add_error_handler(error_handler)
    
    # ==================== START BOT ====================
    logger.info("🤖 Estif Bingo Bot started successfully!")
    logger.info("📦 Features: Transfer | Game | Deposit | Cashout | Web App | OTP")
    
    # Run the bot with enhanced polling
    try:
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query', 'web_app_data'],
            stop_signals=None,
            poll_interval=0.5,
            timeout=30
        )
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        traceback.print_exc()
        raise

# ==================== MAIN ENTRY POINT ====================
start_time = time.time()

async def async_main():
    """Async main function for database initialization"""
    # Clean up any existing bot sessions
    await cleanup_bot_environment()
    
    # Initialize database
    await Database.init_pool()
    logger.info("✅ Database initialized")
    
    # Initialize game handlers
    from bot.handlers.game import start_game_handlers
    await start_game_handlers()
    logger.info("🎮 Game handlers initialized")

def main():
    """Main entry point"""
    # Setup signal handlers
    setup_signal_handlers()
    
    # Acquire instance lock
    if not acquire_instance_lock():
        sys.exit(1)
    
    # Run async initialization
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_main())
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info(f"🚀 Flask API running on port {FLASK_PORT}")
    logger.info("📡 Endpoints available:")
    logger.info("   - POST /api/verify-code")
    logger.info("   - POST /api/exchange-code")
    logger.info("   - POST /api/deduct")
    logger.info("   - POST /api/add")
    logger.info("   - GET  /api/balance/<id>")
    logger.info("   - POST /api/transfer")
    logger.info("   - GET  /api/commission")
    logger.info("   - GET  /health")
    logger.info("   - GET  /ready")
    
    # Run bot (blocking)
    run_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
        release_instance_lock()
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        traceback.print_exc()
        release_instance_lock()
        sys.exit(1)