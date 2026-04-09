// game-server/src/api/game.js
// Estif Bingo 24/7 - Public Game API Endpoints

const express = require("express");
const router = express.Router();
const { Pool } = require("pg");

// ==================== CONFIGURATION ====================
const config = {
    TOTAL_CARTELAS: 1000,
    MAX_CARTELAS: 4,
    BET_AMOUNT: 10,
    SELECTION_TIME: 50,
    DRAW_INTERVAL: 4000,
    WIN_PERCENTAGES: [70, 75, 76, 80],
    NODE_ENV: process.env.NODE_ENV || "development"
};

// Database connection
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === "production" ? { rejectUnauthorized: false } : false
});

// Game state reference (will be set from server.js)
let gameStateRef = null;
let rewardPoolRef = null;
let cartelaDataRef = null;

// Helper functions
function isValidCartelaId(id) {
    return id >= 1 && id <= config.TOTAL_CARTELAS;
}

function getCachedCartelasCount() {
    return cartelaDataRef ? Object.keys(cartelaDataRef).length : 0;
}

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
    
    // Get cartela grid from cache or generate
    let grid = null;
    if (cartelaDataRef && cartelaDataRef[id]) {
        grid = cartelaDataRef[id].grid;
    } else if (gameStateRef && gameStateRef.getCartelaGrid) {
        grid = gameStateRef.getCartelaGrid(id);
    }
    
    if (!grid) {
        return res.status(404).json({ 
            success: false, 
            message: "Cartela grid not found" 
        });
    }
    
    res.json({
        success: true,
        cartelaId: id,
        grid: grid
    });
});

/**
 * Get multiple cartela grids (batch)
 * POST /api/cartelas/batch
 */
router.post("/cartelas/batch", (req, res) => {
    const { ids } = req.body;
    
    if (!ids || !Array.isArray(ids)) {
        return res.status(400).json({ 
            success: false, 
            message: "ids array required" 
        });
    }
    
    const results = [];
    for (const id of ids) {
        const cartelaId = parseInt(id);
        if (isValidCartelaId(cartelaId)) {
            let grid = null;
            if (cartelaDataRef && cartelaDataRef[cartelaId]) {
                grid = cartelaDataRef[cartelaId].grid;
            } else if (gameStateRef && gameStateRef.getCartelaGrid) {
                grid = gameStateRef.getCartelaGrid(cartelaId);
            }
            
            results.push({
                cartelaId: cartelaId,
                success: true,
                grid: grid
            });
        } else {
            results.push({
                cartelaId: cartelaId,
                success: false,
                error: "Invalid cartela ID"
            });
        }
    }
    
    res.json({
        success: true,
        cartelas: results
    });
});

/**
 * Get global game statistics (public)
 * GET /api/global-stats
 */
router.get("/global-stats", (req, res) => {
    const totalCartelas = gameStateRef?.globalTotalSelectedCartelas || 0;
    const winPercentage = rewardPoolRef?.getWinPercentage?.() || config.WIN_PERCENTAGES[1];
    const totalBetAmount = totalCartelas * config.BET_AMOUNT;
    const winnerReward = (totalBetAmount * winPercentage) / 100;
    const adminCommission = totalBetAmount - winnerReward;
    
    res.json({
        success: true,
        totalSelectedCartelas: totalCartelas,
        totalBetAmount: totalBetAmount,
        winnerReward: winnerReward,
        adminCommission: adminCommission,
        winPercentage: winPercentage,
        remainingCartelas: config.TOTAL_CARTELAS - totalCartelas,
        round: gameStateRef?.gameState?.round || 1,
        status: gameStateRef?.gameState?.status || "selection",
        playersOnline: gameStateRef?.players?.size || 0,
        maxCartelasPerPlayer: config.MAX_CARTELAS,
        betAmount: config.BET_AMOUNT
    });
});

/**
 * Get current round number
 * GET /api/current-round
 */
router.get("/current-round", (req, res) => {
    res.json({
        success: true,
        round: gameStateRef?.gameState?.round || 1,
        status: gameStateRef?.gameState?.status || "selection",
        timer: gameStateRef?.gameState?.timer || config.SELECTION_TIME,
        phase: gameStateRef?.gameState?.status || "selection"
    });
});

/**
 * Get drawn numbers so far
 * GET /api/drawn-numbers
 */
router.get("/drawn-numbers", (req, res) => {
    const drawnNumbers = gameStateRef?.gameState?.drawnNumbers || [];
    res.json({
        success: true,
        drawnNumbers: drawnNumbers,
        count: drawnNumbers.length,
        remaining: 75 - drawnNumbers.length
    });
});

/**
 * Get recent winners (last 10 rounds)
 * GET /api/recent-winners
 */
router.get("/recent-winners", async (req, res) => {
    try {
        const limit = parseInt(req.query.limit) || 10;
        const result = await pool.query(`
            SELECT round_number, winners, winner_reward, timestamp, total_pool, win_percentage
            FROM game_rounds 
            WHERE winners IS NOT NULL AND winners != '[]'
            ORDER BY round_id DESC 
            LIMIT $1
        `, [limit]);
        
        const recentWinners = result.rows.map(round => ({
            roundNumber: round.round_number,
            winners: round.winners,
            prizeAmount: round.winner_reward,
            timestamp: round.timestamp,
            totalPool: round.total_pool,
            winPercentage: round.win_percentage
        }));
        
        res.json({
            success: true,
            winners: recentWinners,
            count: recentWinners.length
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
    
    let isAvailable = true;
    let owner = null;
    
    if (gameStateRef?.globalTakenCartelas) {
        const takenInfo = gameStateRef.globalTakenCartelas.get(id);
        isAvailable = !takenInfo;
        owner = takenInfo || null;
    }
    
    res.json({
        success: true,
        cartelaId: id,
        available: isAvailable,
        takenBy: owner?.username || null,
        takenAt: owner?.timestamp || null
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
        let isAvailable = true;
        let owner = null;
        
        if (gameStateRef?.globalTakenCartelas) {
            const takenInfo = gameStateRef.globalTakenCartelas.get(i);
            isAvailable = !takenInfo;
            owner = takenInfo;
        }
        
        allCartelas.push({
            cartelaId: i,
            available: isAvailable,
            takenBy: owner?.username || null,
            takenAt: owner?.timestamp || null
        });
    }
    
    const paginatedCartelas = allCartelas.slice(start, end);
    
    res.json({
        success: true,
        cartelas: paginatedCartelas,
        page: page,
        limit: limit,
        total: config.TOTAL_CARTELAS,
        totalPages: Math.ceil(config.TOTAL_CARTELAS / limit),
        maxCartelasPerPlayer: config.MAX_CARTELAS
    });
});

/**
 * Get active players list (public)
 * GET /api/active-players
 */
router.get("/active-players", (req, res) => {
    const players = [];
    if (gameStateRef?.players) {
        for (const [socketId, player] of gameStateRef.players) {
            players.push({
                username: player.username,
                selectedCount: player.selectedCartelas?.length || 0,
                balance: player.balance || 0
            });
        }
    }
    
    res.json({
        success: true,
        players: players,
        count: players.length,
        maxPlayers: "unlimited"
    });
});

/**
 * Get player stats by Telegram ID
 * GET /api/player-stats/:telegramId
 */
router.get("/player-stats/:telegramId", async (req, res) => {
    const { telegramId } = req.params;
    
    try {
        // Get player stats from database
        const result = await pool.query(`
            SELECT 
                COUNT(*) as total_games_played,
                SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END) as total_won,
                SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END) as total_bet,
                COUNT(CASE WHEN type = 'win' THEN 1 END) as games_won
            FROM game_transactions 
            WHERE telegram_id = $1
        `, [telegramId]);
        
        // Get current session info
        let currentGame = null;
        if (gameStateRef?.players) {
            for (const player of gameStateRef.players.values()) {
                if (player.telegramId === parseInt(telegramId)) {
                    currentGame = {
                        online: true,
                        selectedCartelas: player.selectedCartelas || [],
                        currentRound: gameStateRef.gameState?.round
                    };
                    break;
                }
            }
        }
        
        const stats = result.rows[0] || {};
        
        res.json({
            success: true,
            stats: {
                totalGamesPlayed: parseInt(stats.total_games_played) || 0,
                totalWon: parseFloat(stats.total_won) || 0,
                totalBet: parseFloat(stats.total_bet) || 0,
                gamesWon: parseInt(stats.games_won) || 0,
                winRate: stats.total_games_played ? 
                    ((stats.games_won / stats.total_games_played) * 100).toFixed(2) : 0
            },
            currentGame: currentGame || { online: false }
        });
    } catch (err) {
        console.error("Player stats error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to fetch player stats" 
        });
    }
});

/**
 * Get server health status
 * GET /api/health
 */
router.get("/health", async (req, res) => {
    let dbHealthy = false;
    try {
        await pool.query("SELECT 1");
        dbHealthy = true;
    } catch (err) {
        console.error("Database health check failed:", err);
    }
    
    res.json({
        success: true,
        status: "online",
        timestamp: new Date().toISOString(),
        version: "3.0.0",
        game: {
            status: gameStateRef?.gameState?.status || "unknown",
            round: gameStateRef?.gameState?.round || 1,
            players: gameStateRef?.players?.size || 0,
            selectedCartelas: gameStateRef?.globalTotalSelectedCartelas || 0
        },
        database: dbHealthy ? "connected" : "disconnected",
        cache: {
            cartelasCached: getCachedCartelasCount(),
            totalCartelas: config.TOTAL_CARTELAS
        },
        config: {
            maxCartelasPerPlayer: config.MAX_CARTELAS,
            betAmount: config.BET_AMOUNT,
            selectionTime: config.SELECTION_TIME,
            drawInterval: config.DRAW_INTERVAL
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
        description: "Real-time multiplayer Bingo platform",
        version: "3.0.0",
        nodeVersion: process.version,
        environment: config.NODE_ENV,
        uptime: uptimeFormatted,
        uptimeSeconds: Math.floor(uptime),
        features: {
            totalCartelas: config.TOTAL_CARTELAS,
            maxCartelasPerPlayer: config.MAX_CARTELAS,
            betAmount: `${config.BET_AMOUNT} ETB`,
            selectionTime: `${config.SELECTION_TIME} seconds`,
            drawInterval: `${config.DRAW_INTERVAL / 1000} seconds`,
            availableWinPercentages: config.WIN_PERCENTAGES,
            soundPacks: ["Classic", "Electronic", "Casino", "Retro"],
            multiDeviceSupport: true,
            crashRecovery: true
        },
        links: {
            player: "/player.html",
            admin: "/admin.html",
            health: "/api/health"
        }
    });
});

/**
 * Get top winners leaderboard
 * GET /api/leaderboard?limit=10
 */
router.get("/leaderboard", async (req, res) => {
    const limit = Math.min(parseInt(req.query.limit) || 10, 50);
    
    try {
        const result = await pool.query(`
            SELECT 
                telegram_id,
                username,
                SUM(amount) as total_won,
                COUNT(*) as wins
            FROM game_transactions 
            WHERE type = 'win'
            GROUP BY telegram_id, username
            ORDER BY total_won DESC
            LIMIT $1
        `, [limit]);
        
        res.json({
            success: true,
            leaderboard: result.rows.map(row => ({
                telegramId: row.telegram_id,
                username: row.username,
                totalWon: parseFloat(row.total_won),
                wins: parseInt(row.wins)
            })),
            count: result.rows.length
        });
    } catch (err) {
        console.error("Leaderboard error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to fetch leaderboard" 
        });
    }
});

/**
 * Get statistics summary
 * GET /api/stats/summary
 */
router.get("/stats/summary", async (req, res) => {
    try {
        // Get total games
        const totalGamesResult = await pool.query("SELECT COUNT(*) FROM game_rounds");
        const totalGames = parseInt(totalGamesResult.rows[0].count);
        
        // Get total payouts
        const payoutsResult = await pool.query("SELECT SUM(winner_reward) as total FROM game_rounds");
        const totalPayouts = parseFloat(payoutsResult.rows[0].total) || 0;
        
        // Get total commission
        const commissionResult = await pool.query("SELECT SUM(admin_commission) as total FROM game_rounds");
        const totalCommission = parseFloat(commissionResult.rows[0].total) || 0;
        
        // Get total players
        const playersResult = await pool.query("SELECT COUNT(DISTINCT telegram_id) FROM game_transactions");
        const totalPlayers = parseInt(playersResult.rows[0].count);
        
        res.json({
            success: true,
            summary: {
                totalGames: totalGames,
                totalPayouts: totalPayouts,
                totalCommission: totalCommission,
                totalPlayers: totalPlayers,
                averagePrizePerGame: totalGames > 0 ? (totalPayouts / totalGames).toFixed(2) : 0,
                currentOnline: gameStateRef?.players?.size || 0,
                currentRound: gameStateRef?.gameState?.round || 1,
                currentStatus: gameStateRef?.gameState?.status || "selection"
            }
        });
    } catch (err) {
        console.error("Stats summary error:", err);
        res.status(500).json({ 
            success: false, 
            message: "Failed to fetch statistics" 
        });
    }
});

// ==================== INITIALIZATION ====================
function init(gameState, rewardPool, cartelaData) {
    gameStateRef = gameState;
    rewardPoolRef = rewardPool;
    cartelaDataRef = cartelaData;
    console.log("✅ Game API initialized");
}

// ==================== EXPORTS ====================
module.exports = router;
module.exports.init = init;
module.exports.isValidCartelaId = isValidCartelaId;