// assets/js/cartela.js - Cartela Grid Management

class CartelaManager {
    constructor(totalCartelas = 400, maxPerPlayer = 2) {
        this.totalCartelas = totalCartelas;
        this.maxPerPlayer = maxPerPlayer;
        this.selectedCartelas = [];
        this.cartelaGrids = new Map(); // Cache for grids
        this.container = null;
        this.onSelectCallback = null;
        this.onDeselectCallback = null;
    }
    
    /**
     * Initialize cartela grid in DOM
     */
    init(containerId, onSelect, onDeselect) {
        this.container = document.getElementById(containerId);
        this.onSelectCallback = onSelect;
        this.onDeselectCallback = onDeselect;
        this.render();
    }
    
    /**
     * Render all cartelas
     */
    render() {
        if (!this.container) return;
        
        this.container.innerHTML = '';
        for (let i = 1; i <= this.totalCartelas; i++) {
            const card = this.createCartelaCard(i);
            this.container.appendChild(card);
        }
        this.updateAvailability();
    }
    
    /**
     * Create a single cartela card element
     */
    createCartelaCard(cartelaId) {
        const card = document.createElement('div');
        card.className = 'cartela-card';
        if (this.selectedCartelas.includes(cartelaId)) {
            card.classList.add('selected');
        }
        card.dataset.cartela = cartelaId;
        card.innerHTML = `
            <div class="cartela-number">#${cartelaId}</div>
            <div class="cartela-price">10 ETB</div>
        `;
        card.onclick = (e) => {
            e.stopPropagation();
            this.onCartelaClick(cartelaId);
        };
        return card;
    }
    
    /**
     * Handle cartela click
     */
    onCartelaClick(cartelaId) {
        if (this.selectedCartelas.includes(cartelaId)) {
            // Deselect
            if (this.onDeselectCallback) {
                this.onDeselectCallback(cartelaId);
            }
        } else {
            // Select
            if (this.selectedCartelas.length >= this.maxPerPlayer) {
                showMessage(`Maximum ${this.maxPerPlayer} cartelas per round`, 'warning', 1500);
                return;
            }
            if (this.onSelectCallback) {
                this.onSelectCallback(cartelaId);
            }
        }
    }
    
    /**
     * Select a cartela (called after server confirmation)
     */
    selectCartela(cartelaId, updateBalance) {
        if (!this.selectedCartelas.includes(cartelaId)) {
            this.selectedCartelas.push(cartelaId);
            this.updateCardUI(cartelaId, true);
            if (updateBalance && window.gameManager) {
                window.gameManager.updateBalance(updateBalance);
            }
        }
    }
    
    /**
     * Deselect a cartela
     */
    deselectCartela(cartelaId, updateBalance) {
        const index = this.selectedCartelas.indexOf(cartelaId);
        if (index !== -1) {
            this.selectedCartelas.splice(index, 1);
            this.updateCardUI(cartelaId, false);
            if (updateBalance && window.gameManager) {
                window.gameManager.updateBalance(updateBalance);
            }
        }
    }
    
    /**
     * Update single card UI
     */
    updateCardUI(cartelaId, isSelected) {
        const cards = this.container.querySelectorAll('.cartela-card');
        for (const card of cards) {
            if (parseInt(card.dataset.cartela) === cartelaId) {
                if (isSelected) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
                break;
            }
        }
    }
    
    /**
     * Update cartela availability based on balance and game state
     */
    updateAvailability(balance = 0, gameStatus = 'selection') {
        const cards = this.container.querySelectorAll('.cartela-card');
        const canSelect = (gameStatus === 'selection' && balance >= 10 && this.selectedCartelas.length < this.maxPerPlayer);
        
        for (const card of cards) {
            const cartelaId = parseInt(card.dataset.cartela);
            const isSelected = this.selectedCartelas.includes(cartelaId);
            
            if (!isSelected && (!canSelect || this.isCartelaTaken(cartelaId))) {
                card.classList.add('disabled');
            } else {
                card.classList.remove('disabled');
            }
        }
    }
    
    /**
     * Check if cartela is taken (from server)
     */
    isCartelaTaken(cartelaId) {
        // This will be updated by server events
        return this.takenCartelas?.has(cartelaId) || false;
    }
    
    /**
     * Update taken cartelas from server
     */
    updateTakenCartelas(takenMap) {
        this.takenCartelas = takenMap;
    }
    
    /**
     * Clear all selections (new round)
     */
    clearSelections() {
        this.selectedCartelas = [];
        this.render();
    }
    
    /**
     * Get cartela grid (fetch from server if needed)
     */
    async getCartelaGrid(cartelaId) {
        if (this.cartelaGrids.has(cartelaId)) {
            return this.cartelaGrids.get(cartelaId);
        }
        
        try {
            const response = await fetch(`/api/cartela/${cartelaId}`);
            const data = await response.json();
            if (data.success) {
                this.cartelaGrids.set(cartelaId, data.grid);
                return data.grid;
            }
        } catch (err) {
            console.error('Failed to fetch cartela grid:', err);
        }
        return null;
    }
}

// Create global instance
const cartelaManager = new CartelaManager();