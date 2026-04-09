// game-server/src/api/admin.js
// Estif Bingo 24/7 - Complete Admin API Routes

const express = require("express");
const router = express.Router();
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const { Pool } = require("pg");

// ==================== CONFIGURATION ====================
const config = {
    ADMIN_EMAIL: process.env.ADMIN_EMAIL || "johnsonestiph13@gmail.com",
    ADMIN_PASSWORD_HASH: process.env.ADMIN_PASSWORD_HASH,
    JWT_SECRET: process.env.JWT_SECRET,
    WIN_PERCENTAGES: [70, 75, 76, 80],
    TOTAL_CARTELAS: 1000,
    BET_AMOUNT: 10
};

// Database connection
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === "production" ? { rejectUnauthorized: false } : false
});

// Token storage (in production, use Redis)
let adminTokens = new Map();

// Bot API URL
const BOT_API_URL = process.env.BOT_API_URL;
const API_SECRET = process.env.API_SECRET;

// Game state reference (will be set from server.js)
let gameStateRef = null;
let rewardPoolRef = null;
let roundManagerRef = null;

// Helper function to call bot API
async function callBotAPI(endpoint, method = 'GET', body = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_SECRET
        }
    };
    if (body) options.body = JSON.stringify(body);
    
    const response = await fetch(`${BOT_API_URL}${endpoint}`, options);
    if (!response.ok) {
        throw new Error(`Bot API error: ${response.status}`);
    }
    return response.json();
}

// ==================== AUTHENTICATION ====================

/**
 * Generate admin token
 */
function generateAdminToken(email) {
    const token = jwt.sign(
        { email, role: "admin", timestamp: Date.now() },
        config.JWT_SECRET,
        { expiresIn: "24h" }
    );
    adminTokens.set(token, Date.now());
    return token;
}

/**
 * Verify admin token middleware
 */
function verifyAdminToken(req, res, next) {
    const token = req.headers.authorization?.split(" ")[1];
    if (!token || !adminTokens.has(token)) {
        return res.status(401).json({ 
            success: false, 
            message: "Unauthorized: Invalid or expired token" 
        });
    }
    
    try {
        const decoded = jwt.verify(token, config.JWT_SECRET);
        req.admin = decoded;
        next();
    } catch (err) {
        adminTokens.delete(token);
        return res.status(401).json({ 
            success: false, 
            message: "Unauthorized: Token expired" 
        });
    }
}

/**
 * Revoke admin token (logout)
 */
function revokeAdminToken(token) {
    adminTokens.delete(token);
}

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
    
    // Verify password
    let isValid = false;
    if (config.ADMIN_PASSWORD_HASH) {
        isValid = await bcrypt.compare(password, config.ADMIN_PASSWORD_HASH);
    } else {
        // Fallback for development (remove in production)
        isValid = password === "estiphBingo";
    }
    
    if (!isValid) {
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
    // Get stats from game state if available
    const status = gameStateRef?.gameState?.status || "selection";
    const round = gameStateRef?.gameState?.round || 1;
    const timer = gameStateRef?.gameState?.timer || 50;
    const drawnNumbers = gameStateRef?.gameState?.drawnNumbers || [];
    const playersCount = gameStateRef?.players?.size || 0;
    const totalBet = gameStateRef?.gameState?.totalBet || 0;
    const winnerReward = gameStateRef?.gameState?.winnerReward || 0;
    const adminCommission = gameStateRef?.gameState?.adminCommission || 0;
    const winPercentage = gameStateRef?.gameState?.winPercentage || 75;
    const globalSelectedCartelas = gameStateRef?.globalTotalSelectedCartelas || 0;
    
    // Calculate total balance from players
    let totalBalance = 0;
    if (gameStateRef?.players) {
        for (const player of gameStateRef.players.values()) {
            totalBalance += player.balance || 0;
        }
    }
    
    res.json({
        success: true,
        status: status,
        round: round,
        timer: timer,
        drawnNumbers: drawnNumbers,
        playersCount: playersCount,
        activePlayersCount: playersCount,
        totalBalance: totalBalance.toFixed(2),
        winPercentage: winPercentage,
        totalBet: totalBet,
        winnerReward: winnerReward,
        adminCommission: adminCommission,
        globalSelectedCartelas: globalSelectedCartelas,
        totalCartelas: config.TOTAL_CARTELAS,
        remainingCartelas: config.TOTAL_CARTELAS - globalSelectedCartelas
    });
});

/**
 * Get online players
 * GET /api/admin/players
 */
router.get("/players", verifyAdminToken, (req, res) => {
    const players = [];
    if (gameStateRef?.players) {
        for (const [socketId, player] of gameStateRef.players) {
            players.push({
                socketId: socketId,
                username: player.username,
                telegramId: player.telegramId,
                selectedCount: player.selectedCartelas?.length || 0,
                selectedCartelas: player.selectedCartelas || [],
                balance: player.balance || 0
            });
        }
    }
    
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
    
    try {
        // Get player from bot database
        const result = await callBotAPI(`/api/get-user/${telegramId}`, 'GET');
        
        if (result.success && result.user) {
            // Get current session info from game state
            let currentGameData = null;
            if (gameStateRef?.players) {
                for (const player of gameStateRef.players.values()) {
                    if (player.telegramId === parseInt(telegramId)) {
                        currentGameData = {
                            online: true,
                            selectedCartelas: player.selectedCartelas || [],
                            currentRound: gameStateRef.gameState?.round
                        };
                        break;
                    }
                }
            }
            
            res.json({
                success: true,
                player: {
                    ...result.user,
                    currentGame: currentGameData || { online: false }
                }
            });
        } else {
            res.status(404).json({ 
                success: false, 
                message: "Player not found" 
            });
        }
    } catch (err) {
        console.error("Error fetching player:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to fetch player details" 
        });
    }
});

/**
 * Search players by username or phone
 * POST /api/admin/search-players
 */
router.post("/search-players", verifyAdminToken, async (req, res) => {
    const { search } = req.body;
    
    if (!search || search.length < 2) {
        return res.status(400).json({ 
            success: false, 
            message: "Search term must be at least 2 characters" 
        });
    }
    
    try {
        const result = await callBotAPI('/api/search-players', 'POST', { search });
        res.json(result);
    } catch (err) {
        console.error("Search players error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to search players" 
        });
    }
});

/**
 * Adjust player balance
 * POST /api/admin/adjust-balance
 */
router.post("/adjust-balance", verifyAdminToken, async (req, res) => {
    const { telegram_id, amount, reason } = req.body;
    
    if (!telegram_id || amount === undefined) {
        return res.status(400).json({ 
            success: false, 
            message: "telegram_id and amount required" 
        });
    }
    
    try {
        const result = await callBotAPI('/api/adjust-balance', 'POST', {
            telegram_id,
            amount,
            reason: reason || "Admin adjustment"
        });
        
        if (result.success) {
            // Update balance in game state if player is online
            if (gameStateRef?.players) {
                for (const player of gameStateRef.players.values()) {
                    if (player.telegramId === telegram_id) {
                        player.balance = result.new_balance;
                        break;
                    }
                }
            }
        }
        
        res.json(result);
    } catch (err) {
        console.error("Adjust balance error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to adjust balance" 
        });
    }
});

// ==================== GAME CONTROLS ====================

/**
 * Get current win percentage
 * GET /api/admin/win-percentage
 */
router.get("/win-percentage", verifyAdminToken, async (req, res) => {
    try {
        // Get from bot API
        const result = await callBotAPI('/api/commission', 'GET');
        res.json({
            success: true,
            percentage: result.percentage || 75,
            available: config.WIN_PERCENTAGES
        });
    } catch (err) {
        // Fallback to game state
        const percentage = gameStateRef?.gameState?.winPercentage || 75;
        res.json({
            success: true,
            percentage: percentage,
            available: config.WIN_PERCENTAGES
        });
    }
});

/**
 * Set win percentage
 * POST /api/admin/win-percentage
 */
router.post("/win-percentage", verifyAdminToken, async (req, res) => {
    const { percentage } = req.body;
    
    if (!config.WIN_PERCENTAGES.includes(percentage)) {
        return res.status(400).json({ 
            success: false, 
            message: `Invalid percentage. Allowed: ${config.WIN_PERCENTAGES.join(", ")}` 
        });
    }
    
    try {
        // Update via bot API
        await callBotAPI('/api/commission', 'POST', { percentage });
        
        // Update game state
        if (gameStateRef) {
            gameStateRef.gameState.winPercentage = percentage;
        }
        
        // Broadcast to all players
        const io = req.app.get('io');
        if (io) {
            io.emit("winPercentageChanged", { percentage });
        }
        
        res.json({
            success: true,
            message: `Win percentage updated to ${percentage}%`,
            percentage: percentage
        });
    } catch (err) {
        console.error("Set win percentage error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to update win percentage" 
        });
    }
});

/**
 * Force start game (skip selection phase)
 * POST /api/admin/start-game
 */
router.post("/start-game", verifyAdminToken, (req, res) => {
    if (gameStateRef?.gameState?.status === "selection") {
        // Clear selection timer and force start
        if (gameStateRef.selectionTimer) {
            clearInterval(gameStateRef.selectionTimer);
            gameStateRef.selectionTimer = null;
        }
        
        // Trigger active game start (handled by server.js)
        if (roundManagerRef && roundManagerRef.startActiveGame) {
            roundManagerRef.startActiveGame();
        }
        
        res.json({
            success: true,
            message: "Game started forcefully!"
        });
    } else {
        res.json({
            success: false,
            message: `Cannot start game. Current status: ${gameStateRef?.gameState?.status || "unknown"}`
        });
    }
});

/**
 * Force end current round (no winner)
 * POST /api/admin/end-game
 */
router.post("/end-game", verifyAdminToken, (req, res) => {
    if (gameStateRef?.gameState?.status === "active") {
        // Clear draw timer
        if (gameStateRef.drawTimer) {
            clearInterval(gameStateRef.drawTimer);
            gameStateRef.drawTimer = null;
        }
        
        // End round with no winners
        if (roundManagerRef && roundManagerRef.endRound) {
            roundManagerRef.endRound([]);
        }
        
        res.json({
            success: true,
            message: "Round ended forcefully"
        });
    } else {
        res.json({
            success: false,
            message: `Cannot end game. Current status: ${gameStateRef?.gameState?.status || "unknown"}`
        });
    }
});

/**
 * Reset entire game to round 1
 * POST /api/admin/reset-game
 */
router.post("/reset-game", verifyAdminToken, async (req, res) => {
    try {
        // Clear all timers
        if (gameStateRef) {
            if (gameStateRef.selectionTimer) clearInterval(gameStateRef.selectionTimer);
            if (gameStateRef.drawTimer) clearInterval(gameStateRef.drawTimer);
            if (gameStateRef.nextRoundTimer) clearTimeout(gameStateRef.nextRoundTimer);
            
            // Reset game state
            gameStateRef.gameState = {
                status: "selection",
                round: 1,
                timer: 50,
                drawnNumbers: [],
                winners: [],
                players: gameStateRef.gameState?.players || new Map(),
                totalBet: 0,
                winnerReward: 0,
                adminCommission: 0,
                winPercentage: gameStateRef.gameState?.winPercentage || 75,
                roundStartTime: null,
                roundEndTime: null,
                gameActive: false
            };
            
            // Clear selections
            if (gameStateRef.globalTakenCartelas) {
                gameStateRef.globalTakenCartelas.clear();
            }
            if (gameStateRef.globalTotalSelectedCartelas !== undefined) {
                gameStateRef.globalTotalSelectedCartelas = 0;
            }
            
            // Clear player selections
            if (gameStateRef.gameState?.players) {
                for (const player of gameStateRef.gameState.players.values()) {
                    player.selectedCartelas = [];
                }
            }
            
            // Restart selection timer
            if (roundManagerRef && roundManagerRef.startSelectionTimer) {
                roundManagerRef.startSelectionTimer();
            }
        }
        
        // Clear active selections from database
        await pool.query("DELETE FROM active_round_selections");
        
        // Broadcast reset to all players
        const io = req.app.get('io');
        if (io) {
            io.emit("gameReset", { message: "Game reset by admin to round 1" });
        }
        
        res.json({
            success: true,
            message: "Game reset to round 1"
        });
    } catch (err) {
        console.error("Reset game error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to reset game" 
        });
    }
});

// ==================== REPORTS ====================

/**
 * Daily report
 * GET /api/reports/daily?date=YYYY-MM-DD
 */
router.get("/reports/daily", verifyAdminToken, async (req, res) => {
    const date = req.query.date || new Date().toISOString().split("T")[0];
    
    try {
        const rounds = await pool.query(`
            SELECT * FROM game_rounds 
            WHERE DATE(timestamp) = $1 
            ORDER BY round_id DESC
        `, [date]);
        
        const totalGames = rounds.rows.length;
        const totalBet = rounds.rows.reduce((s, r) => s + (r.total_pool || 0), 0);
        const totalWon = rounds.rows.reduce((s, r) => s + (r.winner_reward || 0), 0);
        const totalCommission = rounds.rows.reduce((s, r) => s + (r.admin_commission || 0), 0);
        
        res.json({ 
            success: true, 
            report: { 
                date, 
                totalGames, 
                totalBet: totalBet.toFixed(2), 
                totalWon: totalWon.toFixed(2), 
                totalCommission: totalCommission.toFixed(2),
                rounds: rounds.rows 
            } 
        });
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
        const rounds = await pool.query(`
            SELECT * FROM game_rounds 
            WHERE EXTRACT(YEAR FROM timestamp) = $1 
            AND EXTRACT(WEEK FROM timestamp) = $2 
            ORDER BY round_id DESC
        `, [year, week]);
        
        const totalGames = rounds.rows.length;
        const totalBet = rounds.rows.reduce((s, r) => s + (r.total_pool || 0), 0);
        const totalWon = rounds.rows.reduce((s, r) => s + (r.winner_reward || 0), 0);
        const totalCommission = rounds.rows.reduce((s, r) => s + (r.admin_commission || 0), 0);
        
        res.json({ 
            success: true, 
            report: { 
                year, 
                week, 
                totalGames, 
                totalBet: totalBet.toFixed(2), 
                totalWon: totalWon.toFixed(2), 
                totalCommission: totalCommission.toFixed(2),
                rounds: rounds.rows 
            } 
        });
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
        const rounds = await pool.query(`
            SELECT * FROM game_rounds 
            WHERE EXTRACT(YEAR FROM timestamp) = $1 
            AND EXTRACT(MONTH FROM timestamp) = $2 
            ORDER BY round_id DESC
        `, [year, month]);
        
        const totalGames = rounds.rows.length;
        const totalBet = rounds.rows.reduce((s, r) => s + (r.total_pool || 0), 0);
        const totalWon = rounds.rows.reduce((s, r) => s + (r.winner_reward || 0), 0);
        const totalCommission = rounds.rows.reduce((s, r) => s + (r.admin_commission || 0), 0);
        
        res.json({ 
            success: true, 
            report: { 
                year, 
                month, 
                totalGames, 
                totalBet: totalBet.toFixed(2), 
                totalWon: totalWon.toFixed(2), 
                totalCommission: totalCommission.toFixed(2),
                rounds: rounds.rows 
            } 
        });
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
        const rounds = await pool.query(`
            SELECT * FROM game_rounds 
            WHERE DATE(timestamp) BETWEEN $1 AND $2 
            ORDER BY round_id DESC
        `, [startDate, endDate]);
        
        const totalGames = rounds.rows.length;
        const totalBet = rounds.rows.reduce((s, r) => s + (r.total_pool || 0), 0);
        const totalWon = rounds.rows.reduce((s, r) => s + (r.winner_reward || 0), 0);
        const totalCommission = rounds.rows.reduce((s, r) => s + (r.admin_commission || 0), 0);
        
        res.json({ 
            success: true, 
            report: { 
                startDate, 
                endDate, 
                totalGames, 
                totalBet: totalBet.toFixed(2), 
                totalWon: totalWon.toFixed(2), 
                totalCommission: totalCommission.toFixed(2),
                rounds: rounds.rows 
            } 
        });
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
        const rounds = await pool.query(`
            SELECT round_id, timestamp, total_pool, winner_reward, admin_commission, win_percentage 
            FROM game_rounds 
            ORDER BY round_id DESC
        `);
        
        const totalCommission = rounds.rows.reduce((sum, r) => sum + (r.admin_commission || 0), 0);
        
        res.json({
            success: true,
            totalCommission: totalCommission.toFixed(2),
            commissionByRound: rounds.rows.map(r => ({
                ...r,
                total_pool: r.total_pool?.toFixed(2),
                winner_reward: r.winner_reward?.toFixed(2),
                admin_commission: r.admin_commission?.toFixed(2)
            }))
        });
    } catch (err) {
        console.error("Commission report error:", err);
        res.status(500).json({ success: false, message: "Failed to generate report" });
    }
});

/**
 * Export report as CSV
 * GET /api/reports/export/daily?date=YYYY-MM-DD
 * GET /api/reports/export/range?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD
 */
router.get("/reports/export/:type", verifyAdminToken, async (req, res) => {
    const { type } = req.params;
    
    let rounds = [];
    let filename = "";
    
    try {
        if (type === "daily") {
            const date = req.query.date || new Date().toISOString().split("T")[0];
            const result = await pool.query(`
                SELECT * FROM game_rounds 
                WHERE DATE(timestamp) = $1 
                ORDER BY round_id DESC
            `, [date]);
            rounds = result.rows;
            filename = `bingo_report_${date}.csv`;
        } else if (type === "range") {
            const { startDate, endDate } = req.query;
            if (!startDate || !endDate) {
                return res.status(400).json({ success: false, message: "startDate and endDate required" });
            }
            const result = await pool.query(`
                SELECT * FROM game_rounds 
                WHERE DATE(timestamp) BETWEEN $1 AND $2 
                ORDER BY round_id DESC
            `, [startDate, endDate]);
            rounds = result.rows;
            filename = `bingo_report_${startDate}_to_${endDate}.csv`;
        } else {
            return res.status(400).json({ success: false, message: "Invalid export type" });
        }
        
        // Generate CSV
        if (rounds.length === 0) {
            return res.status(404).json({ success: false, message: "No data found" });
        }
        
        const headers = ["Round ID", "Round Number", "Date", "Total Pool", "Winner Reward", "Commission", "Win %", "Winners"];
        const csvRows = [headers.join(",")];
        
        for (const round of rounds) {
            const winners = round.winners ? JSON.parse(round.winners).join("; ") : "";
            csvRows.push([
                round.round_id,
                round.round_number,
                new Date(round.timestamp).toLocaleString(),
                round.total_pool,
                round.winner_reward,
                round.admin_commission,
                round.win_percentage,
                `"${winners}"`
            ].join(","));
        }
        
        res.setHeader("Content-Type", "text/csv");
        res.setHeader("Content-Disposition", `attachment; filename="${filename}"`);
        res.send(csvRows.join("\n"));
        
    } catch (err) {
        console.error("Export report error:", err);
        res.status(500).json({ success: false, message: "Failed to export report" });
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

// ==================== INITIALIZATION ====================
function init(gameState, rewardPool, roundManager) {
    gameStateRef = gameState;
    rewardPoolRef = rewardPool;
    roundManagerRef = roundManager;
}

// ==================== EXPORTS ====================
module.exports = router;
module.exports.init = init;
module.exports.verifyAdminToken = verifyAdminToken;