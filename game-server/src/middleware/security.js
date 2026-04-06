// game-server/src/middleware/security.js

const helmet = require("helmet");
const { config, corsOptions } = require("../config");

// ==================== HELMET CONFIGURATION ====================

/**
 * Helmet middleware for setting secure HTTP headers
 * Protects against common web vulnerabilities
 */
const helmetMiddleware = helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            fontSrc: ["'self'", "https://fonts.gstatic.com"],
            scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'", config.BOT_API_URL, "wss:", "https:"],
            frameSrc: ["'none'"],
            objectSrc: ["'none'"],
        },
    },
    crossOriginEmbedderPolicy: false, // Required for some CDNs
    crossOriginResourcePolicy: { policy: "cross-origin" }, // Allow sounds/assets
});

// ==================== INPUT SANITIZATION ====================

/**
 * Basic input sanitization to prevent XSS
 */
function sanitizeInput(str) {
    if (!str || typeof str !== "string") return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#x27;")
        .replace(/\//g, "&#x2F;");
}

/**
 * Sanitize all string fields in an object
 */
function sanitizeObject(obj) {
    if (!obj || typeof obj !== "object") return obj;
    
    const sanitized = {};
    for (const [key, value] of Object.entries(obj)) {
        if (typeof value === "string") {
            sanitized[key] = sanitizeInput(value);
        } else if (typeof value === "object" && value !== null) {
            sanitized[key] = sanitizeObject(value);
        } else {
            sanitized[key] = value;
        }
    }
    return sanitized;
}

// ==================== REQUEST VALIDATION ====================

/**
 * Validate phone number format
 */
function isValidPhone(phone) {
    const phoneRegex = /^[0-9+\-\s()]{8,15}$/;
    return phoneRegex.test(phone);
}

/**
 * Validate amount (positive number, max 1,000,000)
 */
function isValidAmount(amount) {
    const num = parseFloat(amount);
    return !isNaN(num) && num > 0 && num <= 1000000;
}

/**
 * Validate cartela number (1-400)
 */
function isValidCartelaNumber(num, totalCartelas = 400) {
    const n = parseInt(num);
    return !isNaN(n) && n >= 1 && n <= totalCartelas;
}

/**
 * Validate round number
 */
function isValidRoundNumber(num) {
    const n = parseInt(num);
    return !isNaN(n) && n >= 1;
}

// ==================== RATE LIMIT HEADERS ====================

/**
 * Add rate limit headers to response
 */
function addRateLimitHeaders(req, res, next) {
    res.setHeader("X-Content-Type-Options", "nosniff");
    res.setHeader("X-Frame-Options", "DENY");
    res.setHeader("X-XSS-Protection", "1; mode=block");
    next();
}

// ==================== REQUEST LOGGING (Security) ====================

/**
 * Log suspicious requests (potential attacks)
 */
const suspiciousPatterns = [
    /(%3C|<)script(%3E|>)/i,  // XSS attempts
    /(%27|')?(or|and|union|select|insert|drop|delete|update|alter|create|exec|execute) /i, // SQLi
    /\.\.\/|\.\.\\/, // Path traversal
];

function isSuspiciousRequest(req) {
    const checkString = `${req.method} ${req.url} ${JSON.stringify(req.body || {})} ${JSON.stringify(req.query || {})}`;
    
    for (const pattern of suspiciousPatterns) {
        if (pattern.test(checkString)) {
            return true;
        }
    }
    return false;
}

function securityLogging(req, res, next) {
    if (isSuspiciousRequest(req)) {
        console.warn(`⚠️ Suspicious request detected: ${req.method} ${req.url} from ${req.ip}`);
        // Optional: block suspicious requests
        // return res.status(403).json({ success: false, message: "Request blocked" });
    }
    next();
}

// ==================== IP WHITELISTING (Optional) ====================

/**
 * IP whitelist middleware for sensitive endpoints
 * Only allows requests from specified IPs
 */
function ipWhitelist(allowedIps) {
    return (req, res, next) => {
        const clientIp = req.ip || req.connection.remoteAddress;
        
        // Remove IPv6 prefix if present
        const cleanIp = clientIp.replace(/^::ffff:/, "");
        
        if (allowedIps.includes(cleanIp) || allowedIps.includes("*")) {
            next();
        } else {
            console.warn(`Blocked request from non-whitelisted IP: ${cleanIp}`);
            res.status(403).json({ success: false, message: "Access denied" });
        }
    };
}

// ==================== EXPORTS ====================
module.exports = {
    helmetMiddleware,
    sanitizeInput,
    sanitizeObject,
    isValidPhone,
    isValidAmount,
    isValidCartelaNumber,
    isValidRoundNumber,
    addRateLimitHeaders,
    securityLogging,
    ipWhitelist,
};