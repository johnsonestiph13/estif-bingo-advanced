# test_bot.py
import os
import sys

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        from bot.config import config
        print("✅ config imported")
    except Exception as e:
        print(f"❌ config failed: {e}")
        return False
    
    try:
        from bot.db.database import Database
        print("✅ database imported")
    except Exception as e:
        print(f"❌ database failed: {e}")
        return False
    
    try:
        from bot.handlers.start import start
        print("✅ handlers imported")
    except Exception as e:
        print(f"❌ handlers failed: {e}")
        return False
    
    try:
        from bot.keyboards.menu import menu
        print("✅ keyboards imported")
    except Exception as e:
        print(f"❌ keyboards failed: {e}")
        return False
    
    try:
        from bot.texts.locales import TEXTS
        print("✅ texts imported")
    except Exception as e:
        print(f"❌ texts failed: {e}")
        return False
    
    print("\n✅ All imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
