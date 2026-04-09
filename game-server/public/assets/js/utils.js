// assets/js/utils.js - Complete Shared Utility Functions
// Estif Bingo 24/7 - Production Utilities

/**
 * Format seconds to MM:SS or SS (for countdown)
 * @param {number} seconds - Seconds to format
 * @param {boolean} showMinutes - Whether to show minutes
 * @returns {string} Formatted time string
 */
function formatTime(seconds, showMinutes = true) {
    if (isNaN(seconds)) return '0:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    
    if (showMinutes && mins > 0) {
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    return `${secs}`;
}

/**
 * Format number with ETB currency
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
    return `${amount.toFixed(2)} ETB`;
}

/**
 * Format large numbers with K, M suffixes
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * Get BINGO letter for a number (1-75)
 * @param {number} number - Number from 1-75
 * @returns {string} B, I, N, G, or O
 */
function getBingoLetter(number) {
    if (number <= 15) return 'B';
    if (number <= 30) return 'I';
    if (number <= 45) return 'N';
    if (number <= 60) return 'G';
    return 'O';
}

/**
 * Get BINGO letter color
 * @param {string} letter - B, I, N, G, O
 * @returns {string} CSS color code
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
 * Get cartela ID range based on BINGO letter
 * @param {string} letter - B, I, N, G, O
 * @returns {object} { start, end, count }
 */
function getCartelaRange(letter) {
    const ranges = {
        'B': { start: 1, end: 200, count: 200 },
        'I': { start: 201, end: 400, count: 200 },
        'N': { start: 401, end: 600, count: 200 },
        'G': { start: 601, end: 800, count: 200 },
        'O': { start: 801, end: 1000, count: 200 }
    };
    return ranges[letter] || ranges['B'];
}

/**
 * Show temporary message with animation
 * @param {string} message - Message to display
 * @param {string} type - 'info', 'success', 'warning', 'error'
 * @param {number} duration - Duration in milliseconds
 */
function showMessage(message, type = 'info', duration = 3000) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.toast-message');
    existingMessages.forEach(msg => msg.remove());
    
    const toast = document.createElement('div');
    toast.className = `toast-message toast-${type}`;
    
    // Add icon based on type
    const icons = {
        info: 'ℹ️',
        success: '✅',
        warning: '⚠️',
        error: '❌'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">${message}</div>
        <div class="toast-progress"></div>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Animate out
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Show loading spinner
 * @param {string} message - Optional loading message
 * @returns {HTMLElement} Loading element reference
 */
function showLoading(message = 'Loading...') {
    let loader = document.getElementById('global-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'global-loader';
        loader.className = 'global-loader';
        document.body.appendChild(loader);
    }
    
    loader.innerHTML = `
        <div class="loader-content">
            <div class="spinner"></div>
            <div class="loader-message">${message}</div>
        </div>
    `;
    
    loader.style.display = 'flex';
    return loader;
}

/**
 * Hide loading spinner
 */
function hideLoading() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.style.display = 'none';
    }
}

/**
 * Debounce function to limit rapid calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function to limit call rate
 * @param {Function} func - Function to throttle
 * @param {number} limit - Limit in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Get query parameter from URL
 * @param {string} param - Parameter name
 * @returns {string|null} Parameter value or null
 */
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

/**
 * Set query parameter without page reload
 * @param {string} param - Parameter name
 * @param {string} value - Parameter value
 */
function setQueryParam(param, value) {
    const url = new URL(window.location.href);
    url.searchParams.set(param, value);
    window.history.replaceState({}, '', url);
}

/**
 * Safe JSON parse with error handling
 * @param {string} str - JSON string to parse
 * @param {any} defaultValue - Default value if parse fails
 * @returns {any} Parsed object or default value
 */
function safeJSONParse(str, defaultValue = null) {
    try {
        return JSON.parse(str);
    } catch {
        return defaultValue;
    }
}

/**
 * Copy text to clipboard with fallback
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showMessage('Copied to clipboard!', 'success', 1500);
        return true;
    } catch {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showMessage('Copied to clipboard!', 'success', 1500);
        return true;
    }
}

/**
 * LocalStorage wrapper with error handling
 */
const storage = {
    get(key, defaultValue = null) {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : defaultValue;
        } catch {
            return defaultValue;
        }
    },
    
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch {
            return false;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch {
            return false;
        }
    },
    
    clear() {
        try {
            localStorage.clear();
            return true;
        } catch {
            return false;
        }
    }
};

/**
 * SessionStorage wrapper
 */
const session = {
    get(key, defaultValue = null) {
        try {
            const value = sessionStorage.getItem(key);
            return value ? JSON.parse(value) : defaultValue;
        } catch {
            return defaultValue;
        }
    },
    
    set(key, value) {
        try {
            sessionStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch {
            return false;
        }
    },
    
    remove(key) {
        try {
            sessionStorage.removeItem(key);
            return true;
        } catch {
            return false;
        }
    }
};

/**
 * Detect if device is mobile
 * @returns {boolean}
 */
function isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * Detect if device is touch-enabled
 * @returns {boolean}
 */
function isTouchDevice() {
    return ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
}

/**
 * Get device info for analytics
 * @returns {object}
 */
function getDeviceInfo() {
    return {
        isMobile: isMobile(),
        isTouch: isTouchDevice(),
        userAgent: navigator.userAgent,
        language: navigator.language,
        platform: navigator.platform,
        screenSize: `${window.screen.width}x${window.screen.height}`
    };
}

/**
 * Shuffle array (Fisher-Yates)
 * @param {Array} array - Array to shuffle
 * @returns {Array} Shuffled array
 */
function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

/**
 * Generate random number between min and max (inclusive)
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number} Random number
 */
function randomRange(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Format date for display
 * @param {Date|string} date - Date to format
 * @param {boolean} includeTime - Whether to include time
 * @returns {string} Formatted date string
 */
function formatDate(date, includeTime = false) {
    const d = new Date(date);
    if (isNaN(d.getTime())) return 'Invalid Date';
    
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }
    
    return d.toLocaleDateString(undefined, options);
}

/**
 * Truncate text with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, maxLength = 50) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + '...';
}

/**
 * Capitalize first letter of each word
 * @param {string} text - Text to capitalize
 * @returns {string} Capitalized text
 */
function capitalizeWords(text) {
    if (!text) return '';
    return text.split(' ').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ');
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean}
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate phone number (Ethiopian format)
 * @param {string} phone - Phone number to validate
 * @returns {boolean}
 */
function isValidPhone(phone) {
    const re = /^09[0-9]{8}$/;
    return re.test(phone);
}

/**
 * Get color based on balance amount
 * @param {number} balance - User balance
 * @returns {string} CSS color
 */
function getBalanceColor(balance) {
    if (balance >= 100) return '#4caf50';
    if (balance >= 50) return '#8bc34a';
    if (balance >= 10) return '#ffc107';
    return '#f44336';
}

/**
 * Create and download a file
 * @param {string} content - File content
 * @param {string} filename - File name
 * @param {string} type - MIME type
 */
function downloadFile(content, filename, type = 'text/plain') {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Export data as CSV
 * @param {Array} data - Array of objects
 * @param {string} filename - File name
 */
function exportToCSV(data, filename = 'export.csv') {
    if (!data || data.length === 0) {
        showMessage('No data to export', 'warning');
        return;
    }
    
    const headers = Object.keys(data[0]);
    const csvRows = [];
    
    csvRows.push(headers.join(','));
    
    for (const row of data) {
        const values = headers.map(header => {
            const value = row[header] || '';
            return `"${String(value).replace(/"/g, '""')}"`;
        });
        csvRows.push(values.join(','));
    }
    
    downloadFile(csvRows.join('\n'), filename, 'text/csv');
    showMessage('Export completed!', 'success', 2000);
}

/**
 * Add CSS class to body for device detection
 */
function addDeviceClass() {
    if (isMobile()) {
        document.body.classList.add('mobile-device');
    }
    if (isTouchDevice()) {
        document.body.classList.add('touch-device');
    }
}

/**
 * Initialize all utils on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    addDeviceClass();
});

// Export for use in other files (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatTime,
        formatCurrency,
        formatNumber,
        getBingoLetter,
        getBingoColor,
        getCartelaRange,
        showMessage,
        showLoading,
        hideLoading,
        debounce,
        throttle,
        getQueryParam,
        setQueryParam,
        safeJSONParse,
        copyToClipboard,
        storage,
        session,
        isMobile,
        isTouchDevice,
        getDeviceInfo,
        shuffleArray,
        randomRange,
        formatDate,
        truncateText,
        capitalizeWords,
        isValidEmail,
        isValidPhone,
        getBalanceColor,
        downloadFile,
        exportToCSV
    };
}