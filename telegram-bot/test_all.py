#!/usr/bin/env python
# test_all.py - Complete test suite for Estif Bingo Bot

import sys
import asyncio
import importlib

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_imports():
    print_section("Testing Imports")
    modules = [
        'bot.config',
        'bot.db.database',
        'bot.handlers.start',
        'bot.handlers.register',
        'bot.handlers.deposit',
        'bot.handlers.cashout',
        'bot.handlers.transfer',
        'bot.handlers.balance',
        'bot.handlers.invite',
        'bot.handlers.contact',
        'bot.handlers.bingo_otp',
        'bot.handlers.admin_commands',
        'bot.handlers.game',
        'bot.keyboards.menu',
        'bot.keyboards.game_keyboards',
        'bot.texts.locales',
        'bot.texts.game_texts',
        'bot.texts.emojis',
        'bot.utils.otp',
        'bot.utils.logger',
        'bot.utils.security',
        'bot.api.game_api',
        'bot.api.webhooks',
    ]
    
    failed = []
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {e}")
            failed.append(module)
    
    return len(failed) == 0, failed

def test_config():
    print_section("Testing Configuration")
    try:
        from bot.config import config
        print(f"✅ BOT_TOKEN: {'Set' if config.BOT_TOKEN else 'Missing'}")
        print(f"✅ ADMIN_CHAT_ID: {config.ADMIN_CHAT_ID}")
        print(f"✅ FLASK_PORT: {config.FLASK_PORT}")
        print(f"✅ GAME_WEB_URL: {config.GAME_WEB_URL}")
        print(f"✅ Environment: {config.NODE_ENV}")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_optional_packages():
    print_section("Testing Optional Packages")
    
    packages = ['uvloop', 'nest_asyncio', 'psutil', 'fastapi', 'uvicorn']
    
    for package in packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} (installed)")
        except ImportError:
            print(f"⚠️ {package} (not installed - optional)")
    
    return True

async def test_database():
    print_section("Testing Database Connection")
    try:
        from bot.db.database import Database
        await Database.init_pool()
        print("✅ Database connected")
        
        async with Database._pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            print(f"✅ Query test: {result}")
        
        await Database.close_pool()
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    print("\n" + "🎰" * 30)
    print("   ESTIF BINGO 24/7 - LOCAL TEST SUITE")
    print("🎰" * 30)
    
    results = []
    
    # Run tests
    import_success, failed = test_imports()
    results.append(("Imports", import_success))
    
    config_success = test_config()
    results.append(("Configuration", config_success))
    
    test_optional_packages()
    
    # Database test (optional - requires DB connection)
    # db_success = asyncio.run(test_database())
    # results.append(("Database", db_success))
    
    print_section("Test Summary")
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    if import_success and config_success:
        print("\n🎉 All critical tests passed! Ready for deployment!")
    else:
        print("\n⚠️ Some tests failed. Please fix before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
