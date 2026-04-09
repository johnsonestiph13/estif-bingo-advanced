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
            styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://fonts.gstatic.com"],
            fontSrc: ["'self'", "https://fonts.gstatic.com", "data:"],
            scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.socket.io"],
            imgSrc: ["'self'", "data:", "https:", "blob:"],
            connectSrc: ["'self'", config.BOT_API_URL, "wss:", "https:", "ws:"],
            frameSrc: ["'none'"],
            objectSrc: ["'none'"],
            baseUri: ["'self'"],
            formAction: ["'self'"],
            upgradeInsecureRequests: [],
        },
    },
    crossOriginEmbedderPolicy: false, // Required for some CDNs
    crossOriginResourcePolicy: { policy: "cross-origin" }, // Allow sounds/assets
    crossOriginOpenerPolicy: { policy: "same-origin-allow-popups" },
    referrerPolicy: { policy: "strict-origin-when-cross-origin" },
    hsts: {
        maxAge: 31536000, // 1 year
        includeSubDomains: true,
        preload: true
    },
    noSniff: true,
    xssFilter: true,
    hidePoweredBy: true,
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
        .replace(/\//g, "&#x2F;")
        .replace(/`/g, "&#x60;")
        .replace(/=/g, "&#x3D;");
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

/**
 * Escape regex special characters
 */
function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ==================== REQUEST VALIDATION ====================

/**
 * Validate phone number format (Ethiopian format)
 */
function isValidPhone(phone) {
    const phoneRegex = /^(09|07)[0-9]{8}$/;
    return phoneRegex.test(phone);
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate amount (positive number, max 1,000,000)
 */
function isValidAmount(amount) {
    const num = parseFloat(amount);
    return !isNaN(num) && num > 0 && num <= 1000000 && Number.isFinite(num);
}

/**
 * Validate cartela ID (string format like "B1_001" or "O15_188")
 */
function isValidCartelaId(cartelaId, totalCartelas = 1000) {
    if (!cartelaId || typeof cartelaId !== "string") return false;
    
    // Pattern: Letter + Number + _ + 3-digit variation
    // Examples: B1_001, I16_002, N31_003, G46_004, O61_005, O15_188
    const cartelaRegex = /^[BINGO]\d+_\d{3}$/;
    
    if (!cartelaRegex.test(cartelaId)) return false;
    
    // Extract letter and number
    const letter = cartelaId.charAt(0);
    const numberMatch = cartelaId.match(/\d+/);
    const number = numberMatch ? parseInt(numberMatch[0]) : 0;
    
    // Validate number range based on letter
    const ranges = {
        'B': { min: 1, max: 15 },
        'I': { min: 16, max: 30 },
        'N': { min: 31, max: 45 },
        'G': { min: 46, max: 60 },
        'O': { min: 61, max: 75 }
    };
    
    const range = ranges[letter];
    if (!range) return false;
    
    return number >= range.min && number <= range.max;
}

/**
 * Validate cartela number (backward compatibility - for integer IDs)
 */
function isValidCartelaNumber(num, totalCartelas = 1000) {
    const n = parseInt(num);
    return !isNaN(n) && n >= 1 && n <= totalCartelas;
}

/**
 * Validate round number
 */
function isValidRoundNumber(num) {
    const n = parseInt(num);
    return !isNaN(n) && n >= 1 && n <= 999999;
}

/**
 * Validate win percentage
 */
function isValidWinPercentage(percentage) {
    const allowed = [70, 75, 76, 80];
    return allowed.includes(percentage);
}

/**
 * Validate username (alphanumeric, 3-20 chars)
 */
function isValidUsername(username) {
    if (!username || typeof username !== "string") return false;
    const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
    return usernameRegex.test(username);
}

/**
 * Validate JWT token format
 */
function isValidJwtToken(token) {
    if (!token || typeof token !== "string") return false;
    // Basic JWT format check: header.payload.signature
    const jwtRegex = /^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$/;
    return jwtRegex.test(token);
}

// ==================== RATE LIMIT HEADERS ====================

/**
 * Add security headers to response
 */
function addSecurityHeaders(req, res, next) {
    res.setHeader("X-Content-Type-Options", "nosniff");
    res.setHeader("X-Frame-Options", "DENY");
    res.setHeader("X-XSS-Protection", "1; mode=block");
    res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
    res.setHeader("Permissions-Policy", "geolocation=(), microphone=(), camera=()");
    next();
}

// ==================== REQUEST LOGGING (Security) ====================

/**
 * Suspicious patterns for attack detection
 */
const suspiciousPatterns = [
    /(%3C|<)script(%3E|>)/i,           // XSS attempts
    /(%27|')?(or|and|union|select|insert|drop|delete|update|alter|create|exec|execute)\s/i, // SQLi
    /\.\.\/|\.\.\\/,                    // Path traversal
    /\/etc\/passwd/i,                   // System file access
    /(\$|%24)\{.*\}/i,                  // Command injection
    /(eval\(|system\(|exec\(|passthru\()/i, // Code execution
    /(0x[0-9A-Fa-f]+)/i,               // Hex encoding
    /(char\(|chr\(|ord\()/i,           // Character functions
];

/**
 * Check if request contains suspicious patterns
 */
function isSuspiciousRequest(req) {
    const checkString = `${req.method} ${req.url} ${JSON.stringify(req.body || {})} ${JSON.stringify(req.query || {})}`;
    
    for (const pattern of suspiciousPatterns) {
        if (pattern.test(checkString)) {
            return true;
        }
    }
    return false;
}

/**
 * Security logging middleware
 */
function securityLogging(req, res, next) {
    if (isSuspiciousRequest(req)) {
        console.warn(`⚠️ Suspicious request detected: ${req.method} ${req.url} from ${req.ip} - ${new Date().toISOString()}`);
        
        // Optional: block suspicious requests in production
        if (config.IS_PRODUCTION) {
            return res.status(403).json({ 
                success: false, 
                message: "Request blocked for security reasons",
                code: "SECURITY_BLOCKED"
            });
        }
    }
    next();
}

// ==================== IP WHITELISTING ====================

/**
 * IP whitelist middleware for sensitive endpoints
 * Only allows requests from specified IPs
 */
function ipWhitelist(allowedIps) {
    return (req, res, next) => {
        const clientIp = req.ip || req.connection?.remoteAddress || req.socket?.remoteAddress;
        
        // Remove IPv6 prefix if present
        const cleanIp = clientIp?.replace(/^::ffff:/, "") || "";
        
        if (allowedIps.includes(cleanIp) || allowedIps.includes("*")) {
            next();
        } else {
            console.warn(`🔒 Blocked request from non-whitelisted IP: ${cleanIp} to ${req.url}`);
            res.status(403).json({ 
                success: false, 
                message: "Access denied",
                code: "IP_NOT_WHITELISTED"
            });
        }
    };
}

// ==================== RATE LIMITING HELPERS ====================

/**
 * Generate a unique fingerprint for rate limiting
 * Combines IP, User-Agent, and optionally user ID
 */
function generateFingerprint(req, userId = null) {
    const ip = req.ip || req.connection?.remoteAddress || "";
    const userAgent = req.headers['user-agent'] || "";
    const fingerprint = `${ip}:${userAgent.substring(0, 50)}`;
    
    return userId ? `${userId}:${fingerprint}` : fingerprint;
}

// ==================== REQUEST SIZE LIMITING ====================

/**
 * Limit request body size
 */
const bodySizeLimiter = (maxSize = '1mb') => {
    return (req, res, next) => {
        const contentLength = parseInt(req.headers['content-length'] || '0');
        const maxBytes = parseSize(maxSize);
        
        if (contentLength > maxBytes) {
            return res.status(413).json({
                success: false,
                message: `Request body too large. Max size: ${maxSize}`,
                code: "PAYLOAD_TOO_LARGE"
            });
        }
        next();
    };
};

/**
 * Parse size string to bytes (e.g., '1mb' -> 1048576)
 */
function parseSize(sizeStr) {
    const units = {
        'b': 1,
        'kb': 1024,
        'mb': 1024 * 1024,
        'gb': 1024 * 1024 * 1024
    };
    
    const match = sizeStr.match(/^(\d+)(b|kb|mb|gb)$/i);
    if (!match) return parseInt(sizeStr) || 1024 * 1024;
    
    const value = parseInt(match[1]);
    const unit = match[2].toLowerCase();
    
    return value * (units[unit] || 1);
}

// ==================== EXPORTS ====================
module.exports = {
    // Helmet middleware
    helmetMiddleware,
    
    // Input sanitization
    sanitizeInput,
    sanitizeObject,
    escapeRegex,
    
    // Validation
    isValidPhone,
    isValidEmail,
    isValidAmount,
    isValidCartelaId,
    isValidCartelaNumber,
    isValidRoundNumber,
    isValidWinPercentage,
    isValidUsername,
    isValidJwtToken,
    
    // Security headers
    addSecurityHeaders,
    
    // Security logging
    securityLogging,
    isSuspiciousRequest,
    
    // IP whitelisting
    ipWhitelist,
    
    // Rate limiting helpers
    generateFingerprint,
    
    // Request size limiting
    bodySizeLimiter,
    parseSize,
};