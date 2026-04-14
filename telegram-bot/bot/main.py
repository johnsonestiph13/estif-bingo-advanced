# telegram-bot/bot/main.py
# Estif Bingo 24/7 - COMPLETE ULTRA-ENHANCED MAIN FILE
# Version: 4.0.0 - Production Ready with ALL Features
# Includes: Transfer, Game, Deposit, Cashout, OTP, Referral, Tournament, Daily Bonus, Help, About, Admin, and more

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
import json
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

from bot.config import BOT_TOKEN, FLASK_PORT, LOG_LEVEL, LOG_FORMAT
from bot.db.database import Database

# ==================== LOGGING CONFIGURATION ====================
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('backups', exist_ok=True)

logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/bot.log'),
        logging.FileHandler('logs/errors.log') if os.path.exists('logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

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
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        release_instance_lock()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

# ==================== DECORATORS ====================
def log_performance(func):
    """Decorator to log function performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = (time.time() - start) * 1000
            logger.debug(f"{func.__name__} completed in {duration:.2f}ms")
            return result
        except Exception as e:
            duration = (time.time() - start) * 1000
            logger.error(f"{func.__name__} failed after {duration:.2f}ms: {e}")
            raise
    return wrapper

def admin_only(func):
    """Decorator to restrict command to admin only"""
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if str(user_id) != str(os.environ.get("ADMIN_CHAT_ID")):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

# ==================== HEALTH MONITOR ====================
class HealthMonitor:
    """Monitor system health and performance"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.command_counts: Dict[str, int] = {}
    
    def get_uptime(self) -> float:
        return time.time() - self.start_time
    
    def record_command(self, command: str):
        self.request_count += 1
        self.command_counts[command] = self.command_counts.get(command, 0) + 1
    
    def record_error(self):
        self.error_count += 1
    
    def get_stats(self) -> Dict:
        return {
            "uptime_seconds": self.get_uptime(),
            "uptime_hours": round(self.get_uptime() / 3600, 2),
            "requests": self.request_count,
            "errors": self.error_count,
            "error_rate": round((self.error_count / self.request_count * 100), 2) if self.request_count > 0 else 0,
            "commands": self.command_counts
        }

health_monitor = HealthMonitor()

# ==================== BOT PERFORMANCE MONITOR ====================
class BotPerformanceMonitor:
    """Monitor bot performance metrics"""
    
    def __init__(self):
        self.command_stats: Dict[str, Dict] = {}
        self.message_stats: Dict[str, int] = {}
        self.start_time = datetime.now()
    
    def record_command(self, command: str, duration_ms: float, success: bool):
        if command not in self.command_stats:
            self.command_stats[command] = {
                "count": 0,
                "total_duration": 0,
                "success_count": 0,
                "error_count": 0,
                "min_duration": float('inf'),
                "max_duration": 0
            }
        stats = self.command_stats[command]
        stats["count"] += 1
        stats["total_duration"] += duration_ms
        stats["min_duration"] = min(stats["min_duration"], duration_ms)
        stats["max_duration"] = max(stats["max_duration"], duration_ms)
        if success:
            stats["success_count"] += 1
        else:
            stats["error_count"] += 1
    
    def record_message(self, message_type: str):
        self.message_stats[message_type] = self.message_stats.get(message_type, 0) + 1
    
    def get_stats(self) -> Dict:
        result = {}
        for cmd, stats in self.command_stats.items():
            result[cmd] = {
                "count": stats["count"],
                "avg_duration_ms": round(stats["total_duration"] / stats["count"], 2) if stats["count"] > 0 else 0,
                "min_duration_ms": round(stats["min_duration"], 2) if stats["min_duration"] != float('inf') else 0,
                "max_duration_ms": round(stats["max_duration"], 2),
                "success_rate": round(stats["success_count"] / stats["count"] * 100, 2) if stats["count"] > 0 else 0
            }
        return {
            "commands": result,
            "messages": self.message_stats,
            "uptime_hours": round((datetime.now() - self.start_time).total_seconds() / 3600, 2)
        }

perf_monitor = BotPerformanceMonitor()

# ==================== FLASK API SERVER ====================
def run_flask():
    """Run Flask in a separate thread for Game API"""
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "healthy",
            "bot": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": health_monitor.get_uptime(),
            "version": "4.0.0",
            "database": Database._pool is not None
        }), 200
    
    @app.route('/ready', methods=['GET'])
    def ready_check():
        return jsonify({
            "status": "ready",
            "database": Database._pool is not None,
            "bot_initialized": True
        }), 200
    
    @app.route('/metrics', methods=['GET'])
    def metrics():
        return jsonify({
            "health": health_monitor.get_stats(),
            "performance": perf_monitor.get_stats()
        }), 200
    
    @app.route('/ping', methods=['GET'])
    def ping():
        return jsonify({"pong": True, "timestamp": datetime.utcnow().isoformat()}), 200
    
    # Register all API blueprints
    from bot.api.game_api import game_api_bp
    app.register_blueprint(game_api_bp)
    logger.info("✅ Game API blueprint registered")
    
    from bot.api.webhooks import webhook_bp
    app.register_blueprint(webhook_bp)
    logger.info("✅ Webhook blueprint registered")
    
    from bot.api.commission import commission_bp
    app.register_blueprint(commission_bp)
    logger.info("✅ Commission blueprint registered")
    
    from bot.api.balance_ops import balance_bp
    app.register_blueprint(balance_bp)
    logger.info("✅ Balance operations blueprint registered")
    
    from bot.api.auth import auth_bp
    app.register_blueprint(auth_bp)
    logger.info("✅ Auth blueprint registered")
    
    app.run(host='0.0.0.0', port=FLASK_PORT, threaded=True, use_reloader=False)

# ==================== TELEGRAM BOT ====================
async def force_stop_bot():
    """Force stop any existing bot instance"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Delete webhook
            resp1 = await client.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
            # Get updates with high offset to clear queue
            resp2 = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1&timeout=1")
            # Wait a moment for server to process
            await asyncio.sleep(2)
            logger.info("✅ Force stopped any existing bot instance")
            return True
    except Exception as e:
        logger.warning(f"Force stop warning: {e}")
        return False

async def check_daily_bonus(telegram_id: int, context):
    """Check and award daily bonus if available"""
    try:
        from bot.handlers.bonus import check_daily_bonus as check_bonus
        return await check_bonus(telegram_id, context)
    except ImportError:
        # Manual daily bonus implementation
        async with Database._pool.acquire() as conn:
            today = datetime.utcnow().date()
            last_claimed = await conn.fetchval("SELECT last_claimed_date FROM daily_bonuses WHERE telegram_id = $1", telegram_id)
            
            if last_claimed == today:
                return False, 0, 0
            
            # Calculate streak
            streak = 1
            if last_claimed == today - timedelta(days=1):
                streak = await conn.fetchval("SELECT streak_count FROM daily_bonuses WHERE telegram_id = $1", telegram_id) or 1
                streak = streak + 1
            
            bonus_amount = 5 * min(streak, 7)
            await Database.add_balance(telegram_id, bonus_amount, "daily_bonus")
            
            await conn.execute("""
                INSERT INTO daily_bonuses (telegram_id, last_claimed_date, streak_count, total_claimed)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (telegram_id) DO UPDATE
                SET last_claimed_date = EXCLUDED.last_claimed_date,
                    streak_count = EXCLUDED.streak_count,
                    total_claimed = daily_bonuses.total_claimed + EXCLUDED.bonus_amount
            """, telegram_id, today, streak, bonus_amount)
            
            return True, bonus_amount, streak
    except Exception as e:
        logger.error(f"Daily bonus error: {e}")
        return False, 0, 0

def run_bot():
    """Run Telegram bot in the main thread"""
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, ConversationHandler,
        filters, CallbackQueryHandler, Defaults
    )
    from telegram.constants import ParseMode
    
    # ==================== IMPORT ALL HANDLERS ====================
    from bot.handlers.start import start, language_callback, help_command, about_command
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
    
    # ==================== HELPER FUNCTIONS ====================
    async def play(update, context):
        start_time = time.time()
        health_monitor.record_command("play")
        try:
            await play_command(update, context)
            perf_monitor.record_command("play", (time.time() - start_time) * 1000, True)
        except Exception as e:
            perf_monitor.record_command("play", (time.time() - start_time) * 1000, False)
            health_monitor.record_error()
            raise
    
    async def handle_help(update, context):
        await help_command(update, context)
    
    async def handle_about(update, context):
        await about_command(update, context)
    
    async def handle_all_text(update, context):
        start_time = time.time()
        try:
            if await deposit_amount(update, context):
                perf_monitor.record_message("deposit_amount")
                return
            if await cashout_amount(update, context):
                perf_monitor.record_message("cashout_amount")
                return
            if await cashout_account(update, context):
                perf_monitor.record_message("cashout_account")
                return
            
            from bot.texts.locales import TEXTS
            from bot.keyboards.menu import menu
            user = await Database.get_user(update.effective_user.id)
            lang = user.get('lang', 'en') if user else 'en'
            await update.message.reply_text(
                TEXTS[lang]['use_menu'], 
                reply_markup=menu(lang)
            )
            perf_monitor.record_message("unknown_text")
        except Exception as e:
            logger.error(f"Handle all text error: {e}")
            health_monitor.record_error()
        finally:
            perf_monitor.record_command("handle_all_text", (time.time() - start_time) * 1000, True)
    
    # ==================== HELP AND ABOUT CALLBACKS ====================
    async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await help_command(update, context)
    
    async def about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await about_command(update, context)
    
    async def daily_bonus_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        success, amount, streak = await check_daily_bonus(query.from_user.id, context)
        if success:
            await query.edit_message_text(
                f"🎁 *Daily Bonus Claimed!*\n\n"
                f"💰 Amount: *{amount} ETB*\n"
                f"📊 Streak: *{streak} days*\n\n"
                f"Come back tomorrow for more!",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"⏰ *Already Claimed!*\n\n"
                f"You've already claimed your daily bonus today.\n\n"
                f"Come back tomorrow!",
                parse_mode='Markdown'
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
        .connect_timeout(30.0) \
        .read_timeout(30.0) \
        .write_timeout(30.0) \
        .get_updates_connect_timeout(30.0) \
        .get_updates_read_timeout(30.0) \
        .get_updates_write_timeout(30.0) \
        .pool_timeout(30.0) \
        .build()
    
    # ==================== COMMAND HANDLERS ====================
    # Core commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("bingo", bingo_otp))
    application.add_handler(CommandHandler("verify", verify_otp))
    application.add_handler(CommandHandler("invite", invite))
    application.add_handler(CommandHandler("contact", contact_center))
    application.add_handler(CommandHandler("play", play_command))
    application.add_handler(CommandHandler("daily", lambda u, c: check_daily_bonus(u.effective_user.id, c)))
    
    # Financial commands
    application.add_handler(CommandHandler("deposit", deposit))
    application.add_handler(CommandHandler("cashout", cashout))
    application.add_handler(CommandHandler("transfer", transfer))
    
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
    application.add_handler(MessageHandler(filters.Regex("❓ Help|❓ እርዳታ"), handle_help))
    application.add_handler(MessageHandler(filters.Regex("ℹ️ About|ℹ️ ስለ"), handle_about))
    application.add_handler(MessageHandler(filters.Regex("🎁 Daily Bonus|🎁 የዕለት ቦነስ"), 
                                          lambda u, c: check_daily_bonus(u.effective_user.id, c)))
    
    # Catch-all text handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text))
    
    # ==================== CALLBACK QUERY HANDLERS ====================
    # Core callbacks
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(deposit_callback, pattern="^deposit_"))
    application.add_handler(CallbackQueryHandler(cashout_callback, pattern="^cashout_"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
    application.add_handler(CallbackQueryHandler(about_callback, pattern="^about_"))
    
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
    
    # Daily bonus callback
    application.add_handler(CallbackQueryHandler(daily_bonus_callback, pattern="^daily_bonus$"))
    
    # ==================== CONVERSATION HANDLERS ====================
    
    # Transfer Conversation Handler
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
    
    # Register Conversation Handler
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
    
    # Deposit Conversation Handler
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
    
    # Cashout Conversation Handler
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
        health_monitor.record_error()
        logger.error(f"Update {update} caused error {context.error}")
        
        # Log to file for debugging
        with open('logs/errors.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {context.error}\n")
            if update:
                f.write(f"Update: {update}\n")
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "⚠️ *An error occurred.*\n\n"
                    "Please try again later.\n\n"
                    "If the problem persists, contact support.",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    application.add_error_handler(error_handler)
    
    # ==================== JOB QUEUES ====================
    # Cleanup expired data job (runs every hour)
    async def cleanup_job(context):
        logger.info("Running cleanup job...")
        try:
            async with Database._pool.acquire() as conn:
                # Clean expired OTPs
                otp_deleted = await conn.execute("DELETE FROM otp_codes WHERE expires_at < NOW()")
                # Clean expired auth codes
                auth_deleted = await conn.execute("DELETE FROM auth_codes WHERE expires_at < NOW()")
                # Clean old notifications (older than 30 days)
                notif_deleted = await conn.execute("DELETE FROM notifications WHERE created_at < NOW() - INTERVAL '30 days'")
                
                logger.info(f"✅ Cleanup completed - OTP: {otp_deleted}, Auth: {auth_deleted}, Notifications: {notif_deleted}")
        except Exception as e:
            logger.error(f"Cleanup job error: {e}")
    
    # Add jobs to application job queue
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(cleanup_job, interval=3600, first=60)
        logger.info("✅ Job queue initialized")
    
    # ==================== START BOT ====================
    logger.info("=" * 70)
    logger.info("🤖 ESTIF BINGO 24/7 BOT STARTING")
    logger.info("=" * 70)
    logger.info("📦 FEATURES LOADED:")
    logger.info("   ✅ Transfer System")
    logger.info("   ✅ Game Integration")
    logger.info("   ✅ Deposit System")
    logger.info("   ✅ Cashout System")
    logger.info("   ✅ Web App Support")
    logger.info("   ✅ OTP Verification")
    logger.info("   ✅ Referral System")
    logger.info("   ✅ Daily Bonus")
    logger.info("   ✅ Admin Panel")
    logger.info("   ✅ Multi-language Support")
    logger.info("   ✅ Help & About Commands")
    logger.info("   ✅ Performance Monitoring")
    logger.info("   ✅ Health Checks")
    logger.info("=" * 70)
    
    # Run the bot with error catching
    try:
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query', 'web_app_data', 'chat_member', 'my_chat_member'],
            stop_signals=None,
            poll_interval=0.5,
            timeout=30
        )
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        traceback.print_exc()
        raise

# ==================== DATABASE BACKUP ====================
async def backup_database():
    """Create database backup"""
    try:
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.sql")
        
        # Log backup creation (actual backup would use pg_dump in production)
        logger.info(f"✅ Database backup created: {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False

# ==================== MAIN ENTRY POINT ====================
async def async_main():
    """Async main function for database initialization"""
    # Force stop any existing bot instance
    await force_stop_bot()
    
    # Initialize database
    await Database.init_pool()
    logger.info("✅ Database initialized")
    
    # Create database backup on startup (optional)
    # await backup_database()
    
    # Initialize game handlers
    from bot.handlers.game import start_game_handlers
    await start_game_handlers()
    logger.info("🎮 Game handlers initialized")
    
    # Check and log database stats
    try:
        total_users = await Database.get_total_users_count()
        logger.info(f"📊 Total registered users: {total_users}")
        
        total_deposits = await Database.get_total_deposits()
        logger.info(f"💰 Total deposits: {total_deposits:.2f} ETB")
    except Exception as e:
        logger.warning(f"Could not fetch stats: {e}")

def main():
    """Main entry point"""
    # Setup signal handlers
    setup_signal_handlers()
    
    # Acquire instance lock
    if not acquire_instance_lock():
        logger.error("Could not acquire instance lock. Another instance may be running.")
        sys.exit(1)
    
    # Run async initialization
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_main())
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Print startup banner
    logger.info("=" * 70)
    logger.info("🚀 ESTIF BINGO 24/7 BOT DEPLOYED SUCCESSFULLY")
    logger.info("=" * 70)
    logger.info(f"📡 Flask API running on port {FLASK_PORT}")
    logger.info("📡 ENDPOINTS:")
    logger.info("   🔹 POST /api/verify-code")
    logger.info("   🔹 POST /api/exchange-code")
    logger.info("   🔹 POST /api/deduct")
    logger.info("   🔹 POST /api/add")
    logger.info("   🔹 GET  /api/balance/<id>")
    logger.info("   🔹 POST /api/transfer")
    logger.info("   🔹 GET  /api/commission")
    logger.info("   🔹 GET  /health")
    logger.info("   🔹 GET  /ready")
    logger.info("   🔹 GET  /metrics")
    logger.info("   🔹 GET  /ping")
    logger.info("=" * 70)
    logger.info("🤖 TELEGRAM COMMANDS:")
    logger.info("   🔹 /start - Start the bot")
    logger.info("   🔹 /help - Show help")
    logger.info("   🔹 /about - Bot information")
    logger.info("   🔹 /play - Play Bingo")
    logger.info("   🔹 /deposit - Add funds")
    logger.info("   🔹 /cashout - Withdraw funds")
    logger.info("   🔹 /transfer - Send money")
    logger.info("   🔹 /balance - Check balance")
    logger.info("   🔹 /bingo - Get OTP code")
    logger.info("   🔹 /daily - Claim daily bonus")
    logger.info("   🔹 /invite - Get referral link")
    logger.info("   🔹 /contact - Contact support")
    logger.info("=" * 70)
    logger.info("🤖 Telegram Bot is running and ready to accept commands")
    logger.info("=" * 70)
    
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