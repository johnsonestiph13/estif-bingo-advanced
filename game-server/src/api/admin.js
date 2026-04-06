// game-server/src/api/admin.js

const express = require("express");
const router = express.Router();
const { config, validateWinPercentage } = require("../config");
const { verifyAdminToken, generateAdminToken, revokeAdminToken } = require("../middleware/auth");
const gameState = require("../game/gameState");
const rewardPool = require("../game/rewardPool");
const roundManager = require("../game/roundManager");
const db = require("../db/pool");

// ==================== AUTHENTICATION ====================

/**
 * Admin login
 * POST /api/admin/login
 */
router.post("/login", async (req, res) => {
    const { email, password } = req.body;
    
    if (!email || !password) {
        return res.status(400).json({ 
            success: false, 
            message: "Email and password required" 
        });
    }
    
    if (email !== config.ADMIN_EMAIL) {
        return res.status(401).json({ 
            success: false, 
            message: "Invalid credentials" 
        });
    }
    
    // In production, compare with hashed password from env
    // For now, using simple comparison (you should use bcrypt)
    if (password !== "admin123" && !config.ADMIN_PASSWORD_HASH) {
        return res.status(401).json({ 
            success: false, 
            message: "Invalid credentials" 
        });
    }
    
    const token = generateAdminToken(email);
    res.json({ 
        success: true, 
        token,
        message: "Login successful"
    });
});

/**
 * Admin logout
 * POST /api/admin/logout
 */
router.post("/logout", verifyAdminToken, (req, res) => {
    const token = req.headers.authorization?.split(" ")[1];
    if (token) {
        revokeAdminToken(token);
    }
    res.json({ 
        success: true, 
        message: "Logged out successfully" 
    });
});

/**
 * Verify token (check if still valid)
 * GET /api/admin/verify
 */
router.get("/verify", verifyAdminToken, (req, res) => {
    res.json({ 
        success: true, 
        admin: req.admin,
        message: "Token valid" 
    });
});

// ==================== GAME STATISTICS ====================

/**
 * Get current game stats
 * GET /api/admin/stats
 */
router.get("/stats", verifyAdminToken, (req, res) => {
    const players = gameState.getAllPlayers();
    const totalBalance = players.reduce((sum, p) => sum + (p.balance || 0), 0);
    
    res.json({
        success: true,
        status: gameState.gameState.status,
        round: gameState.gameState.round,
        timer: gameState.gameState.timer,
        drawnNumbers: gameState.gameState.drawnNumbers,
        playersCount: gameState.getTotalPlayersCount(),
        activePlayersCount: gameState.getActivePlayersCount(),
        totalBalance: totalBalance.toFixed(2),
        winPercentage: rewardPool.getWinPercentage(),
        totalBet: gameState.gameState.totalBet,
        winnerReward: gameState.gameState.winnerReward,
        adminCommission: gameState.gameState.adminCommission,
        globalSelectedCartelas: gameState.getTotalSelectedCartelasCount(),
        totalCartelas: config.TOTAL_CARTELAS,
        remainingCartelas: config.TOTAL_CARTELAS - gameState.getTotalSelectedCartelasCount()
    });
});

/**
 * Get online players
 * GET /api/admin/players
 */
router.get("/players", verifyAdminToken, (req, res) => {
    const players = gameState.getAllPlayers();
    res.json({
        success: true,
        players: players,
        count: players.length
    });
});

/**
 * Get player details by Telegram ID
 * GET /api/admin/player/:telegramId
 */
router.get("/player/:telegramId", verifyAdminToken, async (req, res) => {
    const { telegramId } = req.params;
    
    const player = gameState.getPlayerByTelegramId(parseInt(telegramId));
    if (!player) {
        return res.status(404).json({ 
            success: false, 
            message: "Player not found" 
        });
    }
    
    res.json({
        success: true,
        player: player.player
    });
});

// ==================== GAME CONTROLS ====================

/**
 * Get current win percentage
 * GET /api/admin/win-percentage
 */
router.get("/win-percentage", verifyAdminToken, (req, res) => {
    res.json({
        success: true,
        percentage: rewardPool.getWinPercentage(),
        available: rewardPool.getAvailableWinPercentages()
    });
});

/**
 * Set win percentage
 * POST /api/admin/win-percentage
 */
router.post("/win-percentage", verifyAdminToken, async (req, res) => {
    const { percentage } = req.body;
    
    if (!validateWinPercentage(percentage)) {
        return res.status(400).json({ 
            success: false, 
            message: `Invalid percentage. Allowed: ${config.WIN_PERCENTAGES.join(", ")}` 
        });
    }
    
    // Update in-memory state
    rewardPool.setWinPercentage(percentage);
    
    // Optionally persist to bot DB via API (handled by server.js)
    res.json({
        success: true,
        message: `Win percentage updated to ${percentage}%`,
        percentage: percentage
    });
});

/**
 * Force start game (skip selection phase)
 * POST /api/admin/start-game
 */
router.post("/start-game", verifyAdminToken, (req, res) => {
    if (gameState.gameState.status === "selection") {
        // Clear selection timer and force start
        gameState.clearSelectionTimer();
        
        // This will be handled by the main server logic
        // The server.js will call roundManager.startActiveGame()
        
        res.json({
            success: true,
            message: "Game started forcefully!"
        });
    } else {
        res.json({
            success: false,
            message: `Cannot start game. Current status: ${gameState.gameState.status}`
        });
    }
});

/**
 * Force end current round (no winner)
 * POST /api/admin/end-game
 */
router.post("/end-game", verifyAdminToken, (req, res) => {
    if (gameState.gameState.status === "active") {
        gameState.clearDrawTimer();
        res.json({
            success: true,
            message: "Round ended forcefully"
        });
    } else {
        res.json({
            success: false,
            message: `Cannot end game. Current status: ${gameState.gameState.status}`
        });
    }
});

/**
 * Reset entire game to round 1
 * POST /api/admin/reset-game
 */
router.post("/reset-game", verifyAdminToken, async (req, res) => {
    gameState.clearAllTimers();
    gameState.fullGameReset();
    
    // Clear active selections from database
    await db.clearActiveSelectionsForRound(gameState.gameState.round);
    
    res.json({
        success: true,
        message: "Game reset to round 1"
    });
});

// ==================== REPORTS ====================

/**
 * Daily report
 * GET /api/reports/daily?date=YYYY-MM-DD
 */
router.get("/reports/daily", verifyAdminToken, async (req, res) => {
    const date = req.query.date || new Date().toISOString().split("T")[0];
    
    try {
        const report = await db.getDailyReport(date);
        res.json({ success: true, report });
    } catch (err) {
        console.error("Daily report error:", err);
        res.status(500).json({ success: false, message: "Failed to generate report" });
    }
});

/**
 * Weekly report
 * GET /api/reports/weekly?year=YYYY&week=W
 */
router.get("/reports/weekly", verifyAdminToken, async (req, res) => {
    const year = parseInt(req.query.year) || new Date().getFullYear();
    const week = parseInt(req.query.week) || getWeekNumber(new Date());
    
    try {
        const report = await db.getWeeklyReport(year, week);
        res.json({ success: true, report });
    } catch (err) {
        console.error("Weekly report error:", err);
        res.status(500).json({ success: false, message: "Failed to generate report" });
    }
});

/**
 * Monthly report
 * GET /api/reports/monthly?year=YYYY&month=M
 */
router.get("/reports/monthly", verifyAdminToken, async (req, res) => {
    const year = parseInt(req.query.year) || new Date().getFullYear();
    const month = parseInt(req.query.month) || new Date().getMonth() + 1;
    
    try {
        const report = await db.getMonthlyReport(year, month);
        res.json({ success: true, report });
    } catch (err) {
        console.error("Monthly report error:", err);
        res.status(500).json({ success: false, message: "Failed to generate report" });
    }
});

/**
 * Custom date range report
 * GET /api/reports/range?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD
 */
router.get("/reports/range", verifyAdminToken, async (req, res) => {
    const { startDate, endDate } = req.query;
    
    if (!startDate || !endDate) {
        return res.status(400).json({ 
            success: false, 
            message: "startDate and endDate required" 
        });
    }
    
    try {
        const report = await db.getRangeReport(startDate, endDate);
        res.json({ success: true, report });
    } catch (err) {
        console.error("Range report error:", err);
        res.status(500).json({ success: false, message: "Failed to generate report" });
    }
});

/**
 * Commission breakdown report
 * GET /api/reports/commission
 */
router.get("/reports/commission", verifyAdminToken, async (req, res) => {
    try {
        const commissionByRound = await db.getCommissionReport();
        const totalCommission = commissionByRound.reduce((sum, r) => sum + (r.admin_commission || 0), 0);
        
        res.json({
            success: true,
            totalCommission,
            commissionByRound
        });
    } catch (err) {
        console.error("Commission report error:", err);
        res.status(500).json({ success: false, message: "Failed to generate report" });
    }
});

// Helper function for week number
function getWeekNumber(date) {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() + 3 - (d.getDay() + 6) % 7);
    const week1 = new Date(d.getFullYear(), 0, 4);
    return 1 + Math.round(((d - week1) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
}

// ==================== EXPORTS ====================
module.exports = router;