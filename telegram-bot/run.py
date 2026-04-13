# run.py - ULTRA OPTIMIZED PRODUCTION READY
# Estif Bingo 24/7 - High-Performance Bot & API Launcher

import asyncio
import threading
import signal
import sys
import os
import gc
import psutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional
import logging
from logging.handlers import RotatingFileHandler
import uvloop
from flask import Flask, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
import nest_asyncio

# Apply ultra-fast asyncio event loop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
nest_asyncio.apply()

from bot.api.game_api import game_api_bp
from bot.api.webhooks import webhook_bp
from bot.config import Config
from bot.db.database import database

# ==================== ULTRA OPTIMIZED LOGGING ====================
class PerformanceLogger:
    """High-performance async logging with rotation"""
    def __init__(self):
        self.logger = logging.getLogger('bingo')
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
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
            MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # 10MB max
        )

flask_app = UltraFastFlask(__name__)

# Add health check endpoint
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
            if not database._pool:
                await database.init_pool()
                logger.info("🔄 Database pool reinitialized")
            elif not await database.health_check():
                await database.close_pool()
                await database.init_pool()
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
        self._request_semaphore = asyncio.Semaphore(100)  # Limit concurrent requests
        
    async def rate_limit(self, func, *args, **kwargs):
        """Apply rate limiting to handlers"""
        async with self._request_semaphore:
            return await func(*args, **kwargs)
    
    async def build_application(self):
        """Build bot application with optimizations"""
        from telegram.ext import (
            ApplicationBuilder, CommandHandler, CallbackQueryHandler,
            MessageHandler, filters, Defaults
        )
        from telegram.constants import ParseMode
        from bot.handlers import (
            start, register, deposit, cashout, balance, 
            invite, contact, admin_commands
        )
        from bot.handlers.game import play_command, game_callback
        
        # Optimized defaults
        defaults = Defaults(
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            disable_notification=False,
            protect_content=False
        )
        
        # Build with connection pool
        self.application = ApplicationBuilder() \
            .token(Config.BOT_TOKEN) \
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
        
        # Add handlers with error handling
        handlers = [
            CommandHandler("start", start.start_command),
            CommandHandler("register", register.register_command),
            CommandHandler("deposit", deposit.deposit_command),
            CommandHandler("cashout", cashout.cashout_command),
            CommandHandler("balance", balance.balance_command),
            CommandHandler("invite", invite.invite_command),
            CommandHandler("play", play_command),
            CommandHandler("help", contact.help_command),
            CommandHandler("admin", admin_commands.admin_panel),
            CommandHandler("setwin", admin_commands.set_win_percentage),
            CommandHandler("stats", admin_commands.stats_command),
            CallbackQueryHandler(deposit.deposit_callback, pattern="deposit"),
            CallbackQueryHandler(cashout.cashout_callback, pattern="cashout"),
            CallbackQueryHandler(admin_commands.admin_callback, pattern="admin"),
            MessageHandler(filters.StatusUpdate.WEB_APP_DATA, game_callback),
        ]
        
        for handler in handlers:
            self.application.add_handler(handler)
        
        # Add error handler
        self.application.add_error_handler(self._error_handler)
        
        return self.application
    
    async def _error_handler(self, update, context):
        """Global error handler"""
        logger.error(f"Bot error: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ An error occurred. Please try again later."
            )
    
    async def start(self):
        """Start bot with optimizations"""
        await self.build_application()
        await self.application.initialize()
        await self.application.start()
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
        from werkzeug.serving import run_simple
        
        # Production settings
        threaded = True
        processes = min(os.cpu_count() or 4, 4)  # Max 4 processes
        
        run_simple(
            '0.0.0.0',
            Config.FLASK_PORT,
            flask_app,
            use_reloader=False,
            use_debugger=False,
            use_evalex=False,
            threaded=threaded,
            processes=processes if not threaded else 1,
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
        logger.info(f"🌐 Flask API running on port {Config.FLASK_PORT} (threaded={True})")
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
                # Check memory usage
                memory = psutil.virtual_memory()
                if memory.percent > 90:
                    logger.warning(f"⚠️ High memory usage: {memory.percent}%")
                    gc.collect()
                
                # Check database connection
                if not await pool_manager.ensure_connection():
                    logger.error("❌ Database connection lost")
                
                # Check CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > 80:
                    logger.warning(f"⚠️ High CPU usage: {cpu_percent}%")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
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
    
    logger.info("""
╔════════════════════════════════════════════════════════════════╗
║     🎰 ESTIF BINGO 24/7 - ULTRA OPTIMIZED EDITION 🎰          ║
║                                                                ║
║  Features:                                                     ║
║  • UVLoop async engine                                        ║
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
            await database.init_pool()
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
    await database.close_pool()
    
    logger.info("👋 Goodbye!")

if __name__ == "__main__":
    # Install uvloop if not already
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass
    
    # Run main with optimal settings
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)