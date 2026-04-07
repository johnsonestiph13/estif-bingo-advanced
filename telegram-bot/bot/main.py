# REMOVE THIS ❌
# async def main():
#     ...

# ADD THIS ✅
def main():
    try:
        import asyncio

        # Initialize DB first
        asyncio.run(Database.init_pool())
        logger.info("Database initialized")

        # Start Flask in background
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info(f"Flask API starting on port {FLASK_PORT}")

        # Create bot
        application = Application.builder().token(BOT_TOKEN).build()

        # ================= HANDLERS =================

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

        # ✅ IMPORTANT FIX HERE
        application.run_polling()

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)