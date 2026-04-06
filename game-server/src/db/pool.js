// game-server/src/db/pool.js

const { Pool } = require("pg");
const { config } = require("../config");

// ==================== POSTGRESQL CONNECTION POOL ====================
const pool = new Pool({
    connectionString: config.DATABASE_URL,
    ssl: config.IS_PRODUCTION ? { rejectUnauthorized: false } : false,
    max: config.DB_POOL_MAX,
    idleTimeoutMillis: config.DB_IDLE_TIMEOUT,
    connectionTimeoutMillis: config.DB_CONNECTION_TIMEOUT,
});

// ==================== EVENT HANDLERS ====================
pool.on("connect", () => {
    console.log("✅ PostgreSQL pool: new client connected");
});

pool.on("error", (err) => {
    console.error("❌ PostgreSQL pool error:", err);
});

// ==================== DATABASE INITIALIZATION ====================
async function initGameDatabase() {
    const client = await pool.connect();
    try {
        // Game rounds table
        await client.query(`
            CREATE TABLE IF NOT EXISTS game_rounds (
                round_id SERIAL PRIMARY KEY,
                round_number INTEGER NOT NULL,
                total_players INTEGER DEFAULT 0,
                total_cartelas INTEGER DEFAULT 0,
                total_pool DECIMAL(10,2) DEFAULT 0,
                winner_reward DECIMAL(10,2) DEFAULT 0,
                admin_commission DECIMAL(10,2) DEFAULT 0,
                winners JSONB,
                winner_cartelas JSONB,
                win_percentage INTEGER DEFAULT 75,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);

        // Game transactions log (for auditing)
        await client.query(`
            CREATE TABLE IF NOT EXISTS game_transactions (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                username VARCHAR(50),
                type VARCHAR(20) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                cartela INTEGER,
                round INTEGER,
                note TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);

        // Active round selections (for crash recovery)
        await client.query(`
            CREATE TABLE IF NOT EXISTS active_round_selections (
                round_number INTEGER NOT NULL,
                cartela_number INTEGER NOT NULL,
                telegram_id BIGINT NOT NULL,
                selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (round_number, cartela_number)
            )
        `);

        // Create indexes for better query performance
        await client.query(`
            CREATE INDEX IF NOT EXISTS idx_game_rounds_timestamp 
            ON game_rounds(timestamp DESC)
        `);
        
        await client.query(`
            CREATE INDEX IF NOT EXISTS idx_game_rounds_round_number 
            ON game_rounds(round_number DESC)
        `);
        
        await client.query(`
            CREATE INDEX IF NOT EXISTS idx_active_round_selections_round 
            ON active_round_selections(round_number)
        `);
        
        await client.query(`
            CREATE INDEX IF NOT EXISTS idx_game_transactions_telegram 
            ON game_transactions(telegram_id)
        `);
        
        await client.query(`
            CREATE INDEX IF NOT EXISTS idx_game_transactions_timestamp 
            ON game_transactions(timestamp DESC)
        `);

        console.log("✅ Game database tables ready");
    } catch (err) {
        console.error("❌ Database initialization error:", err);
        throw err;
    } finally {
        client.release();
    }
}

// ==================== GAME ROUND OPERATIONS ====================
async function saveGameRound(roundData) {
    const { roundNumber, totalPlayers, totalCartelas, totalPool, winnerReward, adminCommission, winners, winnerCartelas, winPercentage, timestamp } = roundData;
    
    const result = await pool.query(`
        INSERT INTO game_rounds (
            round_number, total_players, total_cartelas, total_pool, 
            winner_reward, admin_commission, winners, winner_cartelas, 
            win_percentage, timestamp
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING round_id
    `, [
        roundNumber, totalPlayers, totalCartelas, totalPool,
        winnerReward, adminCommission, JSON.stringify(winners),
        JSON.stringify(winnerCartelas), winPercentage, timestamp
    ]);
    
    return result.rows[0].round_id;
}

async function getGameRounds(filters = {}) {
    let query = "SELECT * FROM game_rounds ORDER BY round_id DESC";
    const params = [];
    const conditions = [];
    
    if (filters.startDate) {
        conditions.push(`DATE(timestamp) >= $${params.length + 1}`);
        params.push(filters.startDate);
    }
    if (filters.endDate) {
        conditions.push(`DATE(timestamp) <= $${params.length + 1}`);
        params.push(filters.endDate);
    }
    if (filters.roundNumber) {
        conditions.push(`round_number = $${params.length + 1}`);
        params.push(filters.roundNumber);
    }
    
    if (conditions.length > 0) {
        query = `SELECT * FROM game_rounds WHERE ${conditions.join(" AND ")} ORDER BY round_id DESC`;
    }
    
    if (filters.limit) {
        query += ` LIMIT $${params.length + 1}`;
        params.push(filters.limit);
    }
    if (filters.offset) {
        query += ` OFFSET $${params.length + 1}`;
        params.push(filters.offset);
    }
    
    const result = await pool.query(query, params);
    return result.rows;
}

async function getGameRoundById(roundId) {
    const result = await pool.query("SELECT * FROM game_rounds WHERE round_id = $1", [roundId]);
    return result.rows[0];
}

// ==================== GAME TRANSACTION OPERATIONS ====================
async function logGameTransaction(telegramId, username, type, amount, cartela, round, note) {
    const result = await pool.query(`
        INSERT INTO game_transactions (telegram_id, username, type, amount, cartela, round, note)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
    `, [telegramId, username, type, amount, cartela, round, note]);
    
    return result.rows[0].id;
}

async function getGameTransactions(telegramId, limit = 50, offset = 0) {
    const result = await pool.query(`
        SELECT * FROM game_transactions 
        WHERE telegram_id = $1 
        ORDER BY timestamp DESC 
        LIMIT $2 OFFSET $3
    `, [telegramId, limit, offset]);
    
    return result.rows;
}

// ==================== ACTIVE ROUND SELECTIONS (Crash Recovery) ====================
async function saveActiveSelection(roundNumber, cartelaNumber, telegramId) {
    await pool.query(`
        INSERT INTO active_round_selections (round_number, cartela_number, telegram_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (round_number, cartela_number) DO NOTHING
    `, [roundNumber, cartelaNumber, telegramId]);
}

async function removeActiveSelection(roundNumber, cartelaNumber) {
    await pool.query(`
        DELETE FROM active_round_selections
        WHERE round_number = $1 AND cartela_number = $2
    `, [roundNumber, cartelaNumber]);
}

async function clearActiveSelectionsForRound(roundNumber) {
    await pool.query("DELETE FROM active_round_selections WHERE round_number = $1", [roundNumber]);
}

async function getActiveSelections() {
    const result = await pool.query(`
        SELECT round_number, cartela_number, telegram_id, selected_at
        FROM active_round_selections
        ORDER BY selected_at
    `);
    return result.rows;
}

async function getActiveSelectionsByRound(roundNumber) {
    const result = await pool.query(`
        SELECT cartela_number, telegram_id, selected_at
        FROM active_round_selections
        WHERE round_number = $1
        ORDER BY selected_at
    `, [roundNumber]);
    return result.rows;
}

// ==================== REPORTING OPERATIONS ====================
async function getDailyReport(date) {
    const result = await pool.query(`
        SELECT 
            COUNT(*) as total_games,
            COALESCE(SUM(total_pool), 0) as total_bet,
            COALESCE(SUM(winner_reward), 0) as total_won,
            COALESCE(SUM(admin_commission), 0) as total_commission
        FROM game_rounds 
        WHERE DATE(timestamp) = $1
    `, [date]);
    
    const rounds = await pool.query(`
        SELECT * FROM game_rounds 
        WHERE DATE(timestamp) = $1 
        ORDER BY round_id DESC
    `, [date]);
    
    return {
        ...result.rows[0],
        rounds: rounds.rows
    };
}

async function getWeeklyReport(year, week) {
    const result = await pool.query(`
        SELECT 
            COUNT(*) as total_games,
            COALESCE(SUM(total_pool), 0) as total_bet,
            COALESCE(SUM(winner_reward), 0) as total_won,
            COALESCE(SUM(admin_commission), 0) as total_commission
        FROM game_rounds 
        WHERE EXTRACT(YEAR FROM timestamp) = $1 AND EXTRACT(WEEK FROM timestamp) = $2
    `, [year, week]);
    
    const rounds = await pool.query(`
        SELECT * FROM game_rounds 
        WHERE EXTRACT(YEAR FROM timestamp) = $1 AND EXTRACT(WEEK FROM timestamp) = $2 
        ORDER BY round_id DESC
    `, [year, week]);
    
    return {
        ...result.rows[0],
        rounds: rounds.rows
    };
}

async function getMonthlyReport(year, month) {
    const result = await pool.query(`
        SELECT 
            COUNT(*) as total_games,
            COALESCE(SUM(total_pool), 0) as total_bet,
            COALESCE(SUM(winner_reward), 0) as total_won,
            COALESCE(SUM(admin_commission), 0) as total_commission
        FROM game_rounds 
        WHERE EXTRACT(YEAR FROM timestamp) = $1 AND EXTRACT(MONTH FROM timestamp) = $2
    `, [year, month]);
    
    const rounds = await pool.query(`
        SELECT * FROM game_rounds 
        WHERE EXTRACT(YEAR FROM timestamp) = $1 AND EXTRACT(MONTH FROM timestamp) = $2 
        ORDER BY round_id DESC
    `, [year, month]);
    
    return {
        ...result.rows[0],
        rounds: rounds.rows
    };
}

async function getRangeReport(startDate, endDate) {
    const result = await pool.query(`
        SELECT 
            COUNT(*) as total_games,
            COALESCE(SUM(total_pool), 0) as total_bet,
            COALESCE(SUM(winner_reward), 0) as total_won,
            COALESCE(SUM(admin_commission), 0) as total_commission
        FROM game_rounds 
        WHERE DATE(timestamp) BETWEEN $1 AND $2
    `, [startDate, endDate]);
    
    const rounds = await pool.query(`
        SELECT * FROM game_rounds 
        WHERE DATE(timestamp) BETWEEN $1 AND $2 
        ORDER BY round_id DESC
    `, [startDate, endDate]);
    
    return {
        ...result.rows[0],
        rounds: rounds.rows
    };
}

async function getCommissionReport() {
    const result = await pool.query(`
        SELECT 
            round_id, 
            timestamp, 
            total_pool, 
            winner_reward, 
            admin_commission,
            win_percentage,
            ROUND((admin_commission / NULLIF(total_pool, 0)) * 100, 2) as commission_percentage
        FROM game_rounds 
        ORDER BY round_id DESC
    `);
    
    return result.rows;
}

// ==================== HEALTH CHECK ====================
async function healthCheck() {
    try {
        await pool.query("SELECT 1");
        return true;
    } catch (err) {
        console.error("Database health check failed:", err);
        return false;
    }
}

// ==================== GRACEFUL SHUTDOWN ====================
async function closePool() {
    console.log("Closing PostgreSQL pool...");
    await pool.end();
    console.log("PostgreSQL pool closed");
}

// ==================== EXPORTS ====================
module.exports = {
    pool,
    initGameDatabase,
    saveGameRound,
    getGameRounds,
    getGameRoundById,
    logGameTransaction,
    getGameTransactions,
    saveActiveSelection,
    removeActiveSelection,
    clearActiveSelectionsForRound,
    getActiveSelections,
    getActiveSelectionsByRound,
    getDailyReport,
    getWeeklyReport,
    getMonthlyReport,
    getRangeReport,
    getCommissionReport,
    healthCheck,
    closePool,
};