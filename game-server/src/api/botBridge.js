// game-server/src/api/botBridge.js

const express = require("express");
const router = express.Router();
const { config } = require("../config");
const { verifyApiKey } = require("../middleware/auth");
const { generatePlayerToken } = require("../middleware/auth");
const db = require("../db/pool");
const gameState = require("../game/gameState");
const rewardPool = require("../game/rewardPool");

// ==================== BOT API ENDPOINTS (Protected by API Key) ====================

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
            message: "Code required" 
        });
    }
    
    try {
        // Code should have been stored by bot and sent to player
        // This endpoint expects that the bot has already validated the code
        // and this is just a passthrough to get the JWT
        
        // For security, the bot should have called /api/verify-code first
        // Here we assume the code is valid and we have the user info
        
        // In production, you would verify the code with the bot API
        // For now, we'll accept a pre-validated token in the request
        
        const { token, telegram_id, username, balance } = req.body;
        
        if (!token || !telegram_id) {
            return res.status(400).json({ 
                success: false, 
                message: "Missing user data" 
            });
        }
        
        // Generate game JWT
        const gameToken = generatePlayerToken(telegram_id, username, balance);
        
        res.json({
            success: true,
            token: gameToken,
            telegram_id: telegram_id,
            username: username,
            balance: balance
        });
    } catch (err) {
        console.error("Exchange code error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to exchange code" 
        });
    }
});

/**
 * Verify player token (bot checking if token is valid)
 * POST /api/verify-token
 * Called by bot when player uses game link with token
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
        const jwt = require("jsonwebtoken");
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

/**
 * Deduct balance (player bought a cartela)
 * POST /api/deduct
 * Called by game server when player selects a cartela
 */
router.post("/deduct", verifyApiKey, async (req, res) => {
    const { telegram_id, amount, reason } = req.body;
    
    if (!telegram_id || !amount) {
        return res.status(400).json({ 
            success: false, 
            message: "telegram_id and amount required" 
        });
    }
    
    if (amount <= 0) {
        return res.status(400).json({ 
            success: false, 
            message: "Amount must be positive" 
        });
    }
    
    try {
        // Forward to bot API to deduct balance
        // This is a bridge - the actual deduction happens in the bot
        // The game server calls this endpoint, which then calls the bot
        
        const fetch = require("node-fetch");
        const response = await fetch(`${config.BOT_API_URL}/api/deduct`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": config.API_SECRET
            },
            body: JSON.stringify({ telegram_id, amount, reason })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Log transaction locally
            await db.logGameTransaction(
                telegram_id, 
                "system", 
                "bet", 
                amount, 
                null, 
                gameState.gameState.round, 
                reason
            );
        }
        
        res.json(data);
    } catch (err) {
        console.error("Deduct error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to deduct balance" 
        });
    }
});

/**
 * Add balance (player won a round)
 * POST /api/add
 * Called by game server when player wins
 */
router.post("/add", verifyApiKey, async (req, res) => {
    const { telegram_id, amount, reason } = req.body;
    
    if (!telegram_id || !amount) {
        return res.status(400).json({ 
            success: false, 
            message: "telegram_id and amount required" 
        });
    }
    
    if (amount <= 0) {
        return res.status(400).json({ 
            success: false, 
            message: "Amount must be positive" 
        });
    }
    
    try {
        // Forward to bot API to add balance
        const fetch = require("node-fetch");
        const response = await fetch(`${config.BOT_API_URL}/api/add`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": config.API_SECRET
            },
            body: JSON.stringify({ telegram_id, amount, reason })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Log transaction locally
            await db.logGameTransaction(
                telegram_id, 
                "system", 
                "win", 
                amount, 
                null, 
                gameState.gameState.round, 
                reason
            );
        }
        
        res.json(data);
    } catch (err) {
        console.error("Add balance error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to add balance" 
        });
    }
});

/**
 * Get commission/win percentage
 * GET /api/commission
 * Called by game server to get current win percentage
 */
router.get("/commission", verifyApiKey, async (req, res) => {
    try {
        const fetch = require("node-fetch");
        const response = await fetch(`${config.BOT_API_URL}/api/commission`, {
            headers: { "X-API-Key": config.API_SECRET }
        });
        const data = await response.json();
        
        res.json({
            success: true,
            percentage: data.percentage || rewardPool.getWinPercentage()
        });
    } catch (err) {
        console.error("Get commission error:", err);
        res.json({
            success: true,
            percentage: rewardPool.getWinPercentage()
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
    
    if (!rewardPool.isValidWinPercentage(percentage)) {
        return res.status(400).json({ 
            success: false, 
            message: `Invalid percentage. Allowed: ${config.WIN_PERCENTAGES.join(", ")}` 
        });
    }
    
    try {
        // Forward to bot API to persist the setting
        const fetch = require("node-fetch");
        await fetch(`${config.BOT_API_URL}/api/commission`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": config.API_SECRET
            },
            body: JSON.stringify({ percentage })
        });
        
        // Update in-memory state
        rewardPool.setWinPercentage(percentage);
        
        res.json({
            success: true,
            message: `Win percentage updated to ${percentage}%`,
            percentage: percentage
        });
    } catch (err) {
        console.error("Set commission error:", err);
        // Still update local state even if bot persistence fails
        rewardPool.setWinPercentage(percentage);
        res.json({
            success: true,
            message: `Win percentage updated locally to ${percentage}%`,
            percentage: percentage
        });
    }
});

/**
 * Get user balance
 * POST /api/get-balance
 * Called by game server to fetch user balance
 */
router.post("/get-balance", verifyApiKey, async (req, res) => {
    const { telegram_id } = req.body;
    
    if (!telegram_id) {
        return res.status(400).json({ 
            success: false, 
            message: "telegram_id required" 
        });
    }
    
    try {
        const fetch = require("node-fetch");
        const response = await fetch(`${config.BOT_API_URL}/api/get-balance`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": config.API_SECRET
            },
            body: JSON.stringify({ telegram_id })
        });
        
        const data = await response.json();
        res.json(data);
    } catch (err) {
        console.error("Get balance error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to fetch balance" 
        });
    }
});

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
        gameStatus: gameState.gameState.status,
        gameRound: gameState.gameState.round
    });
});

// ==================== EXPORTS ====================
module.exports = router;