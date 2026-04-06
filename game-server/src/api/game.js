// game-server/src/api/game.js

const express = require("express");
const router = express.Router();
const { config } = require("../config");
const { getCartelaGrid, isValidCartelaId, getCachedCartelasCount } = require("../game/cartela");
const gameState = require("../game/gameState");
const rewardPool = require("../game/rewardPool");
const db = require("../db/pool");

// ==================== PUBLIC GAME ENDPOINTS ====================

/**
 * Get cartela grid by ID
 * GET /api/cartela/:id
 */
router.get("/cartela/:id", (req, res) => {
    const id = parseInt(req.params.id);
    
    if (!isValidCartelaId(id)) {
        return res.status(400).json({ 
            success: false, 
            message: `Invalid cartela ID. Must be between 1 and ${config.TOTAL_CARTELAS}` 
        });
    }
    
    const grid = getCartelaGrid(id);
    res.json({
        success: true,
        cartelaId: id,
        grid: grid
    });
});

/**
 * Get global game statistics (public)
 * GET /api/global-stats
 */
router.get("/global-stats", (req, res) => {
    const totalCartelas = gameState.getTotalSelectedCartelasCount();
    const { totalBetAmount, winnerReward, adminCommission } = rewardPool.calculateRewardPool(
        totalCartelas,
        config.BET_AMOUNT,
        rewardPool.getWinPercentage()
    );
    
    res.json({
        success: true,
        totalSelectedCartelas: totalCartelas,
        totalBetAmount: totalBetAmount,
        winnerReward: winnerReward,
        adminCommission: adminCommission,
        winPercentage: rewardPool.getWinPercentage(),
        remainingCartelas: config.TOTAL_CARTELAS - totalCartelas,
        round: gameState.gameState.round,
        status: gameState.gameState.status,
        playersOnline: gameState.getTotalPlayersCount()
    });
});

/**
 * Get current round number
 * GET /api/current-round
 */
router.get("/current-round", (req, res) => {
    res.json({
        success: true,
        round: gameState.gameState.round,
        status: gameState.gameState.status,
        timer: gameState.gameState.timer
    });
});

/**
 * Get drawn numbers so far
 * GET /api/drawn-numbers
 */
router.get("/drawn-numbers", (req, res) => {
    res.json({
        success: true,
        drawnNumbers: gameState.gameState.drawnNumbers,
        count: gameState.gameState.drawnNumbers.length
    });
});

/**
 * Get recent winners (last 10 rounds)
 * GET /api/recent-winners
 */
router.get("/recent-winners", async (req, res) => {
    try {
        const rounds = await db.getGameRounds({ limit: 10 });
        const recentWinners = rounds.map(round => ({
            roundNumber: round.round_number,
            winners: round.winners,
            timestamp: round.timestamp,
            winnerReward: round.winner_reward
        }));
        
        res.json({
            success: true,
            winners: recentWinners
        });
    } catch (err) {
        console.error("Recent winners error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to fetch recent winners" 
        });
    }
});

/**
 * Get cartela status (available or taken)
 * GET /api/cartela-status/:id
 */
router.get("/cartela-status/:id", (req, res) => {
    const id = parseInt(req.params.id);
    
    if (!isValidCartelaId(id)) {
        return res.status(400).json({ 
            success: false, 
            message: "Invalid cartela ID" 
        });
    }
    
    const isAvailable = gameState.isCartelaAvailable(id);
    const owner = isAvailable ? null : gameState.getCartelaOwner(id);
    
    res.json({
        success: true,
        cartelaId: id,
        available: isAvailable,
        takenBy: owner ? owner.username : null,
        takenAt: owner ? owner.timestamp : null
    });
});

/**
 * Get all cartela statuses (paginated)
 * GET /api/cartelas-status?page=1&limit=50
 */
router.get("/cartelas-status", (req, res) => {
    const page = parseInt(req.query.page) || 1;
    const limit = Math.min(parseInt(req.query.limit) || 50, 100);
    const start = (page - 1) * limit;
    const end = start + limit;
    
    const allCartelas = [];
    for (let i = 1; i <= config.TOTAL_CARTELAS; i++) {
        allCartelas.push({
            cartelaId: i,
            available: gameState.isCartelaAvailable(i),
            takenBy: gameState.getCartelaOwner(i)?.username || null
        });
    }
    
    const paginatedCartelas = allCartelas.slice(start, end);
    
    res.json({
        success: true,
        cartelas: paginatedCartelas,
        page: page,
        limit: limit,
        total: config.TOTAL_CARTELAS,
        totalPages: Math.ceil(config.TOTAL_CARTELAS / limit)
    });
});

/**
 * Get server health status
 * GET /api/health
 */
router.get("/health", async (req, res) => {
    const dbHealthy = await db.healthCheck();
    
    res.json({
        success: true,
        status: "online",
        timestamp: new Date().toISOString(),
        game: {
            status: gameState.gameState.status,
            round: gameState.gameState.round,
            players: gameState.getTotalPlayersCount()
        },
        database: dbHealthy ? "connected" : "disconnected",
        cache: {
            cartelasCached: getCachedCartelasCount(),
            totalCartelas: config.TOTAL_CARTELAS
        }
    });
});

/**
 * Get server info (version, uptime, etc.)
 * GET /api/info
 */
router.get("/info", (req, res) => {
    const uptime = process.uptime();
    const uptimeFormatted = `${Math.floor(uptime / 86400)}d ${Math.floor((uptime % 86400) / 3600)}h ${Math.floor((uptime % 3600) / 60)}m ${Math.floor(uptime % 60)}s`;
    
    res.json({
        success: true,
        name: "Estif Bingo 24/7",
        version: "3.0.0",
        nodeVersion: process.version,
        environment: config.NODE_ENV,
        uptime: uptimeFormatted,
        uptimeSeconds: uptime,
        features: {
            maxCartelasPerPlayer: config.MAX_CARTELAS,
            betAmount: config.BET_AMOUNT,
            selectionTime: config.SELECTION_TIME,
            drawInterval: config.DRAW_INTERVAL,
            availableWinPercentages: config.WIN_PERCENTAGES
        }
    });
});

// ==================== EXPORTS ====================
module.exports = router;