// game-server/src/api/botBridge.js
// Estif Bingo 24/7 - Bot Bridge API for Telegram Bot Communication

const express = require("express");
const router = express.Router();
const jwt = require("jsonwebtoken");
const { Pool } = require("pg");

// ==================== CONFIGURATION ====================
const config = {
    JWT_SECRET: process.env.JWT_SECRET,
    BOT_API_URL: process.env.BOT_API_URL,
    API_SECRET: process.env.API_SECRET,
    WIN_PERCENTAGES: [70, 75, 76, 80],
    BET_AMOUNT: 10
};

// Database connection
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === "production" ? { rejectUnauthorized: false } : false
});

// Game state reference (will be set from server.js)
let gameStateRef = null;
let rewardPoolRef = null;

// Helper function to call bot API
async function callBotAPI(endpoint, method = 'GET', body = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': config.API_SECRET
        }
    };
    if (body) options.body = JSON.stringify(body);
    
    try {
        const response = await fetch(`${config.BOT_API_URL}${endpoint}`, options);
        if (!response.ok) {
            throw new Error(`Bot API error: ${response.status}`);
        }
        return await response.json();
    } catch (err) {
        console.error(`Bot API call failed (${endpoint}):`, err.message);
        throw err;
    }
}

// ==================== MIDDLEWARE ====================

/**
 * Verify API Key middleware
 */
function verifyApiKey(req, res, next) {
    const apiKey = req.headers['x-api-key'];
    if (!apiKey || apiKey !== config.API_SECRET) {
        return res.status(401).json({ 
            success: false, 
            message: "Unauthorized: Invalid API key" 
        });
    }
    next();
}

/**
 * Generate JWT token for player
 */
function generatePlayerToken(telegramId, username, balance) {
    return jwt.sign(
        { 
            telegram_id: telegramId, 
            username: username, 
            balance: balance,
            timestamp: Date.now()
        },
        config.JWT_SECRET,
        { expiresIn: "2h" }
    );
}

// ==================== AUTHENTICATION ENDPOINTS ====================

/**
 * Exchange one-time code for JWT token
 * POST /api/exchange-code
 * Called by player.html after receiving code from bot
 */
router.post("/exchange-code", verifyApiKey, async (req, res) => {
    const { code } = req.body;
    
    if (!code) {
        return res.status(400).json({ 
            success: false, 
            error: "Code required" 
        });
    }
    
    try {
        // Verify code with bot API
        const result = await callBotAPI('/api/verify-code', 'POST', { code });
        
        if (!result.success || !result.telegram_id) {
            return res.status(401).json({ 
                success: false, 
                error: "Invalid or expired code" 
            });
        }
        
        // Generate game JWT
        const gameToken = generatePlayerToken(
            result.telegram_id, 
            result.username || "Player", 
            result.balance || 0
        );
        
        res.json({
            success: true,
            token: gameToken,
            user: {
                telegram_id: result.telegram_id,
                username: result.username || "Player",
                balance: result.balance || 0
            }
        });
    } catch (err) {
        console.error("Exchange code error:", err);
        res.status(500).json({ 
            success: false, 
            error: "Failed to exchange code" 
        });
    }
});

/**
 * Verify player token
 * POST /api/verify-token
 * Called by game server when player connects via WebSocket
 */
router.post("/verify-token", verifyApiKey, (req, res) => {
    const { token } = req.body;
    
    if (!token) {
        return res.status(400).json({ 
            valid: false, 
            message: "Token required" 
        });
    }
    
    try {
        const decoded = jwt.verify(token, config.JWT_SECRET);
        
        res.json({
            valid: true,
            telegram_id: decoded.telegram_id,
            username: decoded.username,
            balance: decoded.balance
        });
    } catch (err) {
        res.json({
            valid: false,
            message: err.name === "TokenExpiredError" ? "Token expired" : "Invalid token"
        });
    }
});

// ==================== BALANCE OPERATIONS ====================

/**
 * Deduct balance (player bought a cartela)
 * POST /api/deduct
 * Called by game server when player selects a cartela
 */
router.post("/deduct", verifyApiKey, async (req, res) => {
    const { telegram_id, amount, cartela_id, round } = req.body;
    
    if (!telegram_id) {
        return res.status(400).json({ 
            success: false, 
            error: "telegram_id required" 
        });
    }
    
    const deductAmount = amount || config.BET_AMOUNT;
    
    try {
        // Call bot API to deduct balance
        const result = await callBotAPI('/api/deduct', 'POST', {
            telegram_id: telegram_id,
            amount: deductAmount,
            cartela_id: cartela_id,
            round: round,
            reason: `Cartela ${cartela_id} selection round ${round}`
        });
        
        if (result.success) {
            // Log transaction locally
            await pool.query(`
                INSERT INTO game_transactions (telegram_id, type, amount, cartela, round, note)
                VALUES ($1, $2, $3, $4, $5, $6)
            `, [telegram_id, "bet", deductAmount, cartela_id, round, "Cartela selection"]);
        }
        
        res.json(result);
    } catch (err) {
        console.error("Deduct error:", err);
        res.status(500).json({ 
            success: false, 
            error: "Failed to deduct balance" 
        });
    }
});

/**
 * Add balance (player won a round)
 * POST /api/add
 * Called by game server when player wins
 */
router.post("/add", verifyApiKey, async (req, res) => {
    const { telegram_id, amount, round_id, reason } = req.body;
    
    if (!telegram_id || !amount) {
        return res.status(400).json({ 
            success: false, 
            error: "telegram_id and amount required" 
        });
    }
    
    try {
        // Call bot API to add balance
        const result = await callBotAPI('/api/add', 'POST', {
            telegram_id: telegram_id,
            amount: amount,
            round_id: round_id,
            reason: reason || `Won round ${round_id}`
        });
        
        if (result.success) {
            // Log transaction locally
            await pool.query(`
                INSERT INTO game_transactions (telegram_id, type, amount, round, note)
                VALUES ($1, $2, $3, $4, $5)
            `, [telegram_id, "win", amount, round_id, reason]);
        }
        
        res.json(result);
    } catch (err) {
        console.error("Add balance error:", err);
        res.status(500).json({ 
            success: false, 
            error: "Failed to add balance" 
        });
    }
});

/**
 * Get user balance
 * POST /api/balance
 * GET /api/balance/:telegramId
 * Called by game server to fetch user balance
 */
router.get("/balance/:telegramId", verifyApiKey, async (req, res) => {
    const { telegramId } = req.params;
    
    if (!telegramId) {
        return res.status(400).json({ 
            success: false, 
            error: "telegram_id required" 
        });
    }
    
    try {
        const result = await callBotAPI(`/api/balance/${telegramId}`, 'GET');
        res.json(result);
    } catch (err) {
        console.error("Get balance error:", err);
        res.status(500).json({ 
            success: false, 
            error: "Failed to fetch balance" 
        });
    }
});

router.post("/balance", verifyApiKey, async (req, res) => {
    const { telegram_id } = req.body;
    
    if (!telegram_id) {
        return res.status(400).json({ 
            success: false, 
            error: "telegram_id required" 
        });
    }
    
    try {
        const result = await callBotAPI(`/api/balance/${telegram_id}`, 'GET');
        res.json(result);
    } catch (err) {
        console.error("Get balance error:", err);
        res.status(500).json({ 
            success: false, 
            error: "Failed to fetch balance" 
        });
    }
});

// ==================== COMMISSION OPERATIONS ====================

/**
 * Get commission/win percentage
 * GET /api/commission
 * Called by game server to get current win percentage
 */
router.get("/commission", verifyApiKey, async (req, res) => {
    try {
        // Try to get from bot API first
        const result = await callBotAPI('/api/commission', 'GET');
        
        // Update local state if available
        if (rewardPoolRef && result.percentage) {
            rewardPoolRef.setWinPercentage(result.percentage);
        }
        
        res.json({
            success: true,
            percentage: result.percentage || 75
        });
    } catch (err) {
        console.error("Get commission error:", err);
        // Fallback to local state
        const percentage = rewardPoolRef?.getWinPercentage() || 75;
        res.json({
            success: true,
            percentage: percentage
        });
    }
});

/**
 * Set commission/win percentage
 * POST /api/commission
 * Called by game server when admin changes win percentage
 */
router.post("/commission", verifyApiKey, async (req, res) => {
    const { percentage } = req.body;
    
    if (!percentage || !config.WIN_PERCENTAGES.includes(percentage)) {
        return res.status(400).json({ 
            success: false, 
            error: `Invalid percentage. Allowed: ${config.WIN_PERCENTAGES.join(", ")}` 
        });
    }
    
    try {
        // Forward to bot API to persist the setting
        await callBotAPI('/api/commission', 'POST', { percentage });
        
        // Update in-memory state
        if (rewardPoolRef) {
            rewardPoolRef.setWinPercentage(percentage);
        }
        
        // Update game state
        if (gameStateRef) {
            gameStateRef.gameState.winPercentage = percentage;
        }
        
        res.json({
            success: true,
            message: `Win percentage updated to ${percentage}%`,
            percentage: percentage
        });
    } catch (err) {
        console.error("Set commission error:", err);
        // Still update local state even if bot persistence fails
        if (rewardPoolRef) {
            rewardPoolRef.setWinPercentage(percentage);
        }
        if (gameStateRef) {
            gameStateRef.gameState.winPercentage = percentage;
        }
        res.json({
            success: true,
            message: `Win percentage updated locally to ${percentage}%`,
            percentage: percentage,
            warning: "Bot persistence failed"
        });
    }
});

// ==================== PLAYER MANAGEMENT ====================

/**
 * Get user by Telegram ID
 * POST /api/get-user
 * GET /api/get-user/:telegramId
 */
router.get("/get-user/:telegramId", verifyApiKey, async (req, res) => {
    const { telegramId } = req.params;
    
    if (!telegramId) {
        return res.status(400).json({ 
            success: false, 
            error: "telegram_id required" 
        });
    }
    
    try {
        const result = await callBotAPI(`/api/get-user/${telegramId}`, 'GET');
        res.json(result);
    } catch (err) {
        console.error("Get user error:", err);
        res.status(500).json({ 
            success: false, 
            error: "Failed to fetch user" 
        });
    }
});

router.post("/get-user", verifyApiKey, async (req, res) => {
    const { telegram_id } = req.body;
    
    if (!telegram_id) {
        return res.status(400).json({ 
            success: false, 
            error: "telegram_id required" 
        });
    }
    
    try {
        const result = await callBotAPI(`/api/get-user/${telegram_id}`, 'GET');
        res.json(result);
    } catch (err) {
        console.error("Get user error:", err);
        res.status(500).json({ 
            success: false, 
            error: "Failed to fetch user" 
        });
    }
});

/**
 * Search players by username or phone
 * POST /api/search-players
 */
router.post("/search-players", verifyApiKey, async (req, res) => {
    const { search } = req.body;
    
    if (!search || search.length < 2) {
        return res.status(400).json({ 
            success: false, 
            error: "Search term must be at least 2 characters" 
        });
    }
    
    try {
        const result = await callBotAPI('/api/search-players', 'POST', { search });
        res.json(result);
    } catch (err) {
        console.error("Search players error:", err);
        res.status(500).json({ 
            success: false, 
            error: "Failed to search players" 
        });
    }
});

/**
 * Adjust player balance (admin only)
 * POST /api/adjust-balance
 */
router.post("/adjust-balance", verifyApiKey, async (req, res) => {
    const { telegram_id, amount, reason } = req.body;
    
    if (!telegram_id || amount === undefined) {
        return res.status(400).json({ 
            success: false, 
            error: "telegram_id and amount required" 
        });
    }
    
    try {
        const result = await callBotAPI('/api/adjust-balance', 'POST', {
            telegram_id,
            amount,
            reason: reason || "Admin adjustment"
        });
        
        // Update balance in game state if player is online
        if (result.success && gameStateRef?.players) {
            for (const player of gameStateRef.players.values()) {
                if (player.telegramId === telegram_id) {
                    player.balance = result.new_balance;
                    break;
                }
            }
        }
        
        res.json(result);
    } catch (err) {
        console.error("Adjust balance error:", err);
        res.status(500).json({ 
            success: false, 
            error: "Failed to adjust balance" 
        });
    }
});

// ==================== ROUND MANAGEMENT ====================

/**
 * Save round result
 * POST /api/save-round
 * Called by game server when round ends
 */
router.post("/save-round", verifyApiKey, async (req, res) => {
    const { 
        round_id, 
        pool_amount, 
        win_percentage, 
        winners, 
        commission, 
        total_payout 
    } = req.body;
    
    try {
        await pool.query(`
            INSERT INTO game_rounds (round_number, total_pool, winner_reward, admin_commission, winners, win_percentage, total_cartelas)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        `, [
            round_id, 
            pool_amount, 
            total_payout, 
            commission, 
            JSON.stringify(winners), 
            win_percentage,
            winners.length
        ]);
        
        res.json({ success: true });
    } catch (err) {
        console.error("Save round error:", err);
        res.status(500).json({ 
            success: false, 
            error: "Failed to save round" 
        });
    }
});

// ==================== HEALTH CHECK ====================

/**
 * Health check for bot bridge
 * GET /api/bridge-health
 */
router.get("/bridge-health", verifyApiKey, (req, res) => {
    res.json({
        success: true,
        status: "healthy",
        timestamp: new Date().toISOString(),
        botApiUrl: config.BOT_API_URL,
        gameStatus: gameStateRef?.gameState?.status || "unknown",
        gameRound: gameStateRef?.gameState?.round || 1,
        playersOnline: gameStateRef?.players?.size || 0,
        winPercentage: rewardPoolRef?.getWinPercentage() || 75
    });
});

/**
 * Simple ping endpoint
 * GET /api/ping
 */
router.get("/ping", verifyApiKey, (req, res) => {
    res.json({ 
        success: true, 
        pong: true, 
        timestamp: Date.now() 
    });
});

// ==================== INITIALIZATION ====================
function init(gameState, rewardPool) {
    gameStateRef = gameState;
    rewardPoolRef = rewardPool;
    console.log("✅ Bot Bridge initialized with game state");
}

// ==================== EXPORTS ====================
module.exports = router;
module.exports.init = init;
module.exports.verifyApiKey = verifyApiKey;
module.exports.generatePlayerToken = generatePlayerToken;