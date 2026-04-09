"""
Estif Bingo 24/7 - Game API Endpoints for Telegram Bot
Handles all game-related API calls from the Node.js game server
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import jwt
import hashlib
import random
import string
import os
from functools import wraps

# Import database and config
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import database
from config import Config

# Create blueprint
game_api_bp = Blueprint('game_api', __name__)

# ==================== AUTHENTICATION DECORATOR ====================

def verify_api_key(f):
    """Decorator to verify API key for bot-to-server calls"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != Config.API_SECRET:
            return jsonify({'error': 'Unauthorized: Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ==================== AUTHENTICATION ENDPOINTS ====================

@game_api_bp.route('/api/verify-code', methods=['POST'])
@verify_api_key
async def verify_code():
    """Verify one-time code and return user data"""
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'success': False, 'error': 'Code required'}), 400
    
    telegram_id = await database.verify_auth_code(code)
    
    if telegram_id:
        user = await database.get_user(telegram_id)
        if user:
            return jsonify({
                'success': True,
                'telegram_id': telegram_id,
                'username': user['username'],
                'balance': float(user['balance'])
            })
    
    return jsonify({'success': False, 'error': 'Invalid or expired code'}), 401

@game_api_bp.route('/api/exchange-code', methods=['POST'])
@verify_api_key
async def exchange_code():
    """Exchange one-time code for JWT token (called by game server)"""
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'success': False, 'error': 'Code required'}), 400
    
    telegram_id = await database.verify_auth_code(code)
    
    if telegram_id:
        user = await database.get_user(telegram_id)
        if user:
            # Generate JWT token for game server
            token = jwt.encode({
                'telegram_id': telegram_id,
                'username': user['username'],
                'balance': float(user['balance']),
                'exp': datetime.utcnow() + timedelta(hours=2)
            }, Config.JWT_SECRET, algorithm='HS256')
            
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'telegram_id': telegram_id,
                    'username': user['username'],
                    'balance': float(user['balance'])
                }
            })
    
    return jsonify({'success': False, 'error': 'Invalid or expired code'}), 401

@game_api_bp.route('/api/verify-token', methods=['POST'])
@verify_api_key
def verify_token():
    """Verify JWT token (called by game server WebSocket)"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'valid': False, 'message': 'Token required'}), 400
    
    try:
        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        return jsonify({
            'valid': True,
            'telegram_id': decoded['telegram_id'],
            'username': decoded['username'],
            'balance': decoded['balance']
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'message': 'Token expired'})
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'message': 'Invalid token'})

# ==================== BALANCE OPERATIONS ====================

@game_api_bp.route('/api/deduct', methods=['POST'])
@verify_api_key
async def deduct_balance():
    """Deduct balance for cartela purchase"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    amount = data.get('amount', Config.CARTELA_PRICE)
    cartela_id = data.get('cartela_id')
    round_num = data.get('round')
    reason = data.get('reason', 'Cartela selection')
    
    if not telegram_id:
        return jsonify({'success': False, 'error': 'telegram_id required'}), 400
    
    success = await database.update_balance(
        telegram_id,
        -amount,
        'cartela_purchase',
        round_num
    )
    
    if success:
        user = await database.get_user(telegram_id)
        return jsonify({
            'success': True,
            'new_balance': float(user['balance'])
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Insufficient balance'
        }), 400

@game_api_bp.route('/api/add', methods=['POST'])
@verify_api_key
async def add_balance():
    """Add winnings to user balance"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    amount = data.get('amount')
    round_id = data.get('round_id')
    reason = data.get('reason', 'Round win')
    
    if not telegram_id or not amount:
        return jsonify({'success': False, 'error': 'telegram_id and amount required'}), 400
    
    success = await database.update_balance(
        telegram_id,
        amount,
        'winning',
        round_id
    )
    
    if success:
        user = await database.get_user(telegram_id)
        return jsonify({
            'success': True,
            'new_balance': float(user['balance'])
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to add balance'}), 400

@game_api_bp.route('/api/balance/<int:telegram_id>', methods=['GET'])
@verify_api_key
async def get_balance(telegram_id):
    """Get user balance"""
    user = await database.get_user(telegram_id)
    if user:
        return jsonify({
            'success': True,
            'balance': float(user['balance']),
            'can_play': float(user['balance']) >= Config.MIN_BALANCE_FOR_PLAY
        })
    return jsonify({'success': False, 'error': 'User not found'}), 404

@game_api_bp.route('/api/balance', methods=['POST'])
@verify_api_key
async def get_balance_post():
    """Get user balance (POST method)"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    
    if not telegram_id:
        return jsonify({'success': False, 'error': 'telegram_id required'}), 400
    
    user = await database.get_user(telegram_id)
    if user:
        return jsonify({
            'success': True,
            'balance': float(user['balance']),
            'can_play': float(user['balance']) >= Config.MIN_BALANCE_FOR_PLAY
        })
    return jsonify({'success': False, 'error': 'User not found'}), 404

@game_api_bp.route('/api/adjust-balance', methods=['POST'])
@verify_api_key
async def adjust_balance():
    """Adjust user balance (admin action)"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    amount = data.get('amount')
    reason = data.get('reason', 'Admin adjustment')
    
    if not telegram_id or amount is None:
        return jsonify({'success': False, 'error': 'telegram_id and amount required'}), 400
    
    success = await database.update_balance(
        telegram_id,
        amount,
        'admin_adjustment',
        None
    )
    
    if success:
        user = await database.get_user(telegram_id)
        return jsonify({
            'success': True,
            'new_balance': float(user['balance']),
            'message': f'Balance adjusted by {amount} ETB'
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to adjust balance'}), 400

# ==================== COMMISSION / WIN PERCENTAGE ====================

@game_api_bp.route('/api/commission', methods=['GET'])
@verify_api_key
async def get_commission():
    """Get current win percentage"""
    percentage = await database.get_win_percentage()
    return jsonify({
        'success': True,
        'percentage': percentage
    })

@game_api_bp.route('/api/commission', methods=['POST'])
@verify_api_key
async def set_commission():
    """Set win percentage"""
    data = request.get_json()
    percentage = data.get('percentage')
    
    if percentage not in Config.WIN_PERCENTAGES:
        return jsonify({'success': False, 'error': f'Invalid percentage. Allowed: {Config.WIN_PERCENTAGES}'}), 400
    
    await database.set_win_percentage(percentage)
    
    return jsonify({
        'success': True,
        'message': f'Win percentage updated to {percentage}%',
        'percentage': percentage
    })

# ==================== USER MANAGEMENT ====================

@game_api_bp.route('/api/get-user/<int:telegram_id>', methods=['GET'])
@verify_api_key
async def get_user(telegram_id):
    """Get user details by Telegram ID"""
    user = await database.get_user(telegram_id)
    
    if user:
        # Convert to dict and handle Decimal
        user_dict = dict(user)
        if 'balance' in user_dict:
            user_dict['balance'] = float(user_dict['balance'])
        if 'total_deposited' in user_dict:
            user_dict['total_deposited'] = float(user_dict['total_deposited'])
        
        return jsonify({
            'success': True,
            'user': user_dict
        })
    
    return jsonify({'success': False, 'error': 'User not found'}), 404

@game_api_bp.route('/api/get-user', methods=['POST'])
@verify_api_key
async def get_user_post():
    """Get user details by Telegram ID (POST method)"""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    
    if not telegram_id:
        return jsonify({'success': False, 'error': 'telegram_id required'}), 400
    
    user = await database.get_user(telegram_id)
    
    if user:
        user_dict = dict(user)
        if 'balance' in user_dict:
            user_dict['balance'] = float(user_dict['balance'])
        if 'total_deposited' in user_dict:
            user_dict['total_deposited'] = float(user_dict['total_deposited'])
        
        return jsonify({
            'success': True,
            'user': user_dict
        })
    
    return jsonify({'success': False, 'error': 'User not found'}), 404

@game_api_bp.route('/api/search-players', methods=['POST'])
@verify_api_key
async def search_players():
    """Search players by username or phone"""
    data = request.get_json()
    search_term = data.get('search', '')
    
    if len(search_term) < 2:
        return jsonify({'success': False, 'error': 'Search term must be at least 2 characters'}), 400
    
    players = await database.search_players(search_term)
    
    # Convert Decimal to float for JSON serialization
    players_list = []
    for player in players:
        player_dict = dict(player)
        if 'balance' in player_dict:
            player_dict['balance'] = float(player_dict['balance'])
        if 'total_deposited' in player_dict:
            player_dict['total_deposited'] = float(player_dict['total_deposited'])
        players_list.append(player_dict)
    
    return jsonify({
        'success': True,
        'players': players_list
    })

@game_api_bp.route('/api/player-stats/<int:telegram_id>', methods=['GET'])
@verify_api_key
async def get_player_stats(telegram_id):
    """Get player statistics"""
    user = await database.get_user(telegram_id)
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    # Get transaction stats
    async with database.pool.acquire() as conn:
        # Total bets
        total_bets = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) FROM game_transactions 
            WHERE telegram_id = $1 AND type = 'bet'
        """, telegram_id)
        
        # Total wins
        total_wins = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0) FROM game_transactions 
            WHERE telegram_id = $1 AND type = 'win'
        """, telegram_id)
        
        # Games played
        games_played = await conn.fetchval("""
            SELECT COUNT(*) FROM game_transactions 
            WHERE telegram_id = $1 AND type = 'bet'
        """, telegram_id)
        
        # Games won
        games_won = await conn.fetchval("""
            SELECT COUNT(*) FROM game_transactions 
            WHERE telegram_id = $1 AND type = 'win'
        """, telegram_id)
    
    return jsonify({
        'success': True,
        'stats': {
            'total_bets': float(total_bets) if total_bets else 0,
            'total_wins': float(total_wins) if total_wins else 0,
            'games_played': games_played or 0,
            'games_won': games_won or 0,
            'net_result': float(total_wins or 0) - float(total_bets or 0),
            'win_rate': round((games_won or 0) / (games_played or 1) * 100, 2)
        }
    })

# ==================== ROUND MANAGEMENT ====================

@game_api_bp.route('/api/save-round', methods=['POST'])
@verify_api_key
async def save_round():
    """Save round result to database"""
    data = request.get_json()
    
    required_fields = ['round_id', 'pool_amount', 'win_percentage', 'winners', 'commission', 'total_payout']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
    
    async with database.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO game_rounds (round_number, total_pool, winner_reward, admin_commission, winners, win_percentage)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, data['round_id'], data['pool_amount'], data['total_payout'], 
            data['commission'], data['winners'], data['win_percentage'])
    
    return jsonify({'success': True})

# ==================== HEALTH CHECK ====================

@game_api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'telegram-bot-api'
    })

@game_api_bp.route('/api/bridge-health', methods=['GET'])
@verify_api_key
def bridge_health():
    """Health check for bot bridge"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

# ==================== ERROR HANDLERS ====================

@game_api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@game_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500