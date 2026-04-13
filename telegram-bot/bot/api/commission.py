# api/commission.py
"""Commission/win percentage API endpoints for game server
Estif Bingo 24/7 - Handles win percentage management
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from .auth import api_key_required
from ..db.database import Database
from ..config import WIN_PERCENTAGES, DEFAULT_WIN_PERCENTAGE

logger = logging.getLogger(__name__)

# Create blueprint
commission_bp = Blueprint('commission', __name__)


@commission_bp.route('/api/commission', methods=['GET'])
@api_key_required
async def get_commission():
    """Get current win percentage
    
    Returns:
        {
            "success": true,
            "percentage": 80,
            "available": [70, 75, 76, 80],
            "default": 75
        }
    """
    try:
        percentage = await Database.get_win_percentage()
        return jsonify({
            "success": True,
            "percentage": percentage,
            "available": WIN_PERCENTAGES,
            "default": DEFAULT_WIN_PERCENTAGE
        })
    except Exception as e:
        logger.exception("Get commission error")
        return jsonify({
            "success": False,
            "message": "Internal error",
            "percentage": DEFAULT_WIN_PERCENTAGE,
            "available": WIN_PERCENTAGES
        }), 500


@commission_bp.route('/api/commission', methods=['POST'])
@api_key_required
async def set_commission():
    """Set win percentage
    
    Expected JSON body:
        {
            "percentage": 80
        }
    
    Returns:
        {
            "success": true,
            "message": "Win percentage updated to 80%",
            "percentage": 80,
            "previous": 75
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request body"
            }), 400
        
        percentage = data.get('percentage')
        
        if percentage is None:
            return jsonify({
                "success": False,
                "message": "Missing percentage field"
            }), 400
        
        if percentage not in WIN_PERCENTAGES:
            return jsonify({
                "success": False,
                "message": f"Invalid percentage. Allowed values: {WIN_PERCENTAGES}"
            }), 400
        
        # Get previous percentage for response
        previous = await Database.get_win_percentage()
        
        # Update percentage
        await Database.set_win_percentage(percentage)
        
        # Log the change
        logger.info(f"💰 Win percentage changed from {previous}% to {percentage}% via API")
        
        # Record in commission history (if you have commission_logs table)
        try:
            await Database.log_commission_change(previous, percentage, "API")
        except Exception as log_err:
            logger.warning(f"Could not log commission change: {log_err}")
        
        return jsonify({
            "success": True,
            "message": f"Win percentage updated to {percentage}%",
            "percentage": percentage,
            "previous": previous
        })
        
    except Exception as e:
        logger.exception("Set commission error")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500


@commission_bp.route('/api/commission/history', methods=['GET'])
@api_key_required
async def get_commission_history():
    """Get win percentage change history
    
    Query params:
        - limit: Number of records (default: 50)
        - offset: Pagination offset (default: 0)
    
    Returns:
        {
            "success": true,
            "current": 80,
            "history": [
                {
                    "id": 1,
                    "old_percentage": 75,
                    "new_percentage": 80,
                    "changed_by": "admin@estif.com",
                    "changed_at": "2024-01-01T00:00:00"
                }
            ]
        }
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        current = await Database.get_win_percentage()
        
        # Try to get history from commission_logs table
        try:
            history = await Database.get_commission_history(limit, offset)
        except Exception:
            # If table doesn't exist, return empty history
            history = []
        
        return jsonify({
            "success": True,
            "current": current,
            "history": history,
            "count": len(history)
        })
        
    except Exception as e:
        logger.exception("Get commission history error")
        return jsonify({
            "success": False,
            "message": "Internal error"
        }), 500


@commission_bp.route('/api/commission/stats', methods=['GET'])
@api_key_required
async def get_commission_stats():
    """Get commission statistics
    
    Returns:
        {
            "success": true,
            "total_commission": 12500.50,
            "average_win_percentage": 75.5,
            "current": 80,
            "changes_count": 5,
            "last_change": "2024-01-01T00:00:00"
        }
    """
    try:
        current = await Database.get_win_percentage()
        
        # Get statistics from database
        try:
            stats = await Database.get_commission_stats()
        except Exception:
            stats = {
                "total_commission": 0,
                "average_win_percentage": current,
                "changes_count": 0,
                "last_change": None
            }
        
        return jsonify({
            "success": True,
            "current": current,
            "total_commission": stats.get('total_commission', 0),
            "average_win_percentage": stats.get('average_win_percentage', current),
            "changes_count": stats.get('changes_count', 0),
            "last_change": stats.get('last_change')
        })
        
    except Exception as e:
        logger.exception("Get commission stats error")
        return jsonify({
            "success": False,
            "message": "Internal error"
        }), 500


@commission_bp.route('/api/commission/calculate', methods=['POST'])
@api_key_required
async def calculate_commission():
    """Calculate commission for a given amount
    
    Expected JSON body:
        {
            "total_bet": 1000,
            "win_percentage": 80
        }
    
    Returns:
        {
            "success": true,
            "total_bet": 1000,
            "winner_reward": 800,
            "commission": 200,
            "win_percentage": 80
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request body"
            }), 400
        
        total_bet = data.get('total_bet')
        win_percentage = data.get('win_percentage')
        
        if total_bet is None:
            return jsonify({
                "success": False,
                "message": "Missing total_bet field"
            }), 400
        
        if win_percentage is None:
            win_percentage = await Database.get_win_percentage()
        
        if win_percentage not in WIN_PERCENTAGES:
            return jsonify({
                "success": False,
                "message": f"Invalid win_percentage. Allowed: {WIN_PERCENTAGES}"
            }), 400
        
        winner_reward = (total_bet * win_percentage) / 100
        commission = total_bet - winner_reward
        
        return jsonify({
            "success": True,
            "total_bet": total_bet,
            "winner_reward": winner_reward,
            "commission": commission,
            "win_percentage": win_percentage,
            "house_edge": 100 - win_percentage
        })
        
    except Exception as e:
        logger.exception("Calculate commission error")
        return jsonify({
            "success": False,
            "message": "Internal error"
        }), 500


# ==================== ADD THESE METHODS TO DATABASE.PY ====================
# 
# @classmethod
# async def log_commission_change(cls, old_percentage: int, new_percentage: int, changed_by: str = "API"):
#     """Log commission change to database"""
#     async with cls._pool.acquire() as conn:
#         await conn.execute("""
#             INSERT INTO commission_logs (old_percentage, new_percentage, changed_by, changed_at)
#             VALUES ($1, $2, $3, NOW())
#         """, old_percentage, new_percentage, changed_by)
# 
# @classmethod
# async def get_commission_history(cls, limit: int = 50, offset: int = 0):
#     """Get commission change history"""
#     async with cls._pool.acquire() as conn:
#         rows = await conn.fetch("""
#             SELECT id, old_percentage, new_percentage, changed_by, changed_at
#             FROM commission_logs
#             ORDER BY changed_at DESC
#             LIMIT $1 OFFSET $2
#         """, limit, offset)
#         return [dict(r) for r in rows]
# 
# @classmethod
# async def get_commission_stats(cls):
#     """Get commission statistics"""
#     async with cls._pool.acquire() as conn:
#         # Get total commission from game_rounds
#         total = await conn.fetchval("SELECT COALESCE(SUM(admin_commission), 0) FROM game_rounds")
#         
#         # Get average win percentage
#         avg = await conn.fetchval("SELECT COALESCE(AVG(win_percentage), 0) FROM game_rounds")
#         
#         # Get number of changes
#         changes = await conn.fetchval("SELECT COUNT(*) FROM commission_logs")
#         
#         # Get last change time
#         last = await conn.fetchval("SELECT MAX(changed_at) FROM commission_logs")
#         
#         return {
#             "total_commission": float(total) if total else 0,
#             "average_win_percentage": float(avg) if avg else 0,
#             "changes_count": changes or 0,
#             "last_change": last.isoformat() if last else None
#         }


@commission_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({"success": False, "message": "Unauthorized"}), 401


@commission_bp.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Endpoint not found"}), 404


@commission_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"success": False, "message": "Internal server error"}), 500