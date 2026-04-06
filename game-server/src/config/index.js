// game-server/src/config/index.js

const dotenv = require("dotenv");
const path = require("path");

// Load environment variables from .env file (if exists)
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

// ==================== SERVER CONFIG ====================
const config = {
    // Server
    PORT: parseInt(process.env.PORT, 10) || 3000,
    NODE_ENV: process.env.NODE_ENV || "development",
    IS_PRODUCTION: process.env.NODE_ENV === "production",

    // Database (game server)
    DATABASE_URL: process.env.DATABASE_URL,
    DB_POOL_MAX: parseInt(process.env.DB_POOL_MAX, 10) || 20,
    DB_IDLE_TIMEOUT: parseInt(process.env.DB_IDLE_TIMEOUT, 10) || 30000,
    DB_CONNECTION_TIMEOUT: parseInt(process.env.DB_CONNECTION_TIMEOUT, 10) || 5000,

    // Security
    JWT_SECRET: process.env.JWT_SECRET,
    API_SECRET: process.env.API_SECRET,
    JWT_EXPIRY: process.env.JWT_EXPIRY || "2h",
    ADMIN_EMAIL: process.env.ADMIN_EMAIL || "admin@estif.com",
    // Admin password hash – must be set in env for production
    ADMIN_PASSWORD_HASH: process.env.ADMIN_PASSWORD_HASH,

    // Bot API
    BOT_API_URL: process.env.BOT_API_URL,
    BOT_API_TIMEOUT: parseInt(process.env.BOT_API_TIMEOUT, 10) || 5000,
    BOT_API_RETRIES: parseInt(process.env.BOT_API_RETRIES, 10) || 3,

    // Game constants
    SELECTION_TIME: parseInt(process.env.SELECTION_TIME, 10) || 50,
    DRAW_INTERVAL: parseInt(process.env.DRAW_INTERVAL, 10) || 4000,
    NEXT_ROUND_DELAY: parseInt(process.env.NEXT_ROUND_DELAY, 10) || 6000,
    BET_AMOUNT: parseFloat(process.env.BET_AMOUNT) || 10,
    MAX_CARTELAS: parseInt(process.env.MAX_CARTELAS, 10) || 2,
    TOTAL_CARTELAS: parseInt(process.env.TOTAL_CARTELAS, 10) || 400,
    WIN_PERCENTAGES: [70, 75, 76, 80],
    DEFAULT_WIN_PERCENTAGE: 75,

    // Sound packs (client-side, but server serves the files)
    SOUND_PACKS: ["pack1", "pack2", "pack3", "pack4"],
    DEFAULT_SOUND_PACK: "pack1",

    // CORS – restrict in production
    CORS_ORIGINS: process.env.CORS_ORIGINS
        ? process.env.CORS_ORIGINS.split(",")
        : (process.env.NODE_ENV === "production"
            ? ["https://estif-bingo-247.onrender.com", "https://yourdomain.com"]
            : ["http://localhost:3000", "http://localhost:8080", "https://estif-bingo-247.onrender.com"]),

    // Rate limiting
    RATE_LIMIT_WINDOW_MS: parseInt(process.env.RATE_LIMIT_WINDOW_MS, 10) || 15 * 60 * 1000,
    RATE_LIMIT_MAX: parseInt(process.env.RATE_LIMIT_MAX, 10) || 100,
    AUTH_RATE_LIMIT_MAX: parseInt(process.env.AUTH_RATE_LIMIT_MAX, 10) || 5,

    // Paths
    PUBLIC_DIR: path.join(__dirname, "../../../public"),
    DATA_DIR: path.join(__dirname, "../../../data"),
    CARTELA_DATA_FILE: path.join(__dirname, "../../../data/cartelas.json"),
};

// ==================== CORS OPTIONS ====================
const corsOptions = {
    origin: function (origin, callback) {
        // Allow requests with no origin (like mobile apps or curl)
        if (!origin) return callback(null, true);
        if (config.CORS_ORIGINS.indexOf(origin) !== -1 || config.NODE_ENV !== "production") {
            callback(null, true);
        } else {
            callback(new Error("Not allowed by CORS"));
        }
    },
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization", "X-API-Key"],
};

// ==================== HELPER FUNCTIONS ====================
function validateWinPercentage(percentage) {
    return config.WIN_PERCENTAGES.includes(percentage);
}

function getWinPercentageOptions() {
    return [...config.WIN_PERCENTAGES];
}

function isValidCartelaNumber(number) {
    return number >= 1 && number <= config.TOTAL_CARTELAS;
}

// ==================== EXPORTS ====================
module.exports = {
    config,
    corsOptions,
    validateWinPercentage,
    getWinPercentageOptions,
    isValidCartelaNumber,
};