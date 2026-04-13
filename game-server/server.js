// =====================================================
// ESTIF BINGO 24/7 - ULTIMATE GAME SERVER (OPTIMIZED)
// Version: 3.0.0
// Features: WebSockets, Bot API Integration, Admin Panel
// =====================================================

const express = require("express");
const http = require("http");
const https = require("https");
const { Server } = require("socket.io");
const cors = require("cors");
const path = require("path");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const compression = require("compression");
const { Pool } = require("pg");
const fs = require("fs");
const rateLimit = require("express-rate-limit");
const { body, validationResult } = require("express-validator");
const helmet = require("helmet");
const morgan = require("morgan");
require("dotenv").config();

// ==================== ENVIRONMENT VALIDATION ====================
const requiredEnv = ["DATABASE_URL", "JWT_SECRET", "BOT_API_URL", "API_SECRET"];
for (const env of requiredEnv) {
    if (!process.env[env]) {
        console.error(`❌ Missing required environment variable: ${env}`);
        process.exit(1);
    }
}

// ==================== KEEP-ALIVE HTTP AGENTS (PERFORMANCE) ====================
const httpAgent = new http.Agent({ keepAlive: true, keepAliveMsecs: 1000, maxSockets: 100, maxFreeSockets: 10 });
const httpsAgent = new https.Agent({ keepAlive: true, keepAliveMsecs: 1000, maxSockets: 100, maxFreeSockets: 10 });

// ==================== CIRCUIT BREAKER FOR BOT API ====================
let circuitState = "CLOSED";
let failureCount = 0;
let lastFailureTime = 0;
const FAILURE_THRESHOLD = 3;
const OPEN_TIMEOUT = 30000;
const HALF_OPEN_SUCCESS_THRESHOLD = 2;
let halfOpenSuccesses = 0;

// ==================== CACHE MANAGEMENT ====================
const cache = new Map();
const CACHE_TTL = 60000; // 60 seconds

function getCached(key) {
    const cached = cache.get(key);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        return cached.data;
    }
    return null;
}

function setCache(key, data) {
    cache.set(key, { data, timestamp: Date.now() });
}

function clearCache() {
    cache.clear();
    console.log("🧹 Cache cleared");
}

// ==================== MIGRATION FLAG ====================
const SKIP_AUTO_MIGRATIONS = process.env.MANUAL_MIGRATION === "true";

// ==================== INITIALISE EXPRESS & SOCKET.IO ====================
const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: { origin: "*", methods: ["GET", "POST"], credentials: true },
    transports: ["websocket", "polling"],
    pingTimeout: 60000,
    pingInterval: 25000,
    allowEIO3: true,
    maxHttpBufferSize: 1e6,
    serveClient: false
});

// ==================== MIDDLEWARE (OPTIMIZED) ====================
app.use(helmet({
    contentSecurityPolicy: false,
    crossOriginEmbedderPolicy: false
}));
app.use(cors());
app.use(express.json({ limit: "1mb" }));
app.use(express.urlencoded({ extended: true, limit: "1mb" }));
app.use(express.static(path.join(__dirname, "public"), { maxAge: "1d", etag: true }));
app.use(compression({ level: 9, threshold: 512, filter: (req, res) => {
    if (req.headers['x-no-compression']) return false;
    return compression.filter(req, res);
}}));

// Logging in production
if (process.env.NODE_ENV === "production") {
    app.use(morgan("combined"));
} else {
    app.use(morgan("dev"));
}

// ==================== RATE LIMITING (OPTIMIZED) ====================
const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 200,
    message: { success: false, message: "Too many requests, please try again later." },
    skipSuccessfulRequests: false,
    standardHeaders: true,
    legacyHeaders: false
});
app.use("/api/", apiLimiter);

const authLimiter = rateLimit({
    windowMs: 10 * 60 * 1000,
    max: 5,
    skipSuccessfulRequests: true,
    keyGenerator: (req) => req.ip
});

const adminLimiter = rateLimit({
    windowMs: 60 * 1000,
    max: 30,
    skipSuccessfulRequests: false
});

// ==================== BOT API CLIENT (WITH CIRCUIT BREAKER & CACHE) ====================
const BOT_API_URL = process.env.BOT_API_URL;
const API_SECRET = process.env.API_SECRET;

async function callBotAPI(endpoint, body, retries = 2, useCache = false) {
    const cacheKey = `${endpoint}:${JSON.stringify(body)}`;
    
    if (useCache) {
        const cached = getCached(cacheKey);
        if (cached) return cached;
    }
    
    if (circuitState === "OPEN") {
        if (Date.now() - lastFailureTime > OPEN_TIMEOUT) {
            circuitState = "HALF_OPEN";
            halfOpenSuccesses = 0;
            console.log(`🔌 Circuit breaker HALF_OPEN for ${endpoint}`);
        } else {
            throw new Error(`Bot API circuit breaker OPEN for ${endpoint}`);
        }
    }
    
    const url = `${BOT_API_URL}${endpoint}`;
    const agent = url.startsWith("https") ? httpsAgent : httpAgent;
    
    for (let attempt = 1; attempt <= retries; attempt++) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_SECRET
                },
                body: JSON.stringify(body),
                agent: agent,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`Bot API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (circuitState === "HALF_OPEN") {
                halfOpenSuccesses++;
                if (halfOpenSuccesses >= HALF_OPEN_SUCCESS_THRESHOLD) {
                    circuitState = "CLOSED";
                    failureCount = 0;
                    console.log(`✅ Circuit breaker CLOSED for ${endpoint}`);
                }
            } else if (circuitState === "CLOSED") {
                failureCount = 0;
            }
            
            if (useCache && data.success) {
                setCache(cacheKey, data);
            }
            
            return data;
        } catch (err) {
            clearTimeout(timeoutId);
            console.warn(`Bot API call failed (attempt ${attempt}/${retries}): ${endpoint} - ${err.message}`);
            
            if (attempt === retries) {
                failureCount++;
                lastFailureTime = Date.now();
                if (failureCount >= FAILURE_THRESHOLD && circuitState !== "OPEN") {
                    circuitState = "OPEN";
                    console.error(`🔴 Circuit breaker OPEN for ${endpoint}`);
                }
                throw err;
            }
            
            await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt - 1)));
        }
    }
}

async function callBotAPIGet(endpoint, useCache = false) {
    if (useCache) {
        const cached = getCached(endpoint);
        if (cached) return cached;
    }
    
    const url = `${BOT_API_URL}${endpoint}`;
    const agent = url.startsWith("https") ? httpsAgent : httpAgent;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);
    
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'X-API-Key': API_SECRET },
            agent: agent,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`Bot API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (useCache) {
            setCache(endpoint, data);
        }
        
        return data;
    } catch (err) {
        clearTimeout(timeoutId);
        throw err;
    }
}

// ==================== POSTGRESQL DATABASE (OPTIMISED WITH CONNECTION POOL) ====================
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === "production" ? { rejectUnauthorized: false } : false,
    max: 50,
    min: 5,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
    statementTimeout: 10000,
    keepAlive: true
});

pool.on('error', (err) => {
    console.error('Unexpected database error:', err);
});

// ==================== MIGRATION SYSTEM (ENHANCED) ====================
async function runMigrations() {
    if (SKIP_AUTO_MIGRATIONS) {
        console.log("⚠️ MANUAL_MIGRATION=true - Skipping automatic migrations");
        return;
    }

    const migrationsDir = path.join(__dirname, "migrations");
    
    if (!fs.existsSync(migrationsDir)) {
        console.log("📁 No migrations directory found, skipping migrations");
        return;
    }

    const client = await pool.connect();
    try {
        await client.query(`
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed_by VARCHAR(100) DEFAULT CURRENT_USER,
                duration_ms INTEGER
            )
        `);
        
        const executed = await client.query("SELECT name FROM migrations");
        const executedSet = new Set(executed.rows.map(r => r.name));
        
        const files = fs.readdirSync(migrationsDir)
            .filter(f => f.endsWith('.sql'))
            .sort();
        
        for (const file of files) {
            if (!executedSet.has(file)) {
                console.log(`📦 Running migration: ${file}`);
                const startTime = Date.now();
                try {
                    const sql = fs.readFileSync(path.join(migrationsDir, file), 'utf8');
                    await client.query('BEGIN');
                    await client.query(sql);
                    await client.query('INSERT INTO migrations (name, duration_ms) VALUES ($1, $2)', [file, Date.now() - startTime]);
                    await client.query('COMMIT');
                    console.log(`✅ Completed: ${file} (${Date.now() - startTime}ms)`);
                } catch (err) {
                    await client.query('ROLLBACK');
                    console.error(`❌ Failed migration: ${file}`, err.message);
                    throw new Error(`Migration ${file} failed: ${err.message}`);
                }
            }
        }
        
        console.log("✅ Migrations completed");
    } catch (err) {
        console.error("❌ Migration system error:", err);
        throw err;
    } finally {
        client.release();
    }
}

async function runManualMigration(migrationFile, options = {}) {
    const { force = false } = options;
    const migrationsDir = path.join(__dirname, "migrations");
    const filePath = path.join(migrationsDir, migrationFile);
    
    if (!fs.existsSync(filePath)) {
        throw new Error(`Migration file not found: ${migrationFile}`);
    }
    
    const client = await pool.connect();
    try {
        const check = await client.query("SELECT * FROM migrations WHERE name = $1", [migrationFile]);
        if (check.rows.length > 0 && !force) {
            throw new Error(`Migration ${migrationFile} already executed. Use force=true to re-run.`);
        }
        
        const sql = fs.readFileSync(filePath, 'utf8');
        const startTime = Date.now();
        
        await client.query('BEGIN');
        await client.query(sql);
        
        if (check.rows.length === 0) {
            await client.query('INSERT INTO migrations (name, duration_ms) VALUES ($1, $2)', [migrationFile, Date.now() - startTime]);
        } else if (force) {
            await client.query('UPDATE migrations SET executed_at = NOW(), duration_ms = $1 WHERE name = $2', [Date.now() - startTime, migrationFile]);
        }
        
        await client.query('COMMIT');
        console.log(`✅ Manual migration completed: ${migrationFile}`);
        return { success: true, message: `Migration ${migrationFile} completed` };
    } catch (err) {
        await client.query('ROLLBACK');
        throw err;
    } finally {
        client.release();
    }
}

async function getMigrationStatus() {
    const client = await pool.connect();
    try {
        const migrations = await client.query(`
            SELECT name, executed_at, executed_by, duration_ms 
            FROM migrations 
            ORDER BY executed_at DESC
        `);
        return migrations.rows;
    } finally {
        client.release();
    }
}

// ==================== INITIAL DATABASE SETUP ====================
async function initDatabase() {
    const client = await pool.connect();
    try {
        // Core tables with optimized indexes
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
                win_percentage INTEGER DEFAULT 80,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_ms INTEGER
            )
        `);
        
        await client.query(`
            CREATE TABLE IF NOT EXISTS game_transactions (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                username VARCHAR(50),
                type VARCHAR(20) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                cartela VARCHAR(20),
                round INTEGER,
                note TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);
        
        await client.query(`
            CREATE TABLE IF NOT EXISTS active_round_selections (
                round_number INTEGER NOT NULL,
                cartela_number VARCHAR(20) NOT NULL,
                telegram_id BIGINT NOT NULL,
                username VARCHAR(100),
                selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (round_number, cartela_number)
            )
        `);
        
        await client.query(`
            CREATE TABLE IF NOT EXISTS game_settings (
                key VARCHAR(50) PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);
        
        // Optimized indexes
        await client.query(`CREATE INDEX IF NOT EXISTS idx_game_rounds_timestamp ON game_rounds(timestamp DESC)`);
        await client.query(`CREATE INDEX IF NOT EXISTS idx_game_rounds_number ON game_rounds(round_number DESC)`);
        await client.query(`CREATE INDEX IF NOT EXISTS idx_active_round_selections_round ON active_round_selections(round_number)`);
        await client.query(`CREATE INDEX IF NOT EXISTS idx_active_round_selections_telegram ON active_round_selections(telegram_id)`);
        await client.query(`CREATE INDEX IF NOT EXISTS idx_game_transactions_telegram ON game_transactions(telegram_id, timestamp DESC)`);
        await client.query(`CREATE INDEX IF NOT EXISTS idx_game_transactions_type ON game_transactions(type, timestamp DESC)`);
        await client.query(`CREATE INDEX IF NOT EXISTS idx_game_transactions_round ON game_transactions(round)`);

        // Add default sound pack setting if not exists
        await client.query(`
            INSERT INTO game_settings (key, value, description) 
            VALUES ('default_sound_pack', 'pack1', 'Default sound pack for new players')
            ON CONFLICT (key) DO NOTHING
        `);

        console.log("✅ PostgreSQL core tables ready");
    } catch (err) {
        console.error("❌ DB init error:", err);
        throw err;
    } finally {
        client.release();
    }
}

async function initializeDatabase() {
    await initDatabase();
    try {
        await runMigrations();
        console.log("✅ Database initialization complete");
    } catch (err) {
        console.error("❌ Database initialization failed:", err);
        if (process.env.NODE_ENV === "production") {
            process.exit(1);
        }
    }
}

// ==================== GAME LOG HELPER (BATCHED) ====================
const transactionBatch = [];
let batchTimeout = null;

async function flushTransactionBatch() {
    if (transactionBatch.length === 0) return;
    
    const batch = [...transactionBatch];
    transactionBatch.length = 0;
    
    const client = await pool.connect();
    try {
        await client.query('BEGIN');
        for (const tx of batch) {
            await client.query(`
                INSERT INTO game_transactions (telegram_id, username, type, amount, cartela, round, note)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            `, [tx.telegramId, tx.username, tx.type, tx.amount, tx.cartela, tx.round, tx.note]);
        }
        await client.query('COMMIT');
    } catch (err) {
        await client.query('ROLLBACK');
        console.error("Failed to flush transaction batch:", err);
    } finally {
        client.release();
    }
}

async function logGameTransaction(telegramId, username, type, amount, cartela, round, note) {
    transactionBatch.push({ telegramId, username, type, amount, cartela, round, note });
    
    if (batchTimeout) clearTimeout(batchTimeout);
    batchTimeout = setTimeout(() => flushTransactionBatch(), 100);
}

// ==================== LOAD CARTELAS FROM JSON FILE (WITH CACHE) ====================
const CARTELA_DATA_FILE = path.join(__dirname, "data/cartelas.json");
let cartelasData = {};
let cartelaKeys = [];

try {
    if (fs.existsSync(CARTELA_DATA_FILE)) {
        const rawData = fs.readFileSync(CARTELA_DATA_FILE, "utf8");
        cartelasData = JSON.parse(rawData);
        cartelaKeys = Object.keys(cartelasData);
        console.log(`✅ Loaded ${cartelaKeys.length} cartelas from data/cartelas.json`);
    } else {
        console.warn(`⚠️ Cartela file not found at: ${CARTELA_DATA_FILE}`);
        // Generate fallback cartelas
        for (let i = 1; i <= 1000; i++) {
            cartelasData[`CART-${String(i).padStart(4, '0')}`] = { grid: generateRandomGrid() };
        }
        cartelaKeys = Object.keys(cartelasData);
        console.log(`✅ Generated ${cartelaKeys.length} fallback cartelas`);
    }
} catch (err) {
    console.error("❌ Error loading cartelas:", err.message);
    // Generate fallback cartelas
    for (let i = 1; i <= 1000; i++) {
        cartelasData[`CART-${String(i).padStart(4, '0')}`] = { grid: generateRandomGrid() };
    }
    cartelaKeys = Object.keys(cartelasData);
}

// ==================== CARTELA HELPER FUNCTIONS (OPTIMIZED) ====================
function getRandomNumbers(min, max, count) {
    const numbers = Array.from({ length: max - min + 1 }, (_, i) => min + i);
    for (let i = numbers.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [numbers[i], numbers[j]] = [numbers[j], numbers[i]];
    }
    return numbers.slice(0, count);
}

function generateRandomGrid() {
    const b = getRandomNumbers(1, 15, 5);
    const i = getRandomNumbers(16, 30, 5);
    const n = getRandomNumbers(31, 45, 5);
    const g = getRandomNumbers(46, 60, 5);
    const o = getRandomNumbers(61, 75, 5);
    n[2] = 0; // Free space
    return [b, i, n, g, o];
}

function getCartelaGrid(cartelaId) {
    // Direct lookup
    if (cartelasData[cartelaId]) {
        return cartelasData[cartelaId].grid;
    }
    // Prefix match (for old format)
    const matchingKey = cartelaKeys.find(key => key.startsWith(cartelaId));
    if (matchingKey) {
        return cartelasData[matchingKey].grid;
    }
    console.warn(`Cartela ${cartelaId} not found, generating random grid`);
    return generateRandomGrid();
}

// ==================== GAME CONSTANTS ====================
const SELECTION_TIME = parseInt(process.env.SELECTION_TIME) || 50;
const DRAW_INTERVAL = parseInt(process.env.DRAW_INTERVAL) || 4000;
const NEXT_ROUND_DELAY = parseInt(process.env.NEXT_ROUND_DELAY) || 6000;
const BET_AMOUNT = parseFloat(process.env.BET_AMOUNT) || 10;
const WIN_PERCENTAGES = [70, 75, 76, 80];
const DEFAULT_WIN_PERCENTAGE = 80;
const MAX_CARTELAS = parseInt(process.env.MAX_CARTELAS) || 4;
const TOTAL_CARTELAS = cartelaKeys.length;

// ==================== GLOBAL STATE (OPTIMIZED) ====================
let gameState = {
    status: "selection",
    round: 1,
    timer: SELECTION_TIME,
    drawnNumbers: [],
    winners: [],
    players: new Map(),
    totalBet: 0,
    winnerReward: 0,
    adminCommission: 0,
    winPercentage: DEFAULT_WIN_PERCENTAGE,
    roundStartTime: null,
    roundEndTime: null,
    gameActive: false
};
let globalTakenCartelas = new Map();
let globalTotalSelectedCartelas = 0;
let selectionTimer = null;
let drawTimer = null;
let nextRoundTimer = null;
let adminTokens = new Map();
let activeSessions = new Map();

// Clean up admin tokens periodically
setInterval(() => {
    const now = Date.now();
    for (const [token, timestamp] of adminTokens) {
        if (now - timestamp > 7 * 24 * 60 * 60 * 1000) {
            adminTokens.delete(token);
        }
    }
}, 60 * 60 * 1000);

// ==================== LOAD WIN PERCENTAGE FROM BOT (WITH CACHE) ====================
async function loadWinPercentage() {
    try {
        const data = await callBotAPIGet("/api/commission", true);
        gameState.winPercentage = data.percentage || DEFAULT_WIN_PERCENTAGE;
        console.log(`✅ Loaded win percentage: ${gameState.winPercentage}%`);
    } catch (err) {
        console.warn("Could not load win percentage from bot, using default:", err.message);
    }
}

// ==================== MULTI-DEVICE HELPERS ====================
function broadcastToUserDevices(telegramId, event, data, excludeSocketId = null) {
    const sessions = activeSessions.get(telegramId);
    if (!sessions) return;
    for (const socketId of sessions) {
        if (socketId !== excludeSocketId) {
            const socket = io.sockets.sockets.get(socketId);
            if (socket) socket.emit(event, data);
        }
    }
}

// ==================== BINGO CHECKING (OPTIMIZED) ====================
function checkBingoWin(cartelaId, drawnNumbers) {
    const grid = getCartelaGrid(cartelaId);
    if (!grid) return { won: false, winningLines: [] };
    
    const drawnSet = new Set(drawnNumbers);
    drawnSet.add(0); // Free space
    
    const lines = [];
    
    // Check rows
    for (let r = 0; r < 5; r++) {
        if (grid[r].every(v => drawnSet.has(v))) {
            lines.push(`Row ${r+1}`);
        }
    }
    
    // Check columns
    for (let c = 0; c < 5; c++) {
        let win = true;
        for (let r = 0; r < 5; r++) {
            if (!drawnSet.has(grid[r][c])) {
                win = false;
                break;
            }
        }
        if (win) lines.push(`Column ${c+1}`);
    }
    
    // Check diagonals
    let d1 = true, d2 = true;
    for (let i = 0; i < 5; i++) {
        if (!drawnSet.has(grid[i][i])) d1 = false;
        if (!drawnSet.has(grid[i][4-i])) d2 = false;
    }
    if (d1) lines.push("Diagonal ↘");
    if (d2) lines.push("Diagonal ↙");
    
    // Check four corners
    if (drawnSet.has(grid[0][0]) && drawnSet.has(grid[0][4]) && 
        drawnSet.has(grid[4][0]) && drawnSet.has(grid[4][4])) {
        lines.push("Four Corners");
    }
    
    // Check full house (all numbers)
    const allNumbers = grid.flat();
    if (allNumbers.every(v => v === 0 || drawnSet.has(v))) {
        lines.push("Full House (BINGO!)");
    }
    
    return { won: lines.length > 0, winningLines: lines };
}

// ==================== GLOBAL CARTELA TRACKING ====================
function isCartelaAvailable(cartelaNumber) { 
    return !globalTakenCartelas.has(cartelaNumber); 
}

async function reserveCartela(cartelaNumber, telegramId, username) {
    if (globalTakenCartelas.has(cartelaNumber)) return false;
    globalTakenCartelas.set(cartelaNumber, { telegramId, username, timestamp: Date.now() });
    globalTotalSelectedCartelas = globalTakenCartelas.size;
    
    // Async DB update (don't await for performance)
    pool.query(`
        INSERT INTO active_round_selections (round_number, cartela_number, telegram_id, username)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (round_number, cartela_number) DO NOTHING
    `, [gameState.round, cartelaNumber, telegramId, username]).catch(err => 
        console.error("Failed to save cartela selection:", err)
    );
    
    return true;
}

async function releaseCartela(cartelaNumber, telegramId) {
    const cartela = globalTakenCartelas.get(cartelaNumber);
    if (cartela && cartela.telegramId === telegramId) {
        globalTakenCartelas.delete(cartelaNumber);
        globalTotalSelectedCartelas = globalTakenCartelas.size;
        
        pool.query(`
            DELETE FROM active_round_selections
            WHERE round_number = $1 AND cartela_number = $2
        `, [gameState.round, cartelaNumber]).catch(err => 
            console.error("Failed to delete cartela selection:", err)
        );
        
        return true;
    }
    return false;
}

function calculateRewardPool() {
    const totalBetAmount = globalTotalSelectedCartelas * BET_AMOUNT;
    const winnerReward = (totalBetAmount * gameState.winPercentage) / 100;
    const adminCommission = totalBetAmount - winnerReward;
    return { totalBetAmount, winnerReward, adminCommission, totalCartelas: globalTotalSelectedCartelas };
}

function broadcastRewardPool() {
    const { totalBetAmount, winnerReward, totalCartelas } = calculateRewardPool();
    io.emit("rewardPoolUpdate", {
        totalSelectedCartelas: totalCartelas,
        totalBetAmount,
        winnerReward,
        winPercentage: gameState.winPercentage,
        remainingCartelas: TOTAL_CARTELAS - totalCartelas,
        pricePerCartela: BET_AMOUNT
    });
}

// ==================== GAME CORE (OPTIMIZED) ====================
function getBingoLetter(num) {
    if (num <= 15) return "B";
    if (num <= 30) return "I";
    if (num <= 45) return "N";
    if (num <= 60) return "G";
    return "O";
}

function formatTime(sec) { 
    const mins = Math.floor(sec / 60);
    const seconds = sec % 60;
    return `${mins}:${seconds.toString().padStart(2, "0")}`; 
}

function broadcastGameState() {
    const playersList = Array.from(gameState.players.values()).map(p => ({
        socketId: p.socketId,
        username: p.username,
        telegramId: p.telegramId,
        selectedCount: p.selectedCartelas.length,
        selectedCartelas: p.selectedCartelas,
        balance: p.balance
    }));
    
    io.emit("gameState", {
        status: gameState.status,
        round: gameState.round,
        timer: gameState.timer,
        drawnNumbers: gameState.drawnNumbers,
        playersCount: gameState.players.size,
        players: playersList,
        winPercentage: gameState.winPercentage,
        totalBet: gameState.totalBet,
        winnerReward: gameState.winnerReward,
        totalCartelasSelected: globalTotalSelectedCartelas,
        totalCartelasAvailable: TOTAL_CARTELAS
    });
}

function broadcastTimer() { 
    io.emit("timerUpdate", { 
        seconds: gameState.timer, 
        round: gameState.round, 
        formatted: formatTime(gameState.timer), 
        phase: gameState.status 
    }); 
}

function stopGame() { 
    if (drawTimer) clearInterval(drawTimer); 
    drawTimer = null; 
    gameState.gameActive = false; 
}

function startSelectionTimer() {
    if (selectionTimer) clearInterval(selectionTimer);
    gameState.status = "selection";
    gameState.timer = SELECTION_TIME;
    gameState.roundStartTime = new Date();
    gameState.gameActive = false;
    broadcastGameState();
    broadcastTimer();
    
    selectionTimer = setInterval(() => {
        if (gameState.status !== "selection") { 
            clearInterval(selectionTimer); 
            selectionTimer = null; 
            return; 
        }
        gameState.timer--;
        broadcastTimer();
        
        if (gameState.timer === 10) {
            io.emit("warning", { message: "⚠️ Only 10 seconds left to select cartelas!", type: "warning" });
        }
        if (gameState.timer <= 0) {
            clearInterval(selectionTimer);
            selectionTimer = null;
            startActiveGame();
        }
    }, 1000);
}

async function startActiveGame() {
    gameState.status = "active";
    gameState.drawnNumbers = [];
    gameState.winners = [];
    gameState.gameActive = true;
    
    const totalCartelas = globalTotalSelectedCartelas;
    const playersWithCartelas = Array.from(gameState.players.values()).filter(p => p.selectedCartelas.length > 0).length;
    const { totalBetAmount, winnerReward, adminCommission } = calculateRewardPool();
    
    gameState.totalBet = totalBetAmount;
    gameState.winnerReward = winnerReward;
    gameState.adminCommission = adminCommission;
    
    broadcastGameState();
    
    io.emit("gameStarted", {
        round: gameState.round,
        totalPlayers: playersWithCartelas,
        totalCartelas,
        totalBet: gameState.totalBet,
        winnerReward: gameState.winnerReward,
        winPercentage: gameState.winPercentage,
        message: `🎲 Game started! ${totalCartelas} cartelas selected. Prize Pool: ${gameState.winnerReward.toFixed(2)} ETB`
    });
    
    io.emit("finalRewardPool", {
        totalSelectedCartelas: totalCartelas,
        totalBetAmount,
        winnerReward,
        winPercentage: gameState.winPercentage,
        message: `🎯 ${totalCartelas} cartelas selected! Total pool: ${totalBetAmount.toFixed(2)} ETB. Winner takes ${winnerReward.toFixed(2)} ETB!`
    });
    
    // Create shuffled numbers array
    const numbers = Array.from({ length: 75 }, (_, i) => i + 1);
    for (let i = numbers.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [numbers[i], numbers[j]] = [numbers[j], numbers[i]];
    }
    
    let idx = 0;
    drawTimer = setInterval(() => {
        if (gameState.status !== "active" || !gameState.gameActive || gameState.winners.length > 0) {
            if (drawTimer) clearInterval(drawTimer);
            return;
        }
        if (idx >= numbers.length) { 
            endRound([]); 
            return; 
        }
        
        const num = numbers[idx++];
        gameState.drawnNumbers.push(num);
        
        io.emit("numberDrawn", { 
            number: num, 
            letter: getBingoLetter(num), 
            drawnCount: gameState.drawnNumbers.length, 
            remaining: 75 - gameState.drawnNumbers.length,
            numbers: gameState.drawnNumbers
        });
        
        broadcastGameState();
        
        // Check for winners
        const newWinners = [];
        const winnerDetails = [];
        
        for (const [sid, pl] of gameState.players) {
            if (pl.selectedCartelas.length && !gameState.winners.includes(sid)) {
                for (const cid of pl.selectedCartelas) {
                    const { won, winningLines } = checkBingoWin(cid, gameState.drawnNumbers);
                    if (won) { 
                        newWinners.push(sid); 
                        winnerDetails.push({ socketId: sid, cartelaId: cid, winningLines, pattern: winningLines[0] }); 
                        break; 
                    }
                }
            }
        }
        
        if (newWinners.length && gameState.winners.length === 0) {
            endRound(newWinners, winnerDetails);
        }
    }, DRAW_INTERVAL);
}

async function endRound(winnerSocketIds, winnerDetails = []) {
    if (gameState.status !== "active") return;
    stopGame();
    gameState.status = "ended";
    gameState.winners = winnerSocketIds;
    gameState.roundEndTime = new Date();
    
    const roundDuration = gameState.roundEndTime - gameState.roundStartTime;
    const winnerCount = winnerSocketIds.length;
    const perWinner = winnerCount ? gameState.winnerReward / winnerCount : 0;
    const winnerNames = [];
    const winnerCartelas = [];
    
    // Process winners in parallel
    const winnerPromises = [];
    
    for (let i = 0; i < winnerSocketIds.length; i++) {
        const sid = winnerSocketIds[i];
        const pl = gameState.players.get(sid);
        const det = winnerDetails.find(d => d.socketId === sid);
        if (pl) {
            winnerNames.push(pl.username);
            if (det) {
                winnerCartelas.push({ 
                    username: pl.username, 
                    cartelaId: det.cartelaId, 
                    winningLines: det.winningLines,
                    pattern: det.pattern
                });
            }
            
            io.to(sid).emit("youWon", { 
                amount: perWinner, 
                cartelaId: det?.cartelaId, 
                winningLines: det?.winningLines,
                pattern: det?.pattern,
                newBalance: pl.balance + perWinner,
                message: `🎉 You won ${perWinner.toFixed(2)} ETB!` 
            });
            
            // Async bot API call
            winnerPromises.push(
                callBotAPI("/api/add", {
                    telegram_id: pl.telegramId,
                    amount: perWinner,
                    round_id: gameState.round,
                    reason: `won round ${gameState.round}`
                }).then(result => {
                    if (result.success) {
                        pl.balance = result.new_balance;
                        broadcastToUserDevices(pl.telegramId, "balanceUpdated", { 
                            balance: pl.balance, 
                            added: perWinner 
                        });
                    }
                }).catch(err => console.error("Error calling bot API for add:", err))
            );
            
            // Log transaction (batched)
            await logGameTransaction(pl.telegramId, pl.username, "win", perWinner, det?.cartelaId, gameState.round, "Round win");
        }
    }
    
    await Promise.allSettled(winnerPromises);
    
    // Save round to database
    const client = await pool.connect();
    try {
        await client.query(`
            INSERT INTO game_rounds (round_number, total_players, total_cartelas, total_pool, winner_reward, admin_commission, winners, winner_cartelas, win_percentage, timestamp, duration_ms)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        `, [
            gameState.round,
            Array.from(gameState.players.values()).filter(p => p.selectedCartelas.length > 0).length,
            globalTotalSelectedCartelas,
            gameState.totalBet,
            gameState.winnerReward,
            gameState.adminCommission,
            JSON.stringify(winnerNames),
            JSON.stringify(winnerCartelas),
            gameState.winPercentage,
            new Date().toISOString(),
            roundDuration
        ]);
    } catch (err) {
        console.error("Failed to save round:", err);
    } finally {
        client.release();
    }
    
    io.emit("roundEnded", {
        winners: winnerNames,
        winnerCartelas: winnerCartelas,
        winnerCount: winnerCount,
        prizePerWinner: perWinner,
        totalPrize: gameState.winnerReward,
        totalPool: gameState.totalBet,
        commission: gameState.adminCommission,
        winPercentage: gameState.winPercentage,
        round: gameState.round,
        duration: roundDuration,
        message: winnerCount ? `🎉 BINGO! Winners: ${winnerNames.join(", ")}. Each wins ${perWinner.toFixed(2)} ETB!` : "No winners this round!"
    });
    
    broadcastGameState();
    scheduleNextRound();
}

function scheduleNextRound() {
    if (nextRoundTimer) clearTimeout(nextRoundTimer);
    let cd = NEXT_ROUND_DELAY / 1000;
    const interval = setInterval(() => { 
        io.emit("nextRoundCountdown", { seconds: cd }); 
        cd--; 
        if (cd < 0) clearInterval(interval); 
    }, 1000);
    
    nextRoundTimer = setTimeout(() => { 
        resetForNextRound(); 
        nextRoundTimer = null; 
    }, NEXT_ROUND_DELAY);
}

async function resetForNextRound() {
    for (const [_, pl] of gameState.players) {
        pl.selectedCartelas = [];
    }
    
    globalTakenCartelas.clear();
    globalTotalSelectedCartelas = 0;
    
    // Async cleanup
    pool.query("DELETE FROM active_round_selections WHERE round_number = $1", [gameState.round]).catch(err => 
        console.error("Failed to clean active selections:", err)
    );
    
    gameState.round++;
    gameState.status = "selection";
    gameState.timer = SELECTION_TIME;
    gameState.drawnNumbers = [];
    gameState.winners = [];
    gameState.totalBet = 0;
    gameState.winnerReward = 0;
    gameState.adminCommission = 0;
    gameState.gameActive = false;
    
    broadcastGameState();
    broadcastTimer();
    broadcastRewardPool();
    
    io.emit("newRound", { 
        round: gameState.round, 
        timer: SELECTION_TIME,
        winPercentage: gameState.winPercentage,
        pricePerCartela: BET_AMOUNT,
        maxCartelas: MAX_CARTELAS,
        message: `🎲 Round ${gameState.round} starting! Select up to ${MAX_CARTELAS} cartelas within ${SELECTION_TIME} seconds.` 
    });
    
    startSelectionTimer();
}

// ==================== CRASH RECOVERY ====================
async function recoverFromCrash() {
    const res = await pool.query(`
        SELECT round_number, cartela_number, telegram_id, username
        FROM active_round_selections
        ORDER BY selected_at
    `);
    
    if (res.rows.length === 0) {
        console.log("No unfinished round found, starting fresh.");
        return;
    }
    
    const roundNumber = res.rows[0].round_number;
    console.log(`🔄 Recovering round ${roundNumber} with ${res.rows.length} selections`);
    
    gameState.round = roundNumber;
    gameState.status = "selection";
    gameState.timer = SELECTION_TIME;
    gameState.drawnNumbers = [];
    gameState.winners = [];
    gameState.gameActive = false;
    
    for (const row of res.rows) {
        globalTakenCartelas.set(row.cartela_number, { 
            telegramId: row.telegram_id, 
            username: row.username || "recovering...", 
            timestamp: Date.now() 
        });
    }
    
    globalTotalSelectedCartelas = globalTakenCartelas.size;
    const { totalBetAmount, winnerReward, adminCommission } = calculateRewardPool();
    gameState.totalBet = totalBetAmount;
    gameState.winnerReward = winnerReward;
    gameState.adminCommission = adminCommission;
    
    console.log(`✅ Recovered: ${globalTotalSelectedCartelas} cartelas, pool: ${gameState.totalBet.toFixed(2)} ETB`);
    startSelectionTimer();
}

// ==================== ADMIN AUTH ====================
const ADMIN_EMAIL = process.env.ADMIN_EMAIL || "johnsonestiph13@gmail.com";
const ADMIN_PASSWORD_HASH = process.env.ADMIN_PASSWORD_HASH || "$2a$10$ZfdgMySJf9kxQpXbdaZVKORiIVkaHFivZK/OxV/Cv7FA7KJjYSDma";

app.post("/api/admin/login", authLimiter, async (req, res) => {
    const { email, password } = req.body;
    if (!email || !password) {
        return res.status(400).json({ success: false, message: "Email and password required" });
    }
    
    if (email !== ADMIN_EMAIL) {
        return res.status(401).json({ success: false, message: "Invalid credentials" });
    }
    
    const isValid = await bcrypt.compare(password, ADMIN_PASSWORD_HASH);
    if (!isValid) {
        return res.status(401).json({ success: false, message: "Invalid credentials" });
    }
    
    const token = jwt.sign({ email, role: "admin" }, process.env.JWT_SECRET, { expiresIn: "7d" });
    adminTokens.set(token, Date.now());
    res.json({ success: true, token, expiresIn: "7d" });
});

function verifyAdminToken(req, res, next) {
    const token = req.headers.authorization?.split(" ")[1];
    if (!token || !adminTokens.has(token)) {
        return res.status(401).json({ success: false, message: "Unauthorized" });
    }
    next();
}

// ==================== ADMIN ENDPOINTS (OPTIMIZED) ====================
app.get("/api/admin/win-percentage", verifyAdminToken, async (req, res) => {
    try {
        const data = await callBotAPIGet("/api/commission", true);
        res.json({ success: true, percentage: data.percentage, available: data.available });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

app.post("/api/admin/win-percentage", verifyAdminToken, adminLimiter, async (req, res) => {
    const { percentage } = req.body;
    if (!WIN_PERCENTAGES.includes(percentage)) {
        return res.status(400).json({ success: false, message: "Invalid percentage. Allowed: " + WIN_PERCENTAGES.join(", ") });
    }
    try {
        await callBotAPI("/api/commission", { percentage });
        gameState.winPercentage = percentage;
        io.emit("winPercentageChanged", { percentage });
        broadcastRewardPool();
        clearCache();
        res.json({ success: true, message: `Win percentage updated to ${percentage}%` });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// ==================== ENHANCED SOUND MANAGEMENT ENDPOINTS ====================
app.get("/api/admin/default-sound-pack", verifyAdminToken, async (req, res) => {
    try {
        const result = await pool.query("SELECT value FROM game_settings WHERE key = 'default_sound_pack'");
        const defaultPack = result.rows[0]?.value || 'pack1';
        res.json({ success: true, defaultSoundPack: defaultPack, availablePacks: ['pack1', 'pack2', 'pack3', 'pack4'] });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

app.post("/api/admin/default-sound-pack", verifyAdminToken, adminLimiter, async (req, res) => {
    const { soundPack } = req.body;
    const validPacks = ['pack1', 'pack2', 'pack3', 'pack4'];
    
    if (!validPacks.includes(soundPack)) {
        return res.status(400).json({ success: false, message: "Invalid sound pack. Allowed: pack1, pack2, pack3, pack4" });
    }
    
    try {
        await pool.query(`
            INSERT INTO game_settings (key, value, description, updated_at) 
            VALUES ('default_sound_pack', $1, 'Default sound pack for new players', NOW())
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
        `, [soundPack]);
        
        res.json({ success: true, message: `Default sound pack set to ${soundPack}` });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

app.post("/api/admin/force-sound-pack", verifyAdminToken, adminLimiter, async (req, res) => {
    const { soundPack } = req.body;
    const validPacks = ['pack1', 'pack2', 'pack3', 'pack4'];
    
    if (!validPacks.includes(soundPack)) {
        return res.status(400).json({ success: false, message: "Invalid sound pack" });
    }
    
    try {
        io.emit("forceSoundPack", { soundPack });
        console.log(`🔊 Admin forced sound pack to ${soundPack} for all ${io.engine.clientsCount} connected players`);
        
        res.json({ success: true, message: `All players forced to use ${soundPack} sound pack`, affectedPlayers: io.engine.clientsCount });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// ==================== REST OF ADMIN ENDPOINTS ====================
app.get("/api/admin/migrations", verifyAdminToken, async (req, res) => {
    try {
        const status = await getMigrationStatus();
        res.json({ success: true, migrations: status });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

app.post("/api/admin/migrate", verifyAdminToken, adminLimiter, async (req, res) => {
    const { migrationFile, force = false } = req.body;
    if (!migrationFile) {
        return res.status(400).json({ success: false, message: "migrationFile required" });
    }
    try {
        const result = await runManualMigration(migrationFile, { force });
        res.json(result);
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

app.get("/api/admin/stats", verifyAdminToken, (req, res) => {
    const players = Array.from(gameState.players.values());
    const totalBalance = players.reduce((s, p) => s + (p.balance || 0), 0);
    res.json({
        success: true,
        status: gameState.status,
        round: gameState.round,
        timer: gameState.timer,
        drawnNumbers: gameState.drawnNumbers,
        drawnCount: gameState.drawnNumbers.length,
        playersCount: players.length,
        totalBalance: totalBalance.toFixed(2),
        winPercentage: gameState.winPercentage,
        totalBet: gameState.totalBet,
        winnerReward: gameState.winnerReward,
        adminCommission: gameState.adminCommission,
        globalSelectedCartelas: globalTotalSelectedCartelas,
        totalCartelasAvailable: TOTAL_CARTELAS,
        uptime: process.uptime(),
        circuitBreakerState: circuitState
    });
});

app.post("/api/admin/start-game", verifyAdminToken, adminLimiter, (req, res) => {
    if (gameState.status === "selection") {
        if (selectionTimer) clearInterval(selectionTimer);
        startActiveGame();
        res.json({ success: true, message: "Game started forcefully!" });
    } else {
        res.json({ success: false, message: `Cannot start, status: ${gameState.status}` });
    }
});

app.post("/api/admin/end-game", verifyAdminToken, adminLimiter, (req, res) => {
    if (gameState.status === "active") { 
        stopGame(); 
        endRound([]); 
        res.json({ success: true, message: "Game ended" }); 
    } else {
        res.json({ success: false, message: `Cannot end, status: ${gameState.status}` });
    }
});

app.post("/api/admin/reset-game", verifyAdminToken, adminLimiter, async (req, res) => {
    stopGame();
    if (selectionTimer) clearInterval(selectionTimer);
    if (nextRoundTimer) clearTimeout(nextRoundTimer);
    
    await pool.query("DELETE FROM active_round_selections");
    
    gameState = {
        ...gameState,
        status: "selection",
        round: 1,
        timer: SELECTION_TIME,
        drawnNumbers: [],
        winners: [],
        totalBet: 0,
        winnerReward: 0,
        adminCommission: 0,
        roundStartTime: null,
        roundEndTime: null,
        gameActive: false
    };
    
    globalTakenCartelas.clear();
    globalTotalSelectedCartelas = 0;
    
    for (const [_, pl] of gameState.players) {
        pl.selectedCartelas = [];
    }
    
    startSelectionTimer();
    broadcastRewardPool();
    io.emit("gameReset", { message: "Game reset by admin" });
    res.json({ success: true, message: "Game reset successfully" });
});

app.get("/api/admin/players", verifyAdminToken, (req, res) => {
    const players = Array.from(gameState.players.values()).map(p => ({
        username: p.username,
        telegramId: p.telegramId,
        selectedCount: p.selectedCartelas.length,
        selectedCartelas: p.selectedCartelas,
        balance: p.balance
    }));
    res.json({ success: true, players, count: players.length });
});

app.post("/api/admin/search-players", verifyAdminToken, async (req, res) => {
    const { search } = req.body;
    if (!search || search.length < 2) {
        return res.status(400).json({ success: false, message: "Search term must be at least 2 characters" });
    }
    try {
        const result = await callBotAPI("/api/search-players", { search });
        res.json(result);
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

app.get("/api/admin/player/:telegramId", verifyAdminToken, async (req, res) => {
    const { telegramId } = req.params;
    if (!telegramId || isNaN(parseInt(telegramId))) {
        return res.status(400).json({ success: false, message: "Valid telegramId required" });
    }
    try {
        const result = await callBotAPI("/api/get-user", { telegram_id: parseInt(telegramId) });
        res.json(result);
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

app.post("/api/admin/adjust-balance", verifyAdminToken, adminLimiter, async (req, res) => {
    const { telegram_id, amount, reason } = req.body;
    if (!telegram_id || amount === undefined) {
        return res.status(400).json({ success: false, message: "telegram_id and amount required" });
    }
    try {
        const result = await callBotAPI("/api/adjust-balance", { telegram_id, amount, reason: reason || "Admin adjustment" });
        res.json(result);
    } catch (err) {  
        res.status(500).json({ success: false, message: err.message });
    }
});

// ==================== REPORT ENDPOINTS ====================
app.get("/api/reports/daily", verifyAdminToken, async (req, res) => {
    const date = req.query.date || new Date().toISOString().split("T")[0];
    const rounds = await pool.query(`
        SELECT * FROM game_rounds WHERE DATE(timestamp) = $1 ORDER BY round_id DESC
    `, [date]);
    const totalGames = rounds.rows.length;
    const totalBet = rounds.rows.reduce((s, r) => s + (r.total_pool || 0), 0);
    const totalWon = rounds.rows.reduce((s, r) => s + (r.winner_reward || 0), 0);
    const totalCommission = rounds.rows.reduce((s, r) => s + (r.admin_commission || 0), 0);
    res.json({ success: true, report: { date, totalGames, totalBet, totalWon, totalCommission, rounds: rounds.rows } });
});

app.get("/api/reports/weekly", verifyAdminToken, async (req, res) => {
    const { year, week } = req.query;
    const targetYear = parseInt(year) || new Date().getFullYear();
    const targetWeek = parseInt(week) || getWeekNumber(new Date());
    const rounds = await pool.query(`
        SELECT * FROM game_rounds 
        WHERE EXTRACT(YEAR FROM timestamp) = $1 AND EXTRACT(WEEK FROM timestamp) = $2 
        ORDER BY round_id DESC
    `, [targetYear, targetWeek]);
    const totalGames = rounds.rows.length;
    const totalBet = rounds.rows.reduce((s, r) => s + (r.total_pool || 0), 0);
    const totalWon = rounds.rows.reduce((s, r) => s + (r.winner_reward || 0), 0);
    const totalCommission = rounds.rows.reduce((s, r) => s + (r.admin_commission || 0), 0);
    res.json({ success: true, report: { year: targetYear, week: targetWeek, totalGames, totalBet, totalWon, totalCommission, rounds: rounds.rows } });
});

app.get("/api/reports/monthly", verifyAdminToken, async (req, res) => {
    const { year, month } = req.query;
    const targetYear = parseInt(year) || new Date().getFullYear();
    const targetMonth = parseInt(month) || new Date().getMonth() + 1;
    const rounds = await pool.query(`
        SELECT * FROM game_rounds 
        WHERE EXTRACT(YEAR FROM timestamp) = $1 AND EXTRACT(MONTH FROM timestamp) = $2 
        ORDER BY round_id DESC
    `, [targetYear, targetMonth]);
    const totalGames = rounds.rows.length;
    const totalBet = rounds.rows.reduce((s, r) => s + (r.total_pool || 0), 0);
    const totalWon = rounds.rows.reduce((s, r) => s + (r.winner_reward || 0), 0);
    const totalCommission = rounds.rows.reduce((s, r) => s + (r.admin_commission || 0), 0);
    res.json({ success: true, report: { year: targetYear, month: targetMonth, totalGames, totalBet, totalWon, totalCommission, rounds: rounds.rows } });
});

app.get("/api/reports/range", verifyAdminToken, async (req, res) => {
    const { startDate, endDate } = req.query;
    if (!startDate || !endDate) {
        return res.status(400).json({ success: false, message: "startDate and endDate required" });
    }
    const rounds = await pool.query(`
        SELECT * FROM game_rounds WHERE DATE(timestamp) BETWEEN $1 AND $2 ORDER BY round_id DESC
    `, [startDate, endDate]);
    const totalGames = rounds.rows.length;
    const totalBet = rounds.rows.reduce((s, r) => s + (r.total_pool || 0), 0);
    const totalWon = rounds.rows.reduce((s, r) => s + (r.winner_reward || 0), 0);
    const totalCommission = rounds.rows.reduce((s, r) => s + (r.admin_commission || 0), 0);
    res.json({ success: true, report: { startDate, endDate, totalGames, totalBet, totalWon, totalCommission, rounds: rounds.rows } });
});

app.get("/api/reports/commission", verifyAdminToken, async (req, res) => {
    const rounds = await pool.query(`
        SELECT round_id, round_number, timestamp, total_pool, winner_reward, admin_commission, win_percentage 
        FROM game_rounds 
        ORDER BY round_id DESC 
        LIMIT 100
    `);
    const totalCommission = rounds.rows.reduce((s, r) => s + (r.admin_commission || 0), 0);
    res.json({ success: true, commissionByRound: rounds.rows, totalCommission });
});

function getWeekNumber(date) {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() + 3 - (d.getDay() + 6) % 7);
    const week1 = new Date(d.getFullYear(), 0, 4);
    return 1 + Math.round(((d - week1) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
}

// ==================== GAME API ENDPOINTS ====================
app.post("/api/exchange-code", authLimiter, async (req, res) => {
    const { code } = req.body;
    if (!code) {
        return res.status(400).json({ success: false, error: "Code required" });
    }
    
    try {
        const result = await callBotAPI("/api/exchange-code", { code });
        res.json(result);
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.get("/api/cartela/:id", (req, res) => {
    const cartelaId = req.params.id;
    const grid = getCartelaGrid(cartelaId);
    res.json({ success: true, cartelaId, grid });
});

app.get("/api/global-stats", (req, res) => {
    const { totalBetAmount, winnerReward, totalCartelas } = calculateRewardPool();
    res.json({ 
        success: true, 
        totalSelectedCartelas: totalCartelas, 
        totalBetAmount, 
        winnerReward, 
        winPercentage: gameState.winPercentage, 
        remainingCartelas: TOTAL_CARTELAS - totalCartelas,
        pricePerCartela: BET_AMOUNT,
        maxCartelasPerPlayer: MAX_CARTELAS,
        round: gameState.round,
        status: gameState.status,
        timer: gameState.timer
    });
});

app.get("/health", (req, res) => { 
    res.json({ 
        status: "OK", 
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        gameState: gameState.status,
        round: gameState.round,
        players: gameState.players.size,
        circuitBreaker: circuitState
    }); 
});

// ==================== SOCKET.IO AUTHENTICATION (OPTIMIZED) ====================
io.on("connection", (socket) => {
    console.log(`🟢 New socket: ${socket.id} (Total: ${io.engine.clientsCount})`);

    // Send default sound pack to newly connected player
    (async () => {
        try {
            const result = await pool.query("SELECT value FROM game_settings WHERE key = 'default_sound_pack'");
            const defaultPack = result.rows[0]?.value || 'pack1';
            socket.emit("defaultSoundPack", { soundPack: defaultPack });
        } catch (err) {
            console.error("Failed to send default sound pack:", err);
        }
    })();

    socket.on("authenticate", async (data) => {
        const { token } = data;
        if (!token) {
            socket.emit("error", { message: "Authentication token required" });
            return;
        }
        
        try {
            const result = await callBotAPI("/api/verify-token", { token });
            if (!result.valid) {
                socket.emit("error", { message: "Invalid or expired token" });
                return;
            }
            
            const { telegram_id, username, balance } = result;
            
            if (!activeSessions.has(telegram_id)) {
                activeSessions.set(telegram_id, new Set());
            }
            activeSessions.get(telegram_id).add(socket.id);
            
            // Find existing player
            let existingPlayer = null;
            for (const [sid, p] of gameState.players) {
                if (p.telegramId === telegram_id) {
                    existingPlayer = p;
                    break;
                }
            }
            
            let playerData;
            if (existingPlayer) {
                playerData = { 
                    socketId: socket.id, 
                    telegramId: telegram_id, 
                    username, 
                    balance,
                    selectedCartelas: existingPlayer.selectedCartelas, 
                    totalWon: existingPlayer.totalWon || 0, 
                    totalPlayed: existingPlayer.totalPlayed || 0, 
                    gamesWon: existingPlayer.gamesWon || 0 
                };
                gameState.players.set(socket.id, playerData);
            } else {
                let savedSelections = [];
                for (const [cartela, { telegramId: tid }] of globalTakenCartelas.entries()) {
                    if (tid === telegram_id) savedSelections.push(cartela);
                }
                playerData = { 
                    socketId: socket.id, 
                    telegramId: telegram_id, 
                    username, 
                    balance,
                    selectedCartelas: savedSelections, 
                    totalWon: 0, 
                    totalPlayed: 0, 
                    gamesWon: 0 
                };
                gameState.players.set(socket.id, playerData);
            }
            
            socket.emit("authenticated", { 
                success: true, 
                user: { telegram_id, username, balance },
                selectedCartelas: playerData.selectedCartelas,
                gameConfig: {
                    betAmount: BET_AMOUNT,
                    maxCartelas: MAX_CARTELAS,
                    selectionTime: SELECTION_TIME,
                    winPercentage: gameState.winPercentage
                }
            });
            
            socket.emit("gameState", {
                status: gameState.status,
                round: gameState.round,
                timer: gameState.timer,
                drawnNumbers: gameState.drawnNumbers,
                playersCount: gameState.players.size,
                winPercentage: gameState.winPercentage,
                totalBet: gameState.totalBet,
                winnerReward: gameState.winnerReward,
                totalCartelasSelected: globalTotalSelectedCartelas,
                totalCartelasAvailable: TOTAL_CARTELAS
            });
            
            socket.emit("timerUpdate", { 
                seconds: gameState.timer, 
                formatted: formatTime(gameState.timer),
                phase: gameState.status
            });
            
            socket.emit("balanceUpdated", { balance, canPlay: balance >= BET_AMOUNT });
            
            broadcastRewardPool();
            
            io.emit("playersUpdate", {
                count: gameState.players.size,
                players: Array.from(gameState.players.values()).map(p => ({
                    socketId: p.socketId,
                    username: p.username,
                    selectedCount: p.selectedCartelas.length,
                    balance: p.balance
                }))
            });
            
        } catch (err) {
            console.error("Authentication error:", err);
            socket.emit("error", { message: "Authentication service unavailable" });
        }
    });

    socket.on("selectCartela", async (data, callback) => {
        try {
            const player = gameState.players.get(socket.id);
            if (!player) throw new Error("Not authenticated");
            if (gameState.status !== "selection") throw new Error(`Cannot select now (${gameState.status})`);
            if (player.selectedCartelas.length >= MAX_CARTELAS) throw new Error(`Max ${MAX_CARTELAS} cartelas per player`);
            if (player.selectedCartelas.includes(data.cartelaId)) throw new Error("Already selected");
            
            // Check balance via cache first
            const balanceResult = await callBotAPI("/api/balance", { telegram_id: player.telegramId }, 2, true);
            if (!balanceResult.success || balanceResult.balance < BET_AMOUNT) {
                throw new Error(`Insufficient balance: ${balanceResult.balance || 0} ETB. Need ${BET_AMOUNT} ETB`);
            }
            
            if (!isCartelaAvailable(data.cartelaId)) {
                const takenBy = globalTakenCartelas.get(data.cartelaId);
                throw new Error(`❌ Cartela ${data.cartelaId} already taken by ${takenBy?.username || "another player"}`);
            }
            
            const deductResult = await callBotAPI("/api/deduct", {
                telegram_id: player.telegramId,
                amount: BET_AMOUNT,
                cartela_id: data.cartelaId,
                round: gameState.round
            });
            
            if (!deductResult.success) throw new Error(deductResult.error || "Balance deduction failed");
            
            player.balance = deductResult.new_balance;
            
            const reserved = await reserveCartela(data.cartelaId, player.telegramId, player.username);
            if (!reserved) throw new Error("Cartela just taken by someone else");
            
            player.selectedCartelas.push(data.cartelaId);
            
            // Async logging (non-blocking)
            logGameTransaction(player.telegramId, player.username, "bet", BET_AMOUNT, data.cartelaId, gameState.round, "Cartela selection");
            
            const selectionData = {
                cartelaId: data.cartelaId,
                selectedCount: player.selectedCartelas.length,
                selectedCartelas: player.selectedCartelas,
                balance: player.balance,
                remainingSlots: MAX_CARTELAS - player.selectedCartelas.length
            };
            
            socket.emit("selectionConfirmed", selectionData);
            broadcastToUserDevices(player.telegramId, "selectionConfirmed", selectionData, socket.id);
            broadcastRewardPool();
            
            io.emit("cartelaTaken", {
                cartelaId: data.cartelaId,
                username: player.username,
                telegramId: player.telegramId,
                remainingCartelas: TOTAL_CARTELAS - globalTotalSelectedCartelas,
                totalSelected: globalTotalSelectedCartelas
            });
            
            broadcastGameState();
            
            if (callback) callback({ success: true, newBalance: player.balance });
            
        } catch (err) {
            console.error("Select cartela error:", err);
            if (callback) callback({ success: false, error: err.message });
            else socket.emit("error", { message: err.message });
        }
    });

    socket.on("deselectCartela", async (data) => {
        try {
            const player = gameState.players.get(socket.id);
            if (!player) return;
            if (gameState.status !== "selection") {
                socket.emit("error", { message: "Cannot deselect now" });
                return;
            }
            
            const idx = player.selectedCartelas.indexOf(data.cartelaId);
            if (idx !== -1) {
                const released = await releaseCartela(data.cartelaId, player.telegramId);
                if (released) {
                    player.selectedCartelas.splice(idx, 1);
                    
                    const refundResult = await callBotAPI("/api/add", {
                        telegram_id: player.telegramId,
                        amount: BET_AMOUNT,
                        reason: `deselected cartela ${data.cartelaId}`
                    });
                    
                    if (refundResult.success) {
                        player.balance = refundResult.new_balance;
                    }
                    
                    logGameTransaction(player.telegramId, player.username, "refund", BET_AMOUNT, data.cartelaId, gameState.round, "Cartela deselected");
                    
                    const updateData = { 
                        selectedCartelas: player.selectedCartelas, 
                        balance: player.balance,
                        remainingSlots: MAX_CARTELAS - player.selectedCartelas.length
                    };
                    
                    socket.emit("selectionUpdated", updateData);
                    broadcastToUserDevices(player.telegramId, "selectionUpdated", updateData, socket.id);
                    broadcastRewardPool();
                    
                    io.emit("cartelaReleased", {
                        cartelaId: data.cartelaId,
                        releasedBy: player.username,
                        availableCartelas: TOTAL_CARTELAS - globalTotalSelectedCartelas,
                        totalSelected: globalTotalSelectedCartelas
                    });
                    
                    broadcastGameState();
                }
            }
        } catch (err) {
            console.error("Deselect cartela error:", err);
            socket.emit("error", { message: err.message });
        }
    });

    socket.on("checkBalance", async (data, callback) => {
        try {
            const player = gameState.players.get(socket.id);
            if (!player) throw new Error("Not authenticated");
            
            const result = await callBotAPI("/api/balance", { telegram_id: player.telegramId });
            if (result.success) {
                player.balance = result.balance;
                socket.emit("balanceUpdated", { balance: player.balance, canPlay: player.balance >= BET_AMOUNT });
                if (callback) callback({ success: true, balance: player.balance });
            } else {
                if (callback) callback({ success: false, error: "Failed to fetch balance" });
            }
        } catch (err) {
            if (callback) callback({ success: false, error: err.message });
        }
    });

    socket.on("getGameStatus", (callback) => {
        if (callback) {
            callback({
                status: gameState.status,
                round: gameState.round,
                timer: gameState.timer,
                drawnNumbers: gameState.drawnNumbers,
                drawnCount: gameState.drawnNumbers.length,
                winPercentage: gameState.winPercentage,
                totalBet: gameState.totalBet,
                winnerReward: gameState.winnerReward,
                totalCartelasSelected: globalTotalSelectedCartelas,
                totalCartelasAvailable: TOTAL_CARTELAS,
                playersCount: gameState.players.size
            });
        }
    });

    socket.on("getPlayerStatus", (callback) => {
        const player = gameState.players.get(socket.id);
        if (player && callback) {
            callback({
                balance: player.balance,
                selectedCartelas: player.selectedCartelas,
                selectedCount: player.selectedCartelas.length,
                gameStatus: gameState.status,
                timer: gameState.timer,
                round: gameState.round,
                drawnNumbers: gameState.drawnNumbers,
                canSelect: gameState.status === "selection" && player.selectedCartelas.length < MAX_CARTELAS
            });
        } else if (callback) {
            callback({ error: "Player not authenticated" });
        }
    });

    socket.on("getCartelaGrid", (data, callback) => {
        const grid = getCartelaGrid(data.cartelaId);
        if (callback) {
            callback({ success: true, cartelaId: data.cartelaId, grid });
        }
    });

    socket.on("ping", (callback) => {
        if (callback) callback({ serverTime: Date.now() });
    });

    socket.on("disconnect", () => {
        console.log(`🔴 Socket disconnected: ${socket.id} (Remaining: ${io.engine.clientsCount})`);
        
        let telegramToRemove = null;
        for (const [tid, sessions] of activeSessions) {
            if (sessions.has(socket.id)) {
                sessions.delete(socket.id);
                if (sessions.size === 0) telegramToRemove = tid;
                break;
            }
        }
        if (telegramToRemove) activeSessions.delete(telegramToRemove);
        
        const player = gameState.players.get(socket.id);
        if (player) {
            const hasOtherSessions = activeSessions.has(player.telegramId);
            if (!hasOtherSessions) {
                for (const [cnum, cart] of globalTakenCartelas) {
                    if (cart.telegramId === player.telegramId) {
                        globalTakenCartelas.delete(cnum);
                    }
                }
                globalTotalSelectedCartelas = globalTakenCartelas.size;
                gameState.players.delete(socket.id);
                console.log(`🗑️ Removed player ${player.username} (${player.telegramId}) - no active sessions`);
            }
        }
        
        broadcastRewardPool();
        broadcastGameState();
        
        io.emit("playersUpdate", {
            count: gameState.players.size,
            players: Array.from(gameState.players.values()).map(p => ({
                socketId: p.socketId,
                username: p.username,
                selectedCount: p.selectedCartelas.length,
                balance: p.balance
            }))
        });
    });
});

// ==================== GRACEFUL SHUTDOWN ====================
async function gracefulShutdown() {
    console.log("🛑 Shutting down gracefully...");
    stopGame();
    if (selectionTimer) clearInterval(selectionTimer);
    if (nextRoundTimer) clearTimeout(nextRoundTimer);
    
    // Flush remaining transactions
    if (transactionBatch.length > 0) {
        await flushTransactionBatch();
    }
    
    await pool.end();
    server.close(() => {
        console.log("✅ Server closed");
        process.exit(0);
    });
    setTimeout(() => {
        console.error("❌ Forced shutdown");
        process.exit(1);
    }, 10000);
}

process.on("SIGTERM", gracefulShutdown);
process.on("SIGINT", gracefulShutdown);

// ==================== START SERVER ====================
async function startServer() {
    const PORT = process.env.PORT || 3000;
    
    await initializeDatabase();
    await loadWinPercentage();
    
    // Start crash recovery after 2 seconds
    setTimeout(() => recoverFromCrash(), 2000);
    startSelectionTimer();
    
    const PLAYER_URL = process.env.PLAYER_URL || "https://estif-bingo-advanced-1.onrender.com/player.html";
    const ADMIN_URL = process.env.ADMIN_URL || "https://estif-bingo-advanced-1.onrender.com/admin.html";
    
    server.listen(PORT, '0.0.0.0', () => {
        console.log(`
╔═══════════════════════════════════════════════════════════════════════════════════════════════╗
║                         🎲 ESTIF BINGO 24/7 - ULTIMATE EDITION 🎲                              ║
╠═══════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                               ║
║     ✅ TOTAL CARTELAS: ${TOTAL_CARTELAS.toString().padEnd(50)}║
║     ✅ MAX CARTELAS PER PLAYER: ${MAX_CARTELAS.toString().padEnd(47)}║
║     ✅ BET AMOUNT: ${BET_AMOUNT} ETB${" ".repeat(47 - BET_AMOUNT.toString().length)}║
║     ✅ SELECTION TIME: ${SELECTION_TIME} seconds${" ".repeat(47 - SELECTION_TIME.toString().length)}║
║     ✅ DRAW INTERVAL: ${DRAW_INTERVAL/1000} seconds${" ".repeat(47 - (DRAW_INTERVAL/1000).toString().length)}║
║     ✅ WIN PERCENTAGES: ${WIN_PERCENTAGES.join(", ")}%${" ".repeat(41 - WIN_PERCENTAGES.join(", ").length)}║
║                                                                                               ║
║     ✅ CIRCUIT BREAKER PROTECTION ACTIVE                                                     ║
║     ✅ KEEP-ALIVE HTTP AGENTS ACTIVE                                                         ║
║     ✅ RESPONSE CACHING ENABLED                                                              ║
║     ✅ BATCH DATABASE WRITES                                                                 ║
║     ✅ BOT INTEGRATION: Balance checks via Telegram                                          ║
║     ✅ SOUND MANAGEMENT: Admin can set default & force sound packs                           ║
║                                                                                               ║
║     📱 Player: ${PLAYER_URL}${" ".repeat(60 - PLAYER_URL.length)}║
║     🔐 Admin:  ${ADMIN_URL}${" ".repeat(60 - ADMIN_URL.length)}║
║                                                                                               ║
║     ✅ Commission adjustable (70/75/76/80) via admin panel                                   ║
║     ✅ Sound packs served from /public/sounds/                                               ║
║     ✅ Full Telegram bot integration                                                         ║
║     ✅ ${TOTAL_CARTELAS} unique cartelas loaded from JSON${" ".repeat(32 - TOTAL_CARTELAS.toString().length)}║
║     ✅ Multi-device sync support                                                             ║
║     ✅ Crash recovery with active_round_selections                                           ║
║     ✅ Admin session expires in 7 days                                                       ║
║     ✅ WebSocket ping timeout: 60s                                                           ║
║                                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════╝
        `);
    });
}

startServer().catch(console.error);

module.exports = { app, server, io, gameState, runManualMigration, getMigrationStatus, clearCache };