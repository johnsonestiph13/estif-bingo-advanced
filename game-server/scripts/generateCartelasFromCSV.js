// game-server/scripts/generateCartelasFromCSV.js
// Generates 1000 cartelas in the exact CSV format you provided

const fs = require('fs');
const path = require('path');

// Configuration
const TOTAL_CARTELAS = 1000;
const OUTPUT_JSON = path.join(__dirname, '../data/cartelas.json');
const OUTPUT_CSV = path.join(__dirname, '../data/cartelas_1000.csv');

// BINGO column ranges
const B_RANGE = { min: 1, max: 15 };
const I_RANGE = { min: 16, max: 30 };
const N_RANGE = { min: 31, max: 45 };
const G_RANGE = { min: 46, max: 60 };
const O_RANGE = { min: 61, max: 75 };

// Helper: Generate random unique numbers for a column
function getRandomNumbers(min, max, count) {
    const numbers = [];
    const available = [];
    for (let i = min; i <= max; i++) available.push(i);
    
    for (let i = 0; i < count; i++) {
        const idx = Math.floor(Math.random() * available.length);
        numbers.push(available[idx]);
        available.splice(idx, 1);
    }
    return numbers;
}

// Helper: Shuffle array
function shuffleArray(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}

// Generate a single cartela grid (5x5)
function generateCartelaGrid(cartelaId) {
    // Generate 5 numbers for each column (B, I, N, G, O)
    const bNumbers = getRandomNumbers(1, 15, 5);
    const iNumbers = getRandomNumbers(16, 30, 5);
    const nNumbers = getRandomNumbers(31, 45, 5);
    const gNumbers = getRandomNumbers(46, 60, 5);
    const oNumbers = getRandomNumbers(61, 75, 5);
    
    // Set FREE space in center (row 2, column 2 - zero-indexed)
    nNumbers[2] = 0;
    
    // Return as 5x5 grid
    return [
        [bNumbers[0], iNumbers[0], nNumbers[0], gNumbers[0], oNumbers[0]],
        [bNumbers[1], iNumbers[1], nNumbers[1], gNumbers[1], oNumbers[1]],
        [bNumbers[2], iNumbers[2], nNumbers[2], gNumbers[2], oNumbers[2]],
        [bNumbers[3], iNumbers[3], nNumbers[3], gNumbers[3], oNumbers[3]],
        [bNumbers[4], iNumbers[4], nNumbers[4], gNumbers[4], oNumbers[4]]
    ];
}

// Generate CSV row for a cartela
function generateCSVRow(cartelaId, grid) {
    // Extract column values
    const b = grid.map(row => row[0]).join(',');
    const i = grid.map(row => row[1]).join(',');
    const n = grid.map(row => row[2]).join(',');
    const g = grid.map(row => row[3]).join(',');
    const o = grid.map(row => row[4]).join(',');
    
    return `${cartelaId},${cartelaId},"${b}","${i}","${n}","${g}","${o}"`;
}

// Generate all cartelas
function generateAllCartelas() {
    const cartelas = {};
    const csvRows = ['card_no,user_id,b,i,n,g,o']; // CSV header
    
    for (let i = 1; i <= TOTAL_CARTELAS; i++) {
        const cartelaId = i.toString();
        const grid = generateCartelaGrid(cartelaId);
        
        // Store in JSON format
        cartelas[cartelaId] = {
            id: cartelaId,
            grid: grid
        };
        
        // Add to CSV
        csvRows.push(generateCSVRow(cartelaId, grid));
    }
    
    return { cartelas, csvRows };
}

// Save files
function saveFiles(cartelas, csvRows) {
    // Ensure data directory exists
    const dataDir = path.dirname(OUTPUT_JSON);
    if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
    }
    
    // Save JSON
    fs.writeFileSync(OUTPUT_JSON, JSON.stringify(cartelas, null, 2));
    console.log(`✅ Saved ${Object.keys(cartelas).length} cartelas to ${OUTPUT_JSON}`);
    
    // Save CSV
    fs.writeFileSync(OUTPUT_CSV, csvRows.join('\n'));
    console.log(`✅ Saved CSV to ${OUTPUT_CSV}`);
    
    // Print sample
    console.log('\n📊 Sample cartela #1:');
    console.log(JSON.stringify(cartelas['1'], null, 2));
}

// Main execution
function main() {
    console.log(`🎲 Generating ${TOTAL_CARTELAS} cartelas in CSV format...\n`);
    const { cartelas, csvRows } = generateAllCartelas();
    saveFiles(cartelas, csvRows);
    console.log(`\n✨ Done! Generated ${TOTAL_CARTELAS} cartelas.`);
}

// Run if called directly
if (require.main === module) {
    main();
}

module.exports = { generateCartelaGrid, generateAllCartelas };