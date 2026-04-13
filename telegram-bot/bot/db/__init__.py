# telegram-bot/bot/db/__init__.py
# Estif Bingo 24/7 - Database Module Exports

from .database import Database, database

# Export the database instance and class for easy access
__all__ = [
    'Database',
    'database'
]