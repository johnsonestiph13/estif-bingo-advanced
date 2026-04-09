// game-server/src/config/index.js
// Estif Bingo 24/7 - Central Configuration Module

const dotenv = require("dotenv");
const path = require("path");

// Load environment variables
dotenv.config();

// ==================== ENVIRONMENT VALIDATION ====================
const requiredEnv = [
    "DATABASE_URL",
    "JWT_SECRET",
    "BOT_API_URL",
    "API_SECRET"
];

const missingEnv = requiredEnv.filter(env => !process.env[env]);
if (missingEnv.length > 0) {
    console.error(`❌ Missing required environment variables: ${missingEnv.join(", ")}`);
    if (process.env.NODE_ENV !== "production") {
        console.warn("⚠️ Continuing anyway for development, but expect errors.");
    } else {
        process.exit(1);
    }
}

// ==================== BINGO CONFIGURATION ====================
// Cartela ID ranges (75 unique cartela types)
// B1-B15, I16-I30, N31-N45, G46-G60, O61-O75
const BINGO_LETTERS = {
    'B': { min: 1, max: 15, prefix: 'B', count: 15 },
    'I': { min: 16, max: 30, prefix: 'I', count: 15 },
    'N': { min: 31, max: 45, prefix: 'N', count: 15 },
    'G': { min: 46, max: 60, prefix: 'G', count: 15 },
    'O': { min: 61, max: 75, prefix: 'O', count: 15 }
};

// Generate all cartela IDs (75 total)
const ALL_CARTELA_IDS = [];
for (const [letter, range] of Object.entries(BINGO_LETTERS)) {
    for (let num = range.min; num <= range.max; num++) {
        ALL_CARTELA_IDS.push(`${letter}${num}`);
    }
}
const TOTAL_CARTELA_TYPES = ALL_CARTELA_IDS.length; // 75

// Each cartela type can have multiple variations
// Total variations are loaded from cartelas.json
let TOTAL_CARTELA_VARIATIONS = 0;

// ==================== SERVER CONFIG ====================
const config = {
    // Server
    PORT: parseInt(process.env.PORT, 10) || 3000,
    NODE_ENV: process.env.NODE_ENV || "development",
    IS_PRODUCTION: process.env.NODE_ENV === "production",
    IS_DEVELOPMENT: process.env.NODE_ENV === "development",
    
    // Server URLs
    SERVER_URL: process.env.SERVER_URL || "https://estif-bingo-advanced-1.onrender.com",
    PLAYER_URL: process.env.PLAYER_URL || "https://estif-bingo-advanced-1.onrender.com/player.html",
    ADMIN_URL: process.env.ADMIN_URL || "https://estif-bingo-advanced-1.onrender.com/admin.html",

    // Database
    DATABASE_URL: process.env.DATABASE_URL,
    DB_POOL_MAX: parseInt(process.env.DB_POOL_MAX, 10) || 20,
    DB_IDLE_TIMEOUT: parseInt(process.env.DB_IDLE_TIMEOUT, 10) || 30000,
    DB_CONNECTION_TIMEOUT: parseInt(process.env.DB_CONNECTION_TIMEOUT, 10) || 5000,
    DB_SSL: process.env.NODE_ENV === "production" ? { rejectUnauthorized: false } : false,

    // Security
    JWT_SECRET: process.env.JWT_SECRET,
    API_SECRET: process.env.API_SECRET,
    JWT_EXPIRY: process.env.JWT_EXPIRY || "2h",
    JWT_REFRESH_EXPIRY: process.env.JWT_REFRESH_EXPIRY || "7d",
    
    // Admin credentials
    ADMIN_EMAIL: process.env.ADMIN_EMAIL || "johnsonestiph13@gmail.com",
    ADMIN_PASSWORD_HASH: process.env.ADMIN_PASSWORD_HASH || "$2b$10$CwTycUXWue0Thq9StjUM0uJ4Q6Z5wZ5Z5wZ5Z5wZ5Z5wZ5Z5wZ5Z5",
    ADMIN_SESSION_EXPIRY: "24h",

    // Bot API
    BOT_API_URL: process.env.BOT_API_URL,
    BOT_API_TIMEOUT: parseInt(process.env.BOT_API_TIMEOUT, 10) || 10000,
    BOT_API_RETRIES: parseInt(process.env.BOT_API_RETRIES, 10) || 3,
    BOT_API_RETRY_DELAY: parseInt(process.env.BOT_API_RETRY_DELAY, 10) || 1000,

    // Game constants
    SELECTION_TIME: parseInt(process.env.SELECTION_TIME, 10) || 50,
    DRAW_INTERVAL: parseInt(process.env.DRAW_INTERVAL, 10) || 4000,
    NEXT_ROUND_DELAY: parseInt(process.env.NEXT_ROUND_DELAY, 10) || 6000,
    BET_AMOUNT: parseFloat(process.env.BET_AMOUNT) || 10,
    MAX_CARTELAS: parseInt(process.env.MAX_CARTELAS, 10) || 4,
    TOTAL_CARTELA_TYPES: TOTAL_CARTELA_TYPES, // 75 unique cartela IDs
    MIN_BALANCE_FOR_PLAY: parseFloat(process.env.MIN_BALANCE_FOR_PLAY) || 10,
    
    // BINGO Configuration
    BINGO_LETTERS: BINGO_LETTERS,
    ALL_CARTELA_IDS: ALL_CARTELA_IDS,
    
    // Win percentages
    WIN_PERCENTAGES: [70, 75, 76, 80],
    DEFAULT_WIN_PERCENTAGE: 75,

    // Sound packs
    SOUND_PACKS: ["pack1", "pack2", "pack3", "pack4"],
    SOUND_PACK_NAMES: {
        pack1: "Classic Pack",
        pack2: "Electronic Pack",
        pack3: "Casino Pack",
        pack4: "Retro Pack"
    },
    DEFAULT_SOUND_PACK: "pack1",
    SOUND_VOLUME_DEFAULT: 0.7,

    // CORS origins
    CORS_ORIGINS: process.env.CORS_ORIGINS
        ? process.env.CORS_ORIGINS.split(",")
        : (process.env.NODE_ENV === "production"
            ? [
                "https://estif-bingo-advanced-1.onrender.com",
                "https://estif-bingo-bot-1.onrender.com"
              ]
            : [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://localhost:5000",
                "https://estif-bingo-advanced-1.onrender.com",
                "https://estif-bingo-bot-1.onrender.com"
              ]),

    // Rate limiting
    RATE_LIMIT_WINDOW_MS: parseInt(process.env.RATE_LIMIT_WINDOW_MS, 10) || 15 * 60 * 1000,
    RATE_LIMIT_MAX: parseInt(process.env.RATE_LIMIT_MAX, 10) || 100,
    AUTH_RATE_LIMIT_MAX: parseInt(process.env.AUTH_RATE_LIMIT_MAX, 10) || 5,
    GAME_RATE_LIMIT_MAX: parseInt(process.env.GAME_RATE_LIMIT_MAX, 10) || 30,

    // WebSocket configuration
    WS_PING_TIMEOUT: parseInt(process.env.WS_PING_TIMEOUT, 10) || 60000,
    WS_PING_INTERVAL: parseInt(process.env.WS_PING_INTERVAL, 10) || 25000,
    WS_MAX_RECONNECT_ATTEMPTS: parseInt(process.env.WS_MAX_RECONNECT_ATTEMPTS, 10) || 10,
    WS_RECONNECT_DELAY: parseInt(process.env.WS_RECONNECT_DELAY, 10) || 1000,

    // Cache configuration
    CARTELA_CACHE_EXPIRY: parseInt(process.env.CARTELA_CACHE_EXPIRY, 10) || 30 * 60 * 1000,
    PLAYER_SESSION_TIMEOUT: parseInt(process.env.PLAYER_SESSION_TIMEOUT, 10) || 30 * 60 * 1000,

    // Paths
    PUBLIC_DIR: path.join(__dirname, "../../public"),
    DATA_DIR: path.join(__dirname, "../../data"),
    CARTELA_DATA_FILE: path.join(__dirname, "../../data/cartelas.json"),
    SOUNDS_DIR: path.join(__dirname, "../../public/assets/sounds"),
    IMAGES_DIR: path.join(__dirname, "../../public/assets/images"),

    // Feature flags
    FEATURES: {
        MULTI_DEVICE_SYNC: true,
        CRASH_RECOVERY: true,
        SOUND_PACKS: true,
        REFERRAL_SYSTEM: process.env.ENABLE_REFERRAL === "true",
        LEADERBOARD: true,
        DAILY_BONUS: process.env.ENABLE_DAILY_BONUS === "true"
    },

    // Logging
    LOG_LEVEL: process.env.LOG_LEVEL || (process.env.NODE_ENV === "production" ? "info" : "debug"),
    LOG_TO_FILE: process.env.LOG_TO_FILE === "true",
    LOG_FILE_PATH: path.join(__dirname, "../../logs/game-server.log"),
};

// ==================== CORS OPTIONS ====================
const corsOptions = {
    origin: function (origin, callback) {
        if (!origin) return callback(null, true);
        if (config.CORS_ORIGINS.indexOf(origin) !== -1 || config.NODE_ENV !== "production") {
            callback(null, true);
        } else {
            console.warn(`CORS blocked origin: ${origin}`);
            callback(new Error("Not allowed by CORS"));
        }
    },
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization", "X-API-Key", "X-Requested-With"],
    exposedHeaders: ["Content-Disposition"],
    maxAge: 86400
};

// ==================== HELPER FUNCTIONS ====================

/**
 * Parse cartela ID (e.g., "B15" -> { letter: "B", number: 15 })
 * @param {string} cartelaId - Cartela ID like "B15"
 * @returns {object|null}
 */
function parseCartelaId(cartelaId) {
    const match = cartelaId.match(/^([BINGO])(\d+)$/);
    if (!match) return null;
    return {
        letter: match[1],
        number: parseInt(match[2], 10),
        fullId: cartelaId
    };
}

/**
 * Validate cartela ID
 * @param {string} cartelaId - Cartela ID to validate
 * @returns {boolean}
 */
function isValidCartelaId(cartelaId) {
    const parsed = parseCartelaId(cartelaId);
    if (!parsed) return false;
    
    const range = config.BINGO_LETTERS[parsed.letter];
    if (!range) return false;
    
    return parsed.number >= range.min && parsed.number <= range.max;
}

/**
 * Get cartela index (0-74)
 * @param {string} cartelaId - Cartela ID like "B15"
 * @returns {number}
 */
function getCartelaIndex(cartelaId) {
    return config.ALL_CARTELA_IDS.indexOf(cartelaId);
}

/**
 * Get BINGO letter for a number (1-75)
 * @param {number} number - Drawn number
 * @returns {string}
 */
function getBingoLetterForNumber(number) {
    if (number <= 15) return 'B';
    if (number <= 30) return 'I';
    if (number <= 45) return 'N';
    if (number <= 60) return 'G';
    return 'O';
}

/**
 * Get BINGO letter for cartela ID
 * @param {string} cartelaId - Cartela ID like "B15"
 * @returns {string}
 */
function getBingoLetterForCartela(cartelaId) {
    const parsed = parseCartelaId(cartelaId);
    return parsed ? parsed.letter : null;
}

/**
 * Get color for BINGO letter
 * @param {string} letter - B, I, N, G, O
 * @returns {string}
 */
function getBingoColor(letter) {
    const colors = {
        'B': '#ff6b6b', // Red
        'I': '#4ecdc4', // Teal
        'N': '#45b7d1', // Blue
        'G': '#96ceb4', // Green
        'O': '#ffeaa7'  // Yellow
    };
    return colors[letter] || '#ddd';
}

/**
 * Format time in seconds to MM:SS
 * @param {number} seconds
 * @returns {string}
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Calculate reward pool
 * @param {number} selectedCartelas
 * @param {number} winPercentage
 * @returns {object}
 */
function calculateRewardPool(selectedCartelas, winPercentage = config.DEFAULT_WIN_PERCENTAGE) {
    const totalBet = selectedCartelas * config.BET_AMOUNT;
    const winnerReward = (totalBet * winPercentage) / 100;
    const adminCommission = totalBet - winnerReward;
    return { totalBet, winnerReward, adminCommission };
}

/**
 * Set total cartela variations (loaded from file)
 * @param {number} count
 */
function setTotalCartelaVariations(count) {
    TOTAL_CARTELA_VARIATIONS = count;
}

/**
 * Get total cartela variations
 * @returns {number}
 */
function getTotalCartelaVariations() {
    return TOTAL_CARTELA_VARIATIONS;
}

// ==================== CONFIGURATION SUMMARY ====================
if (config.IS_DEVELOPMENT) {
    console.log(`
╔═══════════════════════════════════════════════════════════════════════════╗
║                    🎲 ESTIF BINGO 24/7 - CONFIGURATION                     ║
╠═══════════════════════════════════════════════════════════════════════════╣
║  Environment:     ${config.NODE_ENV.padEnd(40)}║
║  Port:            ${config.PORT.toString().padEnd(40)}║
║  Database:        ${config.DATABASE_URL ? "✅ Configured".padEnd(40) : "❌ Missing".padEnd(40)}║
║  Bot API URL:     ${config.BOT_API_URL ? "✅ Configured".padEnd(40) : "❌ Missing".padEnd(40)}║
╠═══════════════════════════════════════════════════════════════════════════╣
║  📊 CARTELA CONFIGURATION                                                 ║
║  Cartela Types:   ${config.TOTAL_CARTELA_TYPES} (B1-B15, I16-I30, N31-N45, G46-G60, O61-O75)${" ".repeat(20)}║
║  B Range:         B1 - B15 (15 types)${" ".repeat(40)}║
║  I Range:         I16 - I30 (15 types)${" ".repeat(39)}║
║  N Range:         N31 - N45 (15 types)${" ".repeat(39)}║
║  G Range:         G46 - G60 (15 types)${" ".repeat(39)}║
║  O Range:         O61 - O75 (15 types)${" ".repeat(39)}║
╠═══════════════════════════════════════════════════════════════════════════╣
║  🎮 GAME SETTINGS                                                         ║
║  Max per Player:  ${config.MAX_CARTELAS} cartelas${" ".repeat(37)}║
║  Bet Amount:      ${config.BET_AMOUNT} ETB${" ".repeat(40 - config.BET_AMOUNT.toString().length)}║
║  Selection Time:  ${config.SELECTION_TIME} seconds${" ".repeat(39 - config.SELECTION_TIME.toString().length)}║
║  Draw Interval:   ${config.DRAW_INTERVAL / 1000} seconds${" ".repeat(40 - (config.DRAW_INTERVAL / 1000).toString().length)}║
║  Win Percentages: ${config.WIN_PERCENTAGES.join(", ")}${" ".repeat(40 - config.WIN_PERCENTAGES.join(", ").length)}║
╚═══════════════════════════════════════════════════════════════════════════╝
    `);
}

// ==================== EXPORTS ====================
module.exports = {
    config,
    corsOptions,
    parseCartelaId,
    isValidCartelaId,
    getCartelaIndex,
    getBingoLetterForNumber,
    getBingoLetterForCartela,
    getBingoColor,
    formatTime,
    calculateRewardPool,
    setTotalCartelaVariations,
    getTotalCartelaVariations,
    ALL_CARTELA_IDS,
    BINGO_LETTERS
};