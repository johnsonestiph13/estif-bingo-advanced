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

const LOG_DIR = path.join(__dirname, "../../../logs");
const MAX_LOG_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_LOG_FILES = 5;

// Ensure log directory exists
if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
}

// ==================== LOG ROTATION ====================

function rotateLogFile(logFilePath) {
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
        }
    }
}

// ==================== FILE WRITING ====================

function writeToFile(level, message, meta = {}) {
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
        consoleMessage += ` ${JSON.stringify(meta)}`;
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
            ip: req.ip,
            userAgent: req.get("user-agent")
        };
        
        if (res.statusCode >= 500) {
            error(`HTTP ${res.statusCode}: ${req.method} ${req.url}`, meta);
        } else if (res.statusCode >= 400) {
            warn(`HTTP ${res.statusCode}: ${req.method} ${req.url}`, meta);
        } else {
            info(`HTTP ${res.statusCode}: ${req.method} ${req.url}`, meta);
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
        meta.data = safeData;
    }
    debug(`Socket event: ${event}`, meta);
}

/**
 * Log game action
 * @param {string} action - Action name
 * @param {object} details - Action details
 */
function logGameAction(action, details = {}) {
    const meta = { action, ...details };
    info(`Game action: ${action}`, meta);
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

// ==================== EXPORTS ====================

module.exports = {
    error,
    warn,
    info,
    debug,
    trace,
    requestLogger,
    logSocketEvent,
    logGameAction,
    measureTime,
    LOG_LEVELS
};