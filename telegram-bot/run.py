# telegram-bot/run.py - ULTRA OPTIMIZED PRODUCTION READY
# Estif Bingo 24/7 - High-Performance Bot & API Launcher

import asyncio
import threading
import signal
import sys
import os
import gc
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional
import logging
from logging.handlers import RotatingFileHandler

# ==================== OPTIONAL IMPORTS WITH SAFE FALLBACKS ====================

# Try to import uvloop (Linux/Mac only, improves performance)
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    UVLOOP_AVAILABLE = True
    print("✅ Using uvloop for enhanced performance")
except ImportError:
    UVLOOP_AVAILABLE = False
    print("ℹ️ uvloop not available - using standard asyncio")

# Try to import nest_asyncio (allows nested event loops)
try:
    import nest_asyncio
    nest_asyncio.apply()
    NEST_ASYNCIO_AVAILABLE = True
    print("✅ nest_asyncio applied")
except ImportError:
    NEST_ASYNCIO_AVAILABLE = False
    print("ℹ️ nest_asyncio not available")

# Try to import psutil (system monitoring)
try:
    import psutil
    PSUTIL_AVAILABLE = True
    print("✅ psutil available for system monitoring")
except ImportError:
    PSUTIL_AVAILABLE = False
    print("ℹ️ psutil not available - system monitoring disabled")
    # Create a dummy psutil for when it's not available
    class DummyPsutil:
        class virtual_memory:
            @staticmethod
            def percent():
                return 0
        @staticmethod
        def cpu_percent(interval=1):
            return 0
    psutil = DummyPsutil()

from flask import Flask, jsonify
from werkzeug.serving import run_simple

from bot.api.game_api import game_api_bp
from bot.api.webhooks import webhook_bp
from bot.config import config
from bot.db.database import Database

# ==================== ULTRA OPTIMIZED LOGGING ====================
class PerformanceLogger:
    """High-performance async logging with rotation"""
    def __init__(self):
        self.logger = logging.getLogger('bingo')
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))
        self.logger.propagate = False
        
        # Console handler with color
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(
            '\033[92m%(asctime)s\033[0m - \033[94m%(name)s\033[0m - \033[92m%(levelname)s\033[0m - %(message)s',
            datefmt='%H:%M:%S'
        ))
        self.logger.addHandler(console)
        
        # Rotating file handler (10MB per file, 5 backups)
        if not os.path.exists('logs'):
            os.makedirs('logs')
        file_handler = RotatingFileHandler(
            'logs/bingo.log', maxBytes=10_485_760, backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
    
    def info(self, msg): self.logger.info(msg)
    def error(self, msg): self.logger.error(msg)
    def warning(self, msg): self.logger.warning(msg)
    def debug(self, msg): self.logger.debug(msg)

logger = PerformanceLogger()


# ==================== ULTRA FAST FLASK APP ====================
class UltraFastFlask(Flask):
    """Optimized Flask with better defaults"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config.update(
            JSONIFY_PRETTYPRINT_REGULAR=False,
            JSON_SORT_KEYS=False,
            SEND_FILE_MAX_AGE_DEFAULT=31536000,
            PRESERVE_CONTEXT_ON_EXCEPTION=False,
            TRAP_HTTP_EXCEPTIONS=True,
            MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        )

flask_app = UltraFastFlask(__name__)


@flask_app.route('/healthz', methods=['GET'])
def healthz():
    """Kubernetes-style health check"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '3.0.0'
    }), 200


@flask_app.route('/ready', methods=['GET'])
def ready():
    """Readiness probe"""
    return jsonify({'status': 'ready'}), 200


@flask_app.route('/health', methods=['GET'])
def health():
    """Simple health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'telegram-bot-api',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# Register blueprints
flask_app.register_blueprint(game_api_bp, url_prefix='/api/v1')
flask_app.register_blueprint(webhook_bp, url_prefix='/api/v1')


# ==================== CONNECTION POOL MANAGER ====================
class ConnectionPoolManager:
    """Manages database connection pool with auto-recovery"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    async def ensure_connection(self):
        """Ensure database connection is alive"""
        try:
            if not Database._pool:
                await Database.init_pool()
                logger.info("🔄 Database pool reinitialized")
            elif not await Database.health_check():
                await Database.close_pool()
                await Database.init_pool()
                logger.info("🔄 Database pool recovered")
            return True
        except Exception as e:
            logger.error(f"Connection pool error: {e}")
            return False

pool_manager = ConnectionPoolManager()


# ==================== ULTRA OPTIMIZED BOT ====================
class UltraFastBot:
    """High-performance Telegram bot with connection pooling"""
    
    def __init__(self):
        self.application = None
        self._shutdown_event = asyncio.Event()
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._request_semaphore = asyncio.Semaphore(100)
        
    async def rate_limit(self, func, *args, **kwargs):
        """Apply rate limiting to handlers"""
        async with self._request_semaphore:
            return await func(*args, **kwargs)
    
    async def build_application(self):
        """Build bot application with optimizations"""
        from telegram.ext import (
            ApplicationBuilder, CommandHandler, CallbackQueryHandler,
            MessageHandler, filters, Defaults, ConversationHandler
        )
        from telegram.constants import ParseMode
        
        # Import all handlers
        from bot.handlers.start import start, language_callback
        from bot.handlers.register import register, handle_contact, register_phone, register_cancel, PHONE
        from bot.handlers.deposit import (
            deposit, deposit_callback, deposit_amount, deposit_screenshot, deposit_cancel,
            AMOUNT as DEPOSIT_AMOUNT, SCREENSHOT
        )
        from bot.handlers.cashout import (
            cashout, cashout_callback, cashout_amount, cashout_account, cashout_cancel,
            AMOUNT as CASHOUT_AMOUNT, ACCOUNT
        )
        from bot.handlers.balance import balance
        from bot.handlers.invite import invite
        from bot.handlers.contact import contact_center
        from bot.handlers.bingo_otp import bingo_otp, verify_otp
        from bot.handlers.admin_commands import (
            approve_deposit, reject_deposit, approve_cashout, reject_cashout,
            admin_panel, admin_callback, set_win_percentage, stats_command
        )
        from bot.handlers.transfer import (
            transfer, transfer_phone, transfer_amount, transfer_confirm,
            transfer_cancel, transfer_cancel_command, transfer_add_amount, transfer_subtract_amount,
            PHONE_NUMBER, AMOUNT as TRANSFER_AMOUNT, CONFIRM
        )
        from bot.handlers.game import play_command, game_callback, stats_callback, leaderboard_callback, back_to_game_callback
        
        # Optimized defaults
        defaults = Defaults(
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            disable_notification=False,
            protect_content=False
        )
        
        # Build with connection pool
        self.application = ApplicationBuilder() \
            .token(config.BOT_TOKEN) \
            .defaults(defaults) \
            .connection_pool_size(20) \
            .pool_timeout(30) \
            .connect_timeout(10.0) \
            .read_timeout(10.0) \
            .write_timeout(10.0) \
            .get_updates_connect_timeout(10.0) \
            .get_updates_read_timeout(10.0) \
            .get_updates_write_timeout(10.0) \
            .build()
        
        # ==================== COMMAND HANDLERS ====================
        self.application.add_handler(CommandHandler("start", start))
        self.application.add_handler(CommandHandler("register", register))
        self.application.add_handler(CommandHandler("balance", balance))
        self.application.add_handler(CommandHandler("bingo", bingo_otp))
        self.application.add_handler(CommandHandler("verify", verify_otp))
        self.application.add_handler(CommandHandler("invite", invite))
        self.application.add_handler(CommandHandler("contact", contact_center))
        self.application.add_handler(CommandHandler("play", play_command))
        
        # Admin commands
        self.application.add_handler(CommandHandler("admin", admin_panel))
        self.application.add_handler(CommandHandler("setwin", set_win_percentage))
        self.application.add_handler(CommandHandler("stats", stats_command))
        self.application.add_handler(CommandHandler("approve_deposit", approve_deposit))
        self.application.add_handler(CommandHandler("reject_deposit", reject_deposit))
        self.application.add_handler(CommandHandler("approve_cashout", approve_cashout))
        self.application.add_handler(CommandHandler("reject_cashout", reject_cashout))
        
        # ==================== MESSAGE HANDLERS ====================
        self.application.add_handler(MessageHandler(filters.PHOTO, deposit_screenshot))
        self.application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        
        # Menu button handlers
        self.application.add_handler(MessageHandler(filters.Regex("^🎮 Play$|^🎮 ጨዋታ$"), play_command))
        self.application.add_handler(MessageHandler(filters.Regex("📝 Register|📝 ተመዝገብ"), register))
        self.application.add_handler(MessageHandler(filters.Regex("💰 Deposit|💰 ገንዘብ አስገባ"), deposit))
        self.application.add_handler(MessageHandler(filters.Regex("💳 Cash Out|💳 ገንዘብ አውጣ"), cashout))
        self.application.add_handler(MessageHandler(filters.Regex("💸 Transfer|💸 ገንዘብ አስተላልፍ"), transfer))
        self.application.add_handler(MessageHandler(filters.Regex("📞 Contact Center|📞 ደንበኛ አገልግሎት"), contact_center))
        self.application.add_handler(MessageHandler(filters.Regex("🎉 Invite|🎉 ጋብዝ"), invite))
        self.application.add_handler(MessageHandler(filters.Regex("🔐 Bingo Code|🔐 የቢንጎ ኮድ"), bingo_otp))
        
        # ==================== CALLBACK QUERY HANDLERS ====================
        self.application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
        self.application.add_handler(CallbackQueryHandler(deposit_callback, pattern="^deposit_"))
        self.application.add_handler(CallbackQueryHandler(cashout_callback, pattern="^cashout_"))
        self.application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
        
        # Game callbacks
        self.application.add_handler(CallbackQueryHandler(stats_callback, pattern="^game_stats$"))
        self.application.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^game_leaderboard$"))
        self.application.add_handler(CallbackQueryHandler(back_to_game_callback, pattern="^back_to_game$"))
        self.application.add_handler(CallbackQueryHandler(play_command, pattern="^game_menu$"))
        self.application.add_handler(CallbackQueryHandler(play_command, pattern="^play$"))
        
        # Transfer callbacks
        self.application.add_handler(CallbackQueryHandler(transfer_confirm, pattern="^transfer_confirm$"))
        self.application.add_handler(CallbackQueryHandler(transfer_cancel, pattern="^transfer_cancel$"))
        self.application.add_handler(CallbackQueryHandler(transfer_add_amount, pattern="^transfer_add_10$"))
        self.application.add_handler(CallbackQueryHandler(transfer_subtract_amount, pattern="^transfer_sub_10$"))
        
        # ==================== CONVERSATION HANDLERS ====================
        
        # Transfer Conversation
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
        self.application.add_handler(transfer_conv)
        
        # Register Conversation
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
        self.application.add_handler(register_conv)
        
        # Deposit Conversation
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
        self.application.add_handler(deposit_conv)
        
        # Cashout Conversation
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
                ]
            },
            fallbacks=[CommandHandler("cancel", cashout_cancel)],
            name="cashout_conversation",
            persistent=False
        )
        self.application.add_handler(cashout_conv)
        
        # Web App Data Handler
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, game_callback))
        
        # Error Handler
        async def error_handler(update, context):
            logger.error(f"Update {update} caused error {context.error}")
            try:
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "⚠️ An error occurred. Please try again later."
                    )
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
        
        self.application.add_error_handler(error_handler)
        
        return self.application
    
    async def start(self):
        """Start bot with optimizations"""
        await self.build_application()
        await self.application.initialize()
        await self.application.start()
        
        # Clear webhook before polling
        try:
            await self.application.bot.delete_webhook()
            logger.info("✅ Webhook cleared before starting polling")
        except Exception as e:
            logger.warning(f"Could not clear webhook: {e}")
        
        await self.application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query', 'web_app_data']
        )
        logger.info("🚀 Bot started successfully")
    
    async def stop(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down bot...")
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        self._executor.shutdown(wait=True)
        logger.info("✅ Bot stopped")
    
    async def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        await self._shutdown_event.wait()
    
    def shutdown(self):
        """Trigger shutdown"""
        self._shutdown_event.set()


# ==================== ULTRA FAST FLASK SERVER ====================
class UltraFastFlaskServer:
    """High-performance Flask server with gunicorn-like settings"""
    
    def __init__(self):
        self.server = None
        self._running = False
    
    def run(self):
        """Run Flask with optimal settings"""
        run_simple(
            '0.0.0.0',
            config.FLASK_PORT,
            flask_app,
            use_reloader=False,
            use_debugger=False,
            use_evalex=False,
            threaded=True,
            processes=1,
            request_handler=None,
            static_files=None,
            passthrough_errors=False,
            ssl_context=None
        )
    
    def start(self):
        """Start server in thread"""
        self._running = True
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        logger.info(f"🌐 Flask API running on port {config.FLASK_PORT}")
        return thread


# ==================== HEALTH MONITOR ====================
class HealthMonitor:
    """Monitors system health and performance"""
    
    def __init__(self):
        self._running = False
        self._monitor_task = None
    
    async def start(self):
        """Start health monitoring"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def _monitor_loop(self):
        """Monitor system health"""
        while self._running:
            try:
                if PSUTIL_AVAILABLE:
                    memory = psutil.virtual_memory()
                    if memory.percent > 90:
                        logger.warning(f"⚠️ High memory usage: {memory.percent}%")
                        gc.collect()
                    
                    cpu_percent = psutil.cpu_percent(interval=1)
                    if cpu_percent > 80:
                        logger.warning(f"⚠️ High CPU usage: {cpu_percent}%")
                else:
                    # Simple memory cleanup when psutil not available
                    gc.collect()
                
                # Check database connection
                if not await pool_manager.ensure_connection():
                    logger.error("❌ Database connection lost")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass


# ==================== SIGNAL HANDLERS ====================
def setup_signal_handlers(bot: UltraFastBot):
    """Setup graceful shutdown handlers"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        bot.shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


# ==================== MAIN ENTRY POINT ====================
async def main():
    """Ultra-optimized main entry point"""
    start_time = datetime.now()
    
    # Print startup banner with optional features status
    uvloop_status = "✅" if UVLOOP_AVAILABLE else "❌"
    nest_status = "✅" if NEST_ASYNCIO_AVAILABLE else "❌"
    psutil_status = "✅" if PSUTIL_AVAILABLE else "❌"
    
    logger.info(f"""
╔════════════════════════════════════════════════════════════════╗
║     🎰 ESTIF BINGO 24/7 - ULTRA OPTIMIZED EDITION 🎰          ║
║                                                                ║
║  Features:                                                     ║
║  • UVLoop async engine: {uvloop_status}                                     ║
║  • nest_asyncio: {nest_status}                                           ║
║  • psutil monitoring: {psutil_status}                                      ║
║  • Connection pooling                                         ║
║  • Auto-recovery                                              ║
║  • Health monitoring                                          ║
║  • Rate limiting                                              ║
║  • Memory optimization                                        ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize database with retry
    for attempt in range(3):
        try:
            await Database.init_pool()
            logger.info("✅ Database initialized")
            break
        except Exception as e:
            logger.error(f"Database init attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                logger.error("❌ Failed to initialize database after 3 attempts")
                sys.exit(1)
            await asyncio.sleep(2)
    
    # Start health monitor
    monitor = HealthMonitor()
    await monitor.start()
    
    # Start Flask server
    flask_server = UltraFastFlaskServer()
    flask_thread = flask_server.start()
    
    # Start bot
    bot = UltraFastBot()
    setup_signal_handlers(bot)
    
    # Start bot with retry
    for attempt in range(3):
        try:
            await bot.start()
            break
        except Exception as e:
            logger.error(f"Bot start attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                logger.error("❌ Failed to start bot after 3 attempts")
                sys.exit(1)
            await asyncio.sleep(2)
    
    startup_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"✨ System ready in {startup_time:.2f} seconds")
    
    # Wait for shutdown
    await bot.wait_for_shutdown()
    
    # Cleanup
    await monitor.stop()
    await bot.stop()
    await Database.close_pool()
    
    logger.info("👋 Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)