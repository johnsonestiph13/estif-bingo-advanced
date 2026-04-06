// game-server/src/game/cartela.js

const fs = require("fs");
const path = require("path");
const { config } = require("../config");

// ==================== CARTELA DATA CACHE ====================

let cartelaData = {};
const CARTELA_DATA_FILE = config.CARTELA_DATA_FILE;

// Ensure data directory exists
const dataDir = path.dirname(CARTELA_DATA_FILE);
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
}

// Load existing cartela data if available
try {
    if (fs.existsSync(CARTELA_DATA_FILE)) {
        cartelaData = JSON.parse(fs.readFileSync(CARTELA_DATA_FILE, "utf8"));
        console.log(`✅ Loaded ${Object.keys(cartelaData).length} cartelas from cache`);
    }
} catch (err) {
    console.log("⚠️ No cartela cache file found, will generate on demand");
}

// ==================== BINGO CARD GENERATION ====================

/**
 * Generate a random Bingo card (5x5 grid)
 * Follows standard Bingo rules:
 * - B: 1-15, I: 16-30, N: 31-45, G: 46-60, O: 61-75
 * - Center cell is "FREE"
 */
function generateRandomBingoCard() {
    const getRandomNumbers = (min, max, count) => {
        const nums = [];
        const available = [];
        for (let i = min; i <= max; i++) available.push(i);
        
        for (let i = 0; i < count; i++) {
            const idx = Math.floor(Math.random() * available.length);
            nums.push(available[idx]);
            available.splice(idx, 1);
        }
        return nums;
    };
    
    const b = getRandomNumbers(1, 15, 5);
    const i = getRandomNumbers(16, 30, 5);
    const n = getRandomNumbers(31, 45, 5);
    const g = getRandomNumbers(46, 60, 5);
    const o = getRandomNumbers(61, 75, 5);
    
    // Set center as FREE
    n[2] = "FREE";
    
    return [
        [b[0], i[0], n[0], g[0], o[0]],
        [b[1], i[1], n[1], g[1], o[1]],
        [b[2], i[2], n[2], g[2], o[2]],
        [b[3], i[3], n[3], g[3], o[3]],
        [b[4], i[4], n[4], g[4], o[4]]
    ];
}

// ==================== CARTELA GRID RETRIEVAL ====================

/**
 * Get cartela grid by ID (generates if not exists)
 */
function getCartelaGrid(cartelaId) {
    if (cartelaData[cartelaId]) {
        return cartelaData[cartelaId].grid;
    }
    
    const grid = generateRandomBingoCard();
    cartelaData[cartelaId] = {
        id: cartelaId,
        grid: grid,
        generatedAt: new Date().toISOString()
    };
    
    saveCartelaData();
    return grid;
}

/**
 * Save cartela data to JSON file (for persistence across restarts)
 */
function saveCartelaData() {
    try {
        fs.writeFileSync(CARTELA_DATA_FILE, JSON.stringify(cartelaData, null, 2));
        console.log(`💾 Saved ${Object.keys(cartelaData).length} cartelas to cache`);
    } catch (err) {
        console.error("❌ Failed to save cartela data:", err);
    }
}

/**
 * Get cartela metadata (without full grid)
 */
function getCartelaMetadata(cartelaId) {
    if (cartelaData[cartelaId]) {
        return {
            id: cartelaId,
            generatedAt: cartelaData[cartelaId].generatedAt
        };
    }
    return null;
}

// ==================== BINGO WIN DETECTION ====================

/**
 * Check if a cartela has Bingo with the given drawn numbers
 * Returns winning lines (rows, columns, diagonals)
 */
function checkBingoWin(cartelaId, drawnNumbers) {
    const grid = getCartelaGrid(cartelaId);
    if (!grid) return { won: false, winningLines: [] };
    
    const drawnSet = new Set(drawnNumbers);
    drawnSet.add("FREE"); // FREE space is always considered marked
    
    const winningLines = [];
    
    // Check rows
    for (let r = 0; r < 5; r++) {
        if (grid[r].every(cell => drawnSet.has(cell))) {
            winningLines.push(`Row ${r + 1}`);
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
        if (win) winningLines.push(`Column ${c + 1}`);
    }
    
    // Check main diagonal (top-left to bottom-right)
    let diag1 = true;
    for (let i = 0; i < 5; i++) {
        if (!drawnSet.has(grid[i][i])) {
            diag1 = false;
            break;
        }
    }
    if (diag1) winningLines.push("Diagonal ↘");
    
    // Check anti-diagonal (top-right to bottom-left)
    let diag2 = true;
    for (let i = 0; i < 5; i++) {
        if (!drawnSet.has(grid[i][4 - i])) {
            diag2 = false;
            break;
        }
    }
    if (diag2) winningLines.push("Diagonal ↙");
    
    return {
        won: winningLines.length > 0,
        winningLines: winningLines
    };
}

/**
 * Get the letter for a Bingo number (B, I, N, G, O)
 */
function getBingoLetter(number) {
    if (number <= 15) return "B";
    if (number <= 30) return "I";
    if (number <= 45) return "N";
    if (number <= 60) return "G";
    return "O";
}

/**
 * Format number with letter for display (e.g., "B12", "I23")
 */
function formatBingoNumber(number) {
    return `${getBingoLetter(number)}${number}`;
}

// ==================== CARTELA VALIDATION ====================

/**
 * Validate cartela number range
 */
function isValidCartelaId(cartelaId) {
    return cartelaId >= 1 && cartelaId <= config.TOTAL_CARTELAS;
}

/**
 * Get all cartela IDs (1 to TOTAL_CARTELAS)
 */
function getAllCartelaIds() {
    return Array.from({ length: config.TOTAL_CARTELAS }, (_, i) => i + 1);
}

// ==================== CACHE MANAGEMENT ====================

/**
 * Get number of cached cartelas
 */
function getCachedCartelasCount() {
    return Object.keys(cartelaData).length;
}

/**
 * Clear cartela cache (useful for testing)
 */
function clearCartelaCache() {
    cartelaData = {};
    saveCartelaData();
    console.log("🗑️ Cartela cache cleared");
}

// ==================== EXPORTS ====================
module.exports = {
    generateRandomBingoCard,
    getCartelaGrid,
    saveCartelaData,
    getCartelaMetadata,
    checkBingoWin,
    getBingoLetter,
    formatBingoNumber,
    isValidCartelaId,
    getAllCartelaIds,
    getCachedCartelasCount,
    clearCartelaCache,
};