// game-server/src/utils/logger.js

const fs = require("fs");
const path = require("path");
const { config } = require("../config");

// ==================== LOG LEVELS ====================

const LOG_LEVELS = {
    ERROR: 0,
    WARN: 1,
    INFO: 2,
    DEBUG: 3,
    TRACE: 4
};

const LOG_LEVEL_NAMES = {
    0: "ERROR",
    1: "WARN",
    2: "INFO",
    3: "DEBUG",
    4: "TRACE"
};

// Current log level from environment or default to INFO in production, DEBUG in development
const currentLogLevel = LOG_LEVELS[process.env.LOG_LEVEL?.toUpperCase() || (config.IS_PRODUCTION ? "INFO" : "DEBUG")];

// ==================== LOG FILE CONFIGURATION ====================

const LOG_DIR = path.join(__dirname, "../../logs");
const MAX_LOG_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_LOG_FILES = 5;

// Ensure log directory exists
if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
}

// ==================== LOG ROTATION ====================

function rotateLogFile(logFilePath) {
    try {
        if (fs.existsSync(logFilePath)) {
            const stats = fs.statSync(logFilePath);
            if (stats.size >= MAX_LOG_SIZE) {
                // Rotate files
                for (let i = MAX_LOG_FILES - 1; i >= 1; i--) {
                    const oldPath = `${logFilePath}.${i}`;
                    const newPath = `${logFilePath}.${i + 1}`;
                    if (fs.existsSync(oldPath)) {
                        fs.renameSync(oldPath, newPath);
                    }
                }
                fs.renameSync(logFilePath, `${logFilePath}.1`);
                console.log(`📋 Log rotated: ${path.basename(logFilePath)}`);
            }
        }
    } catch (err) {
        console.error("Log rotation error:", err);
    }
}

// ==================== FILE WRITING ====================

function writeToFile(level, message, meta = {}) {
    if (!config.LOG_TO_FILE) return;
    
    try {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level: LOG_LEVEL_NAMES[level],
            message,
            ...meta
        };
        
        const logLine = JSON.stringify(logEntry) + "\n";
        
        // Write to main log file
        const mainLogPath = path.join(LOG_DIR, "game-server.log");
        rotateLogFile(mainLogPath);
        fs.appendFileSync(mainLogPath, logLine, "utf8");
        
        // Write to level-specific log file
        const levelLogPath = path.join(LOG_DIR, `${LOG_LEVEL_NAMES[level].toLowerCase()}.log`);
        fs.appendFileSync(levelLogPath, logLine, "utf8");
    } catch (err) {
        console.error("Failed to write to log file:", err);
    }
}

// ==================== CONSOLE OUTPUT ====================

function formatConsoleMessage(level, message, meta = {}) {
    const timestamp = new Date().toISOString().slice(11, 23);
    const levelName = LOG_LEVEL_NAMES[level];
    let color = "\x1b[0m"; // reset
    
    switch (levelName) {
        case "ERROR":
            color = "\x1b[31m"; // red
            break;
        case "WARN":
            color = "\x1b[33m"; // yellow
            break;
        case "INFO":
            color = "\x1b[36m"; // cyan
            break;
        case "DEBUG":
            color = "\x1b[35m"; // magenta
            break;
        case "TRACE":
            color = "\x1b[90m"; // gray
            break;
    }
    
    let consoleMessage = `${color}[${timestamp}] ${levelName}: ${message}\x1b[0m`;
    
    if (Object.keys(meta).length > 0) {
        // Format meta nicely
        const metaStr = Object.entries(meta)
            .map(([k, v]) => {
                if (typeof v === 'object') return `${k}=${JSON.stringify(v)}`;
                return `${k}=${v}`;
            })
            .join(' ');
        consoleMessage += ` \x1b[90m${metaStr}\x1b[0m`;
    }
    
    return consoleMessage;
}

// ==================== PUBLIC LOGGING METHODS ====================

/**
 * Log error message
 * @param {string} message - Log message
 * @param {object} meta - Additional metadata
 */
function error(message, meta = {}) {
    if (currentLogLevel >= LOG_LEVELS.ERROR) {
        console.error(formatConsoleMessage(LOG_LEVELS.ERROR, message, meta));
        writeToFile(LOG_LEVELS.ERROR, message, meta);
    }
}

/**
 * Log warning message
 * @param {string} message - Log message
 * @param {object} meta - Additional metadata
 */
function warn(message, meta = {}) {
    if (currentLogLevel >= LOG_LEVELS.WARN) {
        console.warn(formatConsoleMessage(LOG_LEVELS.WARN, message, meta));
        writeToFile(LOG_LEVELS.WARN, message, meta);
    }
}

/**
 * Log info message
 * @param {string} message - Log message
 * @param {object} meta - Additional metadata
 */
function info(message, meta = {}) {
    if (currentLogLevel >= LOG_LEVELS.INFO) {
        console.log(formatConsoleMessage(LOG_LEVELS.INFO, message, meta));
        writeToFile(LOG_LEVELS.INFO, message, meta);
    }
}

/**
 * Log debug message
 * @param {string} message - Log message
 * @param {object} meta - Additional metadata
 */
function debug(message, meta = {}) {
    if (currentLogLevel >= LOG_LEVELS.DEBUG) {
        console.debug(formatConsoleMessage(LOG_LEVELS.DEBUG, message, meta));
        writeToFile(LOG_LEVELS.DEBUG, message, meta);
    }
}

/**
 * Log trace message (most verbose)
 * @param {string} message - Log message
 * @param {object} meta - Additional metadata
 */
function trace(message, meta = {}) {
    if (currentLogLevel >= LOG_LEVELS.TRACE) {
        console.trace(formatConsoleMessage(LOG_LEVELS.TRACE, message, meta));
        writeToFile(LOG_LEVELS.TRACE, message, meta);
    }
}

// ==================== REQUEST LOGGING MIDDLEWARE ====================

/**
 * Express middleware for logging HTTP requests
 */
function requestLogger(req, res, next) {
    const start = Date.now();
    
    res.on("finish", () => {
        const duration = Date.now() - start;
        const meta = {
            method: req.method,
            url: req.url,
            status: res.statusCode,
            duration: `${duration}ms`,
            ip: req.ip || req.socket?.remoteAddress,
            userAgent: req.get("user-agent")?.substring(0, 100)
        };
        
        if (res.statusCode >= 500) {
            error(`HTTP ${res.statusCode}: ${req.method} ${req.url}`, meta);
        } else if (res.statusCode >= 400) {
            warn(`HTTP ${res.statusCode}: ${req.method} ${req.url}`, meta);
        } else {
            debug(`HTTP ${res.statusCode}: ${req.method} ${req.url}`, meta);
        }
    });
    
    next();
}

/**
 * Log socket events
 * @param {string} event - Event name
 * @param {string} socketId - Socket ID
 * @param {object} data - Event data (optional)
 */
function logSocketEvent(event, socketId, data = null) {
    const meta = { socketId, event };
    if (data) {
        // Don't log sensitive data
        const safeData = { ...data };
        if (safeData.token) safeData.token = "[REDACTED]";
        if (safeData.password) safeData.password = "[REDACTED]";
        meta.data = safeData;
    }
    debug(`Socket event: ${event}`, meta);
}

// ==================== GAME-SPECIFIC LOGGING ====================

/**
 * Log game action
 * @param {string} action - Action name
 * @param {object} details - Action details
 */
function logGameAction(action, details = {}) {
    const meta = { action, ...details };
    info(`Game action: ${action}`, meta);
}

/**
 * Log cartela selection
 * @param {string} cartelaId - Cartela ID (e.g., "B1_001")
 * @param {number} telegramId - User's Telegram ID
 * @param {string} username - User's username
 * @param {number} round - Round number
 */
function logCartelaSelection(cartelaId, telegramId, username, round) {
    info(`Cartela selected: ${cartelaId}`, {
        cartelaId,
        telegramId,
        username,
        round,
        action: "select_cartela"
    });
}

/**
 * Log cartela deselection
 * @param {string} cartelaId - Cartela ID (e.g., "B1_001")
 * @param {number} telegramId - User's Telegram ID
 * @param {string} username - User's username
 * @param {number} round - Round number
 */
function logCartelaDeselection(cartelaId, telegramId, username, round) {
    info(`Cartela deselected: ${cartelaId}`, {
        cartelaId,
        telegramId,
        username,
        round,
        action: "deselect_cartela"
    });
}

/**
 * Log winner
 * @param {string} cartelaId - Winning cartela ID
 * @param {number} telegramId - Winner's Telegram ID
 * @param {string} username - Winner's username
 * @param {number} amount - Winning amount
 * @param {number} round - Round number
 * @param {string[]} winningLines - Winning lines
 */
function logWinner(cartelaId, telegramId, username, amount, round, winningLines) {
    info(`🏆 WINNER: ${username} won ${amount} ETB with cartela ${cartelaId}`, {
        cartelaId,
        telegramId,
        username,
        amount,
        round,
        winningLines,
        action: "winner"
    });
}

/**
 * Log round start
 * @param {number} round - Round number
 * @param {number} totalCartelas - Total cartelas selected
 * @param {number} totalBet - Total bet amount
 * @param {number} prizePool - Prize pool amount
 */
function logRoundStart(round, totalCartelas, totalBet, prizePool) {
    info(`Round ${round} started`, {
        round,
        totalCartelas,
        totalBet,
        prizePool,
        winPercentage: config.DEFAULT_WIN_PERCENTAGE,
        action: "round_start"
    });
}

/**
 * Log round end
 * @param {number} round - Round number
 * @param {number} winnerCount - Number of winners
 * @param {number} totalPayout - Total payout amount
 * @param {number} commission - Commission amount
 */
function logRoundEnd(round, winnerCount, totalPayout, commission) {
    info(`Round ${round} ended`, {
        round,
        winnerCount,
        totalPayout,
        commission,
        action: "round_end"
    });
}

/**
 * Log number drawn
 * @param {number} number - Drawn number
 * @param {number} round - Round number
 * @param {number} drawnCount - Total drawn count
 */
function logNumberDrawn(number, round, drawnCount) {
    const letter = number <= 15 ? 'B' : number <= 30 ? 'I' : number <= 45 ? 'N' : number <= 60 ? 'G' : 'O';
    trace(`Number drawn: ${letter}${number}`, {
        number,
        letter,
        round,
        drawnCount,
        action: "number_drawn"
    });
}

/**
 * Log admin action
 * @param {string} adminEmail - Admin email
 * @param {string} action - Action performed
 * @param {object} details - Action details
 */
function logAdminAction(adminEmail, action, details = {}) {
    info(`Admin action: ${action} by ${adminEmail}`, {
        adminEmail,
        action,
        ...details,
        type: "admin_action"
    });
}

/**
 * Log balance change
 * @param {number} telegramId - User's Telegram ID
 * @param {string} username - User's username
 * @param {number} amount - Amount changed
 * @param {number} newBalance - New balance
 * @param {string} reason - Reason for change
 */
function logBalanceChange(telegramId, username, amount, newBalance, reason) {
    const changeType = amount >= 0 ? "add" : "deduct";
    info(`Balance ${changeType}: ${username} ${amount >= 0 ? '+' : ''}${amount} ETB`, {
        telegramId,
        username,
        amount,
        newBalance,
        reason,
        action: "balance_change"
    });
}

// ==================== PERFORMANCE LOGGING ====================

/**
 * Measure and log execution time of an async function
 * @param {string} name - Operation name
 * @param {Function} fn - Async function to measure
 * @returns {Promise<any>} - Result of the function
 */
async function measureTime(name, fn) {
    const start = Date.now();
    try {
        const result = await fn();
        const duration = Date.now() - start;
        debug(`Performance: ${name} took ${duration}ms`);
        return result;
    } catch (err) {
        const duration = Date.now() - start;
        error(`Performance error in ${name} after ${duration}ms: ${err.message}`);
        throw err;
    }
}

/**
 * Log memory usage
 */
function logMemoryUsage() {
    const usage = process.memoryUsage();
    debug("Memory usage", {
        rss: `${Math.round(usage.rss / 1024 / 1024)} MB`,
        heapTotal: `${Math.round(usage.heapTotal / 1024 / 1024)} MB`,
        heapUsed: `${Math.round(usage.heapUsed / 1024 / 1024)} MB`,
        external: `${Math.round(usage.external / 1024 / 1024)} MB`
    });
}

// ==================== STARTUP LOGGING ====================

/**
 * Log server startup information
 */
function logStartup() {
    info("🚀 Estif Bingo 24/7 Server Starting", {
        version: "3.0.0",
        nodeVersion: process.version,
        environment: config.NODE_ENV,
        logLevel: LOG_LEVEL_NAMES[currentLogLevel],
        totalCartelas: config.TOTAL_CARTELAS,
        maxCartelasPerPlayer: config.MAX_CARTELAS,
        betAmount: config.BET_AMOUNT,
        selectionTime: config.SELECTION_TIME,
        drawInterval: config.DRAW_INTERVAL
    });
}

/**
 * Log shutdown information
 */
function logShutdown() {
    info("🛑 Estif Bingo 24/7 Server Shutting Down", {
        timestamp: new Date().toISOString()
    });
}

// ==================== EXPORTS ====================

module.exports = {
    // Core logging
    error,
    warn,
    info,
    debug,
    trace,
    
    // Middleware
    requestLogger,
    
    // Socket logging
    logSocketEvent,
    
    // Game-specific logging
    logGameAction,
    logCartelaSelection,
    logCartelaDeselection,
    logWinner,
    logRoundStart,
    logRoundEnd,
    logNumberDrawn,
    logAdminAction,
    logBalanceChange,
    
    // Performance logging
    measureTime,
    logMemoryUsage,
    
    // Startup/shutdown
    logStartup,
    logShutdown,
    
    // Constants
    LOG_LEVELS
};