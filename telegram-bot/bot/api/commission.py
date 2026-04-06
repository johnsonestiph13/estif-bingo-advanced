# api/commission.py
"""Commission/win percentage API endpoints"""

import logging
from flask import Blueprint, request, jsonify
from .auth import api_key_required
from ..db.database import Database
from ..config import ALLOWED_WIN_PERCENTAGES, DEFAULT_WIN_PERCENTAGE

logger = logging.getLogger(__name__)

# Create blueprint
commission_bp = Blueprint('commission', __name__)

@commission_bp.route('/api/commission', methods=['GET'])
@api_key_required
async def get_commission():
    """Get current win percentage"""
    try:
        percentage = await Database.get_win_percentage()
        return jsonify({
            "success": True,
            "percentage": percentage,
            "available": ALLOWED_WIN_PERCENTAGES
        })
    except Exception as e:
        logger.exception("Get commission error")
        return jsonify({
            "success": False,
            "message": "Internal error",
            "percentage": DEFAULT_WIN_PERCENTAGE
        }), 500

@commission_bp.route('/api/commission', methods=['POST'])
@api_key_required
async def set_commission():
    """Set win percentage"""
    data = request.get_json()
    percentage = data.get('percentage')
    
    if percentage not in ALLOWED_WIN_PERCENTAGES:
        return jsonify({
            "success": False,
            "message": f"Invalid percentage. Allowed: {ALLOWED_WIN_PERCENTAGES}"
        }), 400
    
    try:
        await Database.set_win_percentage(percentage)
        
        # Log the change (optional - you can add a commission_logs table)
        logger.info(f"Win percentage changed to {percentage}% via API")
        
        return jsonify({
            "success": True,
            "message": f"Win percentage updated to {percentage}%",
            "percentage": percentage
        })
    except Exception as e:
        logger.exception("Set commission error")
        return jsonify({
            "success": False,
            "message": "Internal error"
        }), 500

@commission_bp.route('/api/commission/history', methods=['GET'])
@api_key_required
async def get_commission_history():
    """Get win percentage change history"""
    try:
        # This would require a commission_logs table
        # For now, return current only
        percentage = await Database.get_win_percentage()
        return jsonify({
            "success": True,
            "current": percentage,
            "history": []  # Add history if you have commission_logs table
        })
    except Exception as e:
        logger.exception("Get commission history error")
        return jsonify({
            "success": False,
            "message": "Internal error"
        }), 500