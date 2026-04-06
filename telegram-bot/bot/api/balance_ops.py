# api/balance_ops.py
"""Balance operations API endpoints for game server"""

import logging
from flask import Blueprint, request, jsonify
from .auth import api_key_required
from ..db.database import Database

logger = logging.getLogger(__name__)

# Create blueprint
balance_bp = Blueprint('balance', __name__)

@balance_bp.route('/api/deduct', methods=['POST'])
@api_key_required
async def deduct():
    """Deduct balance from user (called by game server)"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    amount = data.get('amount')
    reason = data.get('reason', '')
    
    if not telegram_id or not amount:
        return jsonify({"success": False, "message": "Missing fields"}), 400
    
    try:
        new_balance = await Database.deduct_balance(telegram_id, amount, reason)
        return jsonify({"success": True, "new_balance": new_balance})
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        logger.exception("Deduct error")
        return jsonify({"success": False, "message": "Internal error"}), 500

@balance_bp.route('/api/add', methods=['POST'])
@api_key_required
async def add():
    """Add balance to user (called by game server for wins)"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    amount = data.get('amount')
    reason = data.get('reason', '')
    
    if not telegram_id or not amount:
        return jsonify({"success": False, "message": "Missing fields"}), 400
    
    try:
        new_balance = await Database.add_balance(telegram_id, amount, reason)
        return jsonify({"success": True, "new_balance": new_balance})
        
    except Exception as e:
        logger.exception("Add error")
        return jsonify({"success": False, "message": "Internal error"}), 500

@balance_bp.route('/api/get-balance', methods=['POST'])
@api_key_required
async def get_balance():
    """Get user's current balance"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    
    if not telegram_id:
        return jsonify({"success": False, "message": "telegram_id required"}), 400
    
    try:
        balance = await Database.get_balance(telegram_id)
        return jsonify({"success": True, "balance": balance})
        
    except Exception as e:
        logger.exception("Get balance error")
        return jsonify({"success": False, "message": "Internal error"}), 500

@balance_bp.route('/api/batch-balance', methods=['POST'])
@api_key_required
async def batch_balance():
    """Process multiple balance operations in batch"""
    data = request.get_json()
    operations = data.get('operations', [])
    
    if not operations:
        return jsonify({"success": False, "message": "No operations provided"}), 400
    
    results = []
    for op in operations:
        try:
            if op.get('type') == 'add':
                new_balance = await Database.add_balance(
                    op['telegram_id'], op['amount'], op.get('reason', '')
                )
                results.append({
                    "telegram_id": op['telegram_id'],
                    "success": True,
                    "new_balance": new_balance
                })
            elif op.get('type') == 'deduct':
                new_balance = await Database.deduct_balance(
                    op['telegram_id'], op['amount'], op.get('reason', '')
                )
                results.append({
                    "telegram_id": op['telegram_id'],
                    "success": True,
                    "new_balance": new_balance
                })
            else:
                results.append({
                    "telegram_id": op['telegram_id'],
                    "success": False,
                    "error": f"Unknown operation type: {op.get('type')}"
                })
        except Exception as e:
            results.append({
                "telegram_id": op['telegram_id'],
                "success": False,
                "error": str(e)
            })
    
    return jsonify({"success": True, "results": results})