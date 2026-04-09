// assets/js/cartela.js - Complete Cartela Grid Management
// Estif Bingo 24/7 - 1000 Unique Cartelas with BINGO Letter Mapping

class CartelaManager {
    constructor(totalCartelas = 1000, maxPerPlayer = 4) {
        this.totalCartelas = totalCartelas;
        this.maxPerPlayer = maxPerPlayer;
        this.selectedCartelas = new Map(); // cartelaId -> { element, grid, selectedAt }
        this.cartelaGrids = new Map(); // Cache for full grids
        this.cartelaPreviews = new Map(); // Cache for preview data
        this.container = null;
        this.onSelectCallback = null;
        this.onDeselectCallback = null;
        this.takenCartelas = new Set(); // Cartelas taken by other players
        this.currentRound = 1;
        this.loadingGrids = new Set(); // Track loading grids
        this.gridCacheExpiry = 30 * 60 * 1000; // 30 minutes cache
        this.lastCacheClear = Date.now();
    }
    
    /**
     * Initialize cartela grid in DOM
     */
    init(containerId, onSelect, onDeselect) {
        this.container = document.getElementById(containerId);
        this.onSelectCallback = onSelect;
        this.onDeselectCallback = onDeselect;
        
        if (!this.container) {
            console.error('Container not found:', containerId);
            return;
        }
        
        this.render();
        this.startCacheCleanup();
    }
    
    /**
     * Render all cartelas (1-1000)
     */
    render() {
        if (!this.container) return;
        
        // Clear container with loading state
        this.container.innerHTML = '<div class="cartelas-loading">Loading 1000 cartelas...</div>';
        
        // Use requestAnimationFrame for better performance
        requestAnimationFrame(() => {
            this.container.innerHTML = '';
            
            // Use document fragment for batch DOM updates
            const fragment = document.createDocumentFragment();
            
            for (let i = 1; i <= this.totalCartelas; i++) {
                const card = this.createCartelaCard(i);
                fragment.appendChild(card);
            }
            
            this.container.appendChild(fragment);
            this.updateAvailability();
            
            // Lazy load grids for visible cartelas
            this.lazyLoadGrids();
        });
    }
    
    /**
     * Create a single cartela card element with BINGO layout
     */
    createCartelaCard(cartelaId) {
        const card = document.createElement('div');
        card.className = 'cartela-card';
        card.setAttribute('data-cartela-id', cartelaId);
        
        if (this.selectedCartelas.has(cartelaId)) {
            card.classList.add('selected');
        }
        
        if (this.takenCartelas.has(cartelaId)) {
            card.classList.add('taken');
        }
        
        // Get BINGO letter for this cartela (based on cartela ID range)
        const bingoLetter = this.getBingoLetter(cartelaId);
        const letterColor = this.getLetterColor(bingoLetter);
        
        // Create card structure with preview grid
        card.innerHTML = `
            <div class="cartela-header" style="border-left-color: ${letterColor}">
                <span class="cartela-bingo-letter" style="background: ${letterColor}">${bingoLetter}</span>
                <span class="cartela-id">#${cartelaId}</span>
                <span class="cartela-price">10 ETB</span>
            </div>
            <div class="cartela-preview-grid" id="preview-${cartelaId}">
                ${this.generatePreviewSkeleton()}
            </div>
            <div class="cartela-footer">
                <button class="select-cartela-btn" data-cartela="${cartelaId}">
                    ${this.selectedCartelas.has(cartelaId) ? '✓ Selected' : 'Select Cartela'}
                </button>
            </div>
        `;
        
        // Add click handler to button
        const btn = card.querySelector('.select-cartela-btn');
        btn.onclick = (e) => {
            e.stopPropagation();
            this.onCartelaClick(cartelaId);
        };
        
        // Add hover effect for grid preview
        card.onmouseenter = () => this.loadPreviewGrid(cartelaId);
        
        return card;
    }
    
    /**
     * Get BINGO letter based on cartela ID
     * Each letter has 200 cartelas (1000 total / 5 letters = 200 each)
     */
    getBingoLetter(cartelaId) {
        if (cartelaId <= 200) return 'B';
        if (cartelaId <= 400) return 'I';
        if (cartelaId <= 600) return 'N';
        if (cartelaId <= 800) return 'G';
        return 'O';
    }
    
    /**
     * Get color for BINGO letter
     */
    getLetterColor(letter) {
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
     * Generate preview skeleton (loading state)
     */
    generatePreviewSkeleton() {
        return `
            <div class="preview-skeleton">
                <div class="skeleton-row">
                    <span>B</span><span>I</span><span>N</span><span>G</span><span>O</span>
                </div>
                <div class="skeleton-numbers">
                    ${Array(5).fill().map(() => 
                        '<div class="skeleton-line">???</div>'
                    ).join('')}
                </div>
            </div>
        `;
    }
    
    /**
     * Generate actual preview grid (5x5 with numbers)
     */
    generatePreviewGrid(grid) {
        if (!grid) return this.generatePreviewSkeleton();
        
        // Get column ranges based on BINGO
        const ranges = {
            'B': [1, 15],
            'I': [16, 30],
            'N': [31, 45],
            'G': [46, 60],
            'O': [61, 75]
        };
        
        let html = '<div class="cartela-grid">';
        html += '<div class="grid-row header-row">';
        html += '<span>B</span><span>I</span><span>N</span><span>G</span><span>O</span>';
        html += '</div>';
        
        // Generate 5x5 grid
        for (let row = 0; row < 5; row++) {
            html += '<div class="grid-row">';
            for (let col = 0; col < 5; col++) {
                const number = grid[row][col];
                const isFree = (row === 2 && col === 2); // FREE space
                const numberClass = isFree ? 'free-space' : 'number';
                const displayValue = isFree ? 'FREE' : number;
                
                html += `<div class="${numberClass}" data-number="${number}" data-row="${row}" data-col="${col}">
                            ${displayValue}
                        </div>`;
            }
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * Load preview grid for a cartela (lazy loading)
     */
    async loadPreviewGrid(cartelaId) {
        const previewContainer = document.getElementById(`preview-${cartelaId}`);
        if (!previewContainer || previewContainer.dataset.loaded === 'true') return;
        
        // Don't load if already loading
        if (this.loadingGrids.has(cartelaId)) return;
        
        this.loadingGrids.add(cartelaId);
        previewContainer.innerHTML = '<div class="loading-spinner-small"></div>';
        
        try {
            const grid = await this.getCartelaGrid(cartelaId);
            if (grid) {
                previewContainer.innerHTML = this.generatePreviewGrid(grid);
                previewContainer.dataset.loaded = 'true';
            }
        } catch (error) {
            console.error(`Failed to load cartela ${cartelaId}:`, error);
            previewContainer.innerHTML = '<div class="load-error">⚠️</div>';
        } finally {
            this.loadingGrids.delete(cartelaId);
        }
    }
    
    /**
     * Lazy load grids for visible cartelas (performance optimization)
     */
    lazyLoadGrids() {
        if (!this.container) return;
        
        // Use Intersection Observer for lazy loading
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const card = entry.target;
                    const cartelaId = parseInt(card.dataset.cartelaId);
                    this.loadPreviewGrid(cartelaId);
                    observer.unobserve(card);
                }
            });
        }, { rootMargin: '100px' });
        
        // Observe all cartela cards
        const cards = this.container.querySelectorAll('.cartela-card');
        cards.forEach(card => observer.observe(card));
    }
    
    /**
     * Handle cartela click
     */
    onCartelaClick(cartelaId) {
        // Check if cartela is taken by someone else
        if (this.takenCartelas.has(cartelaId)) {
            this.showMessage('This cartela is already taken!', 'warning');
            return;
        }
        
        // Check if already selected
        if (this.selectedCartelas.has(cartelaId)) {
            this.deselectCartela(cartelaId);
            return;
        }
        
        // Check max limit
        if (this.selectedCartelas.size >= this.maxPerPlayer) {
            this.showMessage(`Maximum ${this.maxPerPlayer} cartelas per player!`, 'warning');
            return;
        }
        
        // Call select callback (will check balance and server)
        if (this.onSelectCallback) {
            this.onSelectCallback(cartelaId);
        }
    }
    
    /**
     * Select a cartela (called after server confirmation)
     */
    async selectCartela(cartelaId, newBalance = null) {
        if (this.selectedCartelas.has(cartelaId)) return false;
        
        // Load grid if not loaded
        const grid = await this.getCartelaGrid(cartelaId);
        
        this.selectedCartelas.set(cartelaId, {
            element: document.querySelector(`.cartela-card[data-cartela-id="${cartelaId}"]`),
            grid: grid,
            selectedAt: Date.now()
        });
        
        this.updateCardUI(cartelaId, true);
        
        // Update button text
        const card = document.querySelector(`.cartela-card[data-cartela-id="${cartelaId}"]`);
        if (card) {
            const btn = card.querySelector('.select-cartela-btn');
            if (btn) btn.textContent = '✓ Selected';
        }
        
        // Trigger event
        const event = new CustomEvent('cartelaSelected', { detail: { cartelaId, grid } });
        document.dispatchEvent(event);
        
        // Update balance display if provided
        if (newBalance !== null && window.gameManager) {
            window.gameManager.updateBalance(newBalance);
        }
        
        this.updateAvailability();
        return true;
    }
    
    /**
     * Deselect a cartela
     */
    deselectCartela(cartelaId) {
        if (!this.selectedCartelas.has(cartelaId)) return false;
        
        this.selectedCartelas.delete(cartelaId);
        this.updateCardUI(cartelaId, false);
        
        // Update button text
        const card = document.querySelector(`.cartela-card[data-cartela-id="${cartelaId}"]`);
        if (card) {
            const btn = card.querySelector('.select-cartela-btn');
            if (btn) btn.textContent = 'Select Cartela';
        }
        
        // Trigger event
        const event = new CustomEvent('cartelaDeselected', { detail: { cartelaId } });
        document.dispatchEvent(event);
        
        if (this.onDeselectCallback) {
            this.onDeselectCallback(cartelaId);
        }
        
        this.updateAvailability();
        return true;
    }
    
    /**
     * Update single card UI
     */
    updateCardUI(cartelaId, isSelected) {
        const card = document.querySelector(`.cartela-card[data-cartela-id="${cartelaId}"]`);
        if (card) {
            if (isSelected) {
                card.classList.add('selected');
                card.style.transform = 'scale(1.02)';
            } else {
                card.classList.remove('selected');
                card.style.transform = 'scale(1)';
            }
        }
    }
    
    /**
     * Mark a number on all selected cartelas (during game)
     */
    markNumberOnCartelas(number) {
        const letter = this.getNumberLetter(number);
        
        for (const [cartelaId, data] of this.selectedCartelas) {
            if (data.grid) {
                this.markNumberOnCartela(cartelaId, number, letter);
            }
        }
    }
    
    /**
     * Mark number on specific cartela
     */
    markNumberOnCartela(cartelaId, number, letter) {
        const card = document.querySelector(`.cartela-card[data-cartela-id="${cartelaId}"]`);
        if (!card) return;
        
        // Find and mark the number in the grid
        const numberElements = card.querySelectorAll(`.number[data-number="${number}"]`);
        numberElements.forEach(el => {
            el.classList.add('marked');
            el.style.background = '#4caf50';
            el.style.color = 'white';
            el.style.transform = 'scale(1.1)';
            
            // Add animation
            setTimeout(() => {
                if (el) el.style.transform = 'scale(1)';
            }, 300);
        });
    }
    
    /**
     * Check if any selected cartela has BINGO
     */
    checkBingoOnSelected(numbersDrawn) {
        const winners = [];
        const drawnSet = new Set(numbersDrawn);
        
        for (const [cartelaId, data] of this.selectedCartelas) {
            if (data.grid && this.checkBingo(data.grid, drawnSet)) {
                winners.push(cartelaId);
            }
        }
        
        return winners;
    }
    
    /**
     * Check BINGO on a single grid
     */
    checkBingo(grid, drawnSet) {
        // Check rows
        for (let row = 0; row < 5; row++) {
            let rowComplete = true;
            for (let col = 0; col < 5; col++) {
                const number = grid[row][col];
                if (number !== 'FREE' && !drawnSet.has(number)) {
                    rowComplete = false;
                    break;
                }
            }
            if (rowComplete) return true;
        }
        
        // Check columns
        for (let col = 0; col < 5; col++) {
            let colComplete = true;
            for (let row = 0; row < 5; row++) {
                const number = grid[row][col];
                if (number !== 'FREE' && !drawnSet.has(number)) {
                    colComplete = false;
                    break;
                }
            }
            if (colComplete) return true;
        }
        
        // Check main diagonal
        let diag1Complete = true;
        for (let i = 0; i < 5; i++) {
            const number = grid[i][i];
            if (number !== 'FREE' && !drawnSet.has(number)) {
                diag1Complete = false;
                break;
            }
        }
        if (diag1Complete) return true;
        
        // Check anti-diagonal
        let diag2Complete = true;
        for (let i = 0; i < 5; i++) {
            const number = grid[i][4 - i];
            if (number !== 'FREE' && !drawnSet.has(number)) {
                diag2Complete = false;
                break;
            }
        }
        if (diag2Complete) return true;
        
        return false;
    }
    
    /**
     * Get BINGO letter for a number
     */
    getNumberLetter(number) {
        if (number <= 15) return 'B';
        if (number <= 30) return 'I';
        if (number <= 45) return 'N';
        if (number <= 60) return 'G';
        return 'O';
    }
    
    /**
     * Update cartela availability based on balance and game state
     */
    updateAvailability(balance = 0, gameStatus = 'selection', canPlay = true) {
        const cards = this.container.querySelectorAll('.cartela-card');
        const canSelect = (gameStatus === 'selection' && canPlay && balance >= 10 && this.selectedCartelas.size < this.maxPerPlayer);
        
        cards.forEach(card => {
            const cartelaId = parseInt(card.dataset.cartelaId);
            const isSelected = this.selectedCartelas.has(cartelaId);
            const isTaken = this.takenCartelas.has(cartelaId);
            const btn = card.querySelector('.select-cartela-btn');
            
            if (!isSelected && (!canSelect || isTaken)) {
                card.classList.add('disabled');
                if (btn) btn.disabled = true;
            } else {
                card.classList.remove('disabled');
                if (btn && !isSelected) btn.disabled = false;
            }
            
            // Show taken tooltip
            if (isTaken && !isSelected) {
                card.title = 'Taken by another player';
            } else {
                card.title = '';
            }
        });
    }
    
    /**
     * Update taken cartelas from server
     */
    updateTakenCartelas(takenMap) {
        this.takenCartelas.clear();
        for (const [cartelaId, player] of Object.entries(takenMap)) {
            this.takenCartelas.add(parseInt(cartelaId));
        }
        
        // Update UI
        const cards = this.container.querySelectorAll('.cartela-card');
        cards.forEach(card => {
            const cartelaId = parseInt(card.dataset.cartelaId);
            if (this.takenCartelas.has(cartelaId) && !this.selectedCartelas.has(cartelaId)) {
                card.classList.add('taken');
                const btn = card.querySelector('.select-cartela-btn');
                if (btn) btn.disabled = true;
            } else {
                card.classList.remove('taken');
            }
        });
    }
    
    /**
     * Get cartela grid (fetch from server with cache)
     */
    async getCartelaGrid(cartelaId) {
        // Check cache
        if (this.cartelaGrids.has(cartelaId)) {
            const cached = this.cartelaGrids.get(cartelaId);
            if (Date.now() - cached.timestamp < this.gridCacheExpiry) {
                return cached.grid;
            }
        }
        
        try {
            const response = await fetch(`/api/cartela/${cartelaId}`);
            const data = await response.json();
            
            if (data.success && data.grid) {
                // Cache the grid
                this.cartelaGrids.set(cartelaId, {
                    grid: data.grid,
                    timestamp: Date.now()
                });
                return data.grid;
            }
        } catch (err) {
            console.error(`Failed to fetch cartela ${cartelaId}:`, err);
        }
        
        // Return mock grid if API fails (for development)
        return this.generateMockGrid(cartelaId);
    }
    
    /**
     * Generate mock grid for development (5x5 with proper BINGO ranges)
     */
    generateMockGrid(cartelaId) {
        const bingoLetter = this.getBingoLetter(cartelaId);
        const ranges = {
            'B': [1, 15],
            'I': [16, 30],
            'N': [31, 45],
            'G': [46, 60],
            'O': [61, 75]
        };
        
        const range = ranges[bingoLetter];
        const grid = [];
        
        for (let row = 0; row < 5; row++) {
            const rowNumbers = [];
            for (let col = 0; col < 5; col++) {
                if (row === 2 && col === 2) {
                    rowNumbers.push('FREE');
                } else {
                    // Generate random number within letter range
                    const num = Math.floor(Math.random() * (range[1] - range[0] + 1)) + range[0];
                    rowNumbers.push(num);
                }
            }
            grid.push(rowNumbers);
        }
        
        return grid;
    }
    
    /**
     * Clear all selections (new round)
     */
    clearSelections() {
        this.selectedCartelas.clear();
        this.takenCartelas.clear();
        this.render();
    }
    
    /**
     * Reset for new round
     */
    resetForNewRound(roundNumber) {
        this.currentRound = roundNumber;
        this.selectedCartelas.clear();
        this.takenCartelas.clear();
        this.render();
    }
    
    /**
     * Get selected cartelas list
     */
    getSelectedCartelas() {
        return Array.from(this.selectedCartelas.keys());
    }
    
    /**
     * Get selected cartelas count
     */
    getSelectedCount() {
        return this.selectedCartelas.size;
    }
    
    /**
     * Show message to user
     */
    showMessage(message, type = 'info') {
        const event = new CustomEvent('showMessage', { detail: { message, type } });
        document.dispatchEvent(event);
    }
    
    /**
     * Start cache cleanup interval
     */
    startCacheCleanup() {
        setInterval(() => {
            const now = Date.now();
            for (const [id, data] of this.cartelaGrids.entries()) {
                if (now - data.timestamp > this.gridCacheExpiry) {
                    this.cartelaGrids.delete(id);
                }
            }
        }, 5 * 60 * 1000); // Clean every 5 minutes
    }
    
    /**
     * Highlight winning pattern on cartela
     */
    highlightWinningPattern(cartelaId, pattern) {
        const card = document.querySelector(`.cartela-card[data-cartela-id="${cartelaId}"]`);
        if (!card) return;
        
        card.classList.add('winner-highlight');
        card.style.animation = 'pulse 0.5s 3';
        
        // Scroll to winning cartela
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Remove highlight after 5 seconds
        setTimeout(() => {
            card.classList.remove('winner-highlight');
        }, 5000);
    }
}

// Create global instance
const cartelaManager = new CartelaManager(1000, 4);

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = cartelaManager;
}