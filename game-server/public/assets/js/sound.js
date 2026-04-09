// assets/js/sound.js - Complete Sound Management System
// Estif Bingo 24/7 - 4 Sound Packs with Lazy Loading

class SoundManager {
    constructor() {
        this.soundPack = localStorage.getItem('soundPack') || 'pack1';
        this.enabled = localStorage.getItem('soundEnabled') !== 'false';
        this.volume = parseFloat(localStorage.getItem('soundVolume')) || 0.7;
        this.sounds = {
            win: null,
            select: null,
            countdown: null,
            newRound: null,
            error: null,
            click: null,
            numbers: new Map()
        };
        this.preloaded = false;
        this.loadingPromises = new Map();
        this.audioContext = null;
        this.userInteracted = false;
        this.pendingSounds = [];
        
        // Available sound packs
        this.availablePacks = ['pack1', 'pack2', 'pack3', 'pack4'];
        this.packNames = {
            pack1: 'Classic',
            pack2: 'Electronic',
            pack3: 'Casino',
            pack4: 'Retro'
        };
        
        // Bind methods
        this.initAudioContext = this.initAudioContext.bind(this);
        this.handleUserInteraction = this.handleUserInteraction.bind(this);
        
        // Listen for user interaction to enable audio
        document.addEventListener('click', this.handleUserInteraction);
        document.addEventListener('touchstart', this.handleUserInteraction);
        document.addEventListener('keydown', this.handleUserInteraction);
    }
    
    /**
     * Initialize Audio Context (required for iOS)
     */
    async initAudioContext() {
        if (this.audioContext) return;
        
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            await this.audioContext.resume();
            console.log('🔊 Audio context initialized');
        } catch (error) {
            console.warn('Failed to initialize audio context:', error);
        }
    }
    
    /**
     * Handle user interaction to enable audio (iOS requires user gesture)
     */
    async handleUserInteraction() {
        if (!this.userInteracted) {
            this.userInteracted = true;
            await this.initAudioContext();
            this.playPendingSounds();
        }
    }
    
    /**
     * Play any sounds that were queued before user interaction
     */
    playPendingSounds() {
        while (this.pendingSounds.length > 0) {
            const sound = this.pendingSounds.shift();
            this.playSound(sound);
        }
    }
    
    /**
     * Set sound pack (1-4)
     */
    setSoundPack(pack) {
        if (!this.availablePacks.includes(pack)) {
            console.warn(`Invalid sound pack: ${pack}`);
            return;
        }
        
        this.soundPack = pack;
        localStorage.setItem('soundPack', pack);
        this.preloaded = false;
        this.sounds.numbers.clear();
        
        // Reload sounds
        this.preload();
        
        // Trigger event for UI update
        this.trigger('packChanged', { pack, name: this.packNames[pack] });
        
        console.log(`🔊 Sound pack changed to: ${this.packNames[pack]}`);
    }
    
    /**
     * Get current sound pack info
     */
    getCurrentPack() {
        return {
            id: this.soundPack,
            name: this.packNames[this.soundPack],
            available: this.availablePacks
        };
    }
    
    /**
     * Enable/disable sounds
     */
    setEnabled(enabled) {
        this.enabled = enabled;
        localStorage.setItem('soundEnabled', enabled);
        
        if (!enabled) {
            this.stopAll();
        }
        
        this.trigger('enabledChanged', enabled);
    }
    
    /**
     * Toggle sound on/off
     */
    toggleEnabled() {
        this.setEnabled(!this.enabled);
        return this.enabled;
    }
    
    /**
     * Set volume (0-1)
     */
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        localStorage.setItem('soundVolume', this.volume);
        
        // Update volume for all loaded sounds
        if (this.sounds.win) this.sounds.win.volume = this.volume;
        if (this.sounds.select) this.sounds.select.volume = this.volume;
        if (this.sounds.countdown) this.sounds.countdown.volume = this.volume;
        if (this.sounds.newRound) this.sounds.newRound.volume = this.volume;
        if (this.sounds.error) this.sounds.error.volume = this.volume;
        if (this.sounds.click) this.sounds.click.volume = this.volume;
        
        for (const sound of this.sounds.numbers.values()) {
            sound.volume = this.volume;
        }
        
        this.trigger('volumeChanged', this.volume);
    }
    
    /**
     * Preload all critical sounds
     */
    async preload() {
        if (this.preloaded) return;
        
        console.log(`🔊 Preloading sound pack: ${this.soundPack}`);
        
        const soundsToLoad = [
            'win.mp3',
            'select.mp3',
            'countdown.mp3',
            'newRound.mp3',
            'error.mp3',
            'click.mp3'
        ];
        
        // Load effect sounds in parallel
        const loadPromises = soundsToLoad.map(soundFile => {
            const soundName = soundFile.replace('.mp3', '');
            return this.loadSound(soundName, soundFile);
        });
        
        // Preload first 20 numbers (most common)
        const numberPromises = [];
        for (let i = 1; i <= 20; i++) {
            numberPromises.push(this.preloadNumber(i));
        }
        
        try {
            await Promise.all([...loadPromises, ...numberPromises]);
            this.preloaded = true;
            console.log('✅ All sounds preloaded successfully');
        } catch (error) {
            console.warn('Some sounds failed to preload:', error);
            this.preloaded = true; // Still mark as preloaded to avoid retry spam
        }
    }
    
    /**
     * Load a sound file
     */
    async loadSound(name, fileName) {
        if (this.sounds[name] && this.sounds[name].src) return this.sounds[name];
        
        return new Promise((resolve, reject) => {
            const audio = new Audio();
            audio.volume = this.volume;
            audio.preload = 'auto';
            
            audio.addEventListener('canplaythrough', () => {
                this.sounds[name] = audio;
                resolve(audio);
            });
            
            audio.addEventListener('error', (e) => {
                console.warn(`Failed to load sound: ${name}`, e);
                reject(e);
            });
            
            audio.src = `/sounds/${this.soundPack}/${fileName}`;
            audio.load();
        });
    }
    
    /**
     * Preload a specific number sound
     */
    async preloadNumber(number) {
        if (this.sounds.numbers.has(number)) {
            return this.sounds.numbers.get(number);
        }
        
        if (this.loadingPromises.has(`number_${number}`)) {
            return this.loadingPromises.get(`number_${number}`);
        }
        
        const promise = new Promise((resolve, reject) => {
            const audio = new Audio();
            audio.volume = this.volume;
            audio.preload = 'auto';
            
            audio.addEventListener('canplaythrough', () => {
                this.sounds.numbers.set(number, audio);
                this.loadingPromises.delete(`number_${number}`);
                resolve(audio);
            });
            
            audio.addEventListener('error', () => {
                this.loadingPromises.delete(`number_${number}`);
                reject(new Error(`Failed to load number ${number}`));
            });
            
            audio.src = `/sounds/${this.soundPack}/${number}.mp3`;
            audio.load();
        });
        
        this.loadingPromises.set(`number_${number}`, promise);
        return promise;
    }
    
    /**
     * Play number drawn sound (lazy loaded)
     */
    async playNumber(number) {
        if (!this.enabled) return;
        
        try {
            const sound = await this.preloadNumber(number);
            await this.playSound(sound);
        } catch (error) {
            console.log(`Failed to play number ${number}:`, error);
        }
    }
    
    /**
     * Play win sound
     */
    async playWin() {
        if (!this.enabled) return;
        
        // Add victory fanfare effect - play multiple times for excitement
        if (this.sounds.win) {
            await this.playSound(this.sounds.win);
            
            // Optional: Add extra celebration sound after win
            setTimeout(() => {
                if (this.enabled && this.sounds.select) {
                    this.playSound(this.sounds.select);
                }
            }, 500);
        }
    }
    
    /**
     * Play select sound (cartela click)
     */
    async playSelect() {
        if (!this.enabled) return;
        if (this.sounds.select) {
            await this.playSound(this.sounds.select);
        }
    }
    
    /**
     * Play countdown tick (for timer)
     */
    async playCountdown() {
        if (!this.enabled) return;
        if (this.sounds.countdown) {
            await this.playSound(this.sounds.countdown);
        }
    }
    
    /**
     * Play new round sound
     */
    async playNewRound() {
        if (!this.enabled) return;
        if (this.sounds.newRound) {
            await this.playSound(this.sounds.newRound);
        }
    }
    
    /**
     * Play error sound
     */
    async playError() {
        if (!this.enabled) return;
        if (this.sounds.error) {
            await this.playSound(this.sounds.error);
        }
    }
    
    /**
     * Play click sound (UI interaction)
     */
    async playClick() {
        if (!this.enabled) return;
        if (this.sounds.click) {
            await this.playSound(this.sounds.click);
        }
    }
    
    /**
     * Generic play sound method with user interaction handling
     */
    async playSound(audioElement) {
        if (!audioElement) return;
        
        // If no user interaction yet, queue the sound
        if (!this.userInteracted) {
            this.pendingSounds.push(audioElement);
            return;
        }
        
        try {
            audioElement.currentTime = 0;
            
            // Use AudioContext if available for better iOS support
            if (this.audioContext && this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }
            
            await audioElement.play();
        } catch (error) {
            console.log('Audio play failed:', error);
            
            // On iOS, try to resume AudioContext
            if (error.name === 'NotAllowedError' && this.audioContext) {
                await this.audioContext.resume();
                try {
                    await audioElement.play();
                } catch (retryError) {
                    console.log('Retry failed:', retryError);
                }
            }
        }
    }
    
    /**
     * Play sequence of numbers (for debugging/celebration)
     */
    async playNumberSequence(numbers, delay = 200) {
        for (const number of numbers) {
            await this.playNumber(number);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
    
    /**
     * Play celebration sound (for big wins)
     */
    async playCelebration() {
        if (!this.enabled) return;
        
        // Play win sound multiple times with increasing pitch (if supported)
        if (this.sounds.win) {
            for (let i = 0; i < 3; i++) {
                await this.playSound(this.sounds.win);
                await new Promise(resolve => setTimeout(resolve, 300));
            }
        }
    }
    
    /**
     * Stop all sounds
     */
    stopAll() {
        if (this.sounds.win) this.stopSound(this.sounds.win);
        if (this.sounds.select) this.stopSound(this.sounds.select);
        if (this.sounds.countdown) this.stopSound(this.sounds.countdown);
        if (this.sounds.newRound) this.stopSound(this.sounds.newRound);
        if (this.sounds.error) this.stopSound(this.sounds.error);
        if (this.sounds.click) this.stopSound(this.sounds.click);
        
        for (const sound of this.sounds.numbers.values()) {
            this.stopSound(sound);
        }
    }
    
    /**
     * Stop a specific sound
     */
    stopSound(audioElement) {
        if (audioElement) {
            audioElement.pause();
            audioElement.currentTime = 0;
        }
    }
    
    /**
     * Create volume slider UI element
     */
    createVolumeSlider(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const sliderContainer = document.createElement('div');
        sliderContainer.className = 'volume-control';
        sliderContainer.innerHTML = `
            <label>🔊 Volume</label>
            <input type="range" min="0" max="1" step="0.01" value="${this.volume}" class="volume-slider">
            <span class="volume-value">${Math.round(this.volume * 100)}%</span>
        `;
        
        const slider = sliderContainer.querySelector('.volume-slider');
        const valueSpan = sliderContainer.querySelector('.volume-value');
        
        slider.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            this.setVolume(value);
            valueSpan.textContent = `${Math.round(value * 100)}%`;
        });
        
        container.appendChild(sliderContainer);
    }
    
    /**
     * Create sound pack selector UI
     */
    createSoundPackSelector(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const selectorContainer = document.createElement('div');
        selectorContainer.className = 'sound-pack-selector';
        selectorContainer.innerHTML = `
            <label>🎵 Sound Pack</label>
            <div class="pack-buttons">
                ${this.availablePacks.map(pack => `
                    <button class="pack-btn ${pack === this.soundPack ? 'active' : ''}" data-pack="${pack}">
                        ${this.packNames[pack]}
                    </button>
                `).join('')}
            </div>
            <button class="sound-toggle-btn">
                ${this.enabled ? '🔊 Sound On' : '🔇 Sound Off'}
            </button>
        `;
        
        // Add pack button listeners
        selectorContainer.querySelectorAll('.pack-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const pack = btn.dataset.pack;
                this.setSoundPack(pack);
                
                // Update active state
                selectorContainer.querySelectorAll('.pack-btn').forEach(b => {
                    b.classList.remove('active');
                });
                btn.classList.add('active');
                
                // Play preview sound
                this.playSelect();
            });
        });
        
        // Add toggle button listener
        const toggleBtn = selectorContainer.querySelector('.sound-toggle-btn');
        toggleBtn.addEventListener('click', () => {
            const newState = this.toggleEnabled();
            toggleBtn.textContent = newState ? '🔊 Sound On' : '🔇 Sound Off';
            this.playClick();
        });
        
        container.appendChild(selectorContainer);
    }
    
    /**
     * Simple event emitter for UI updates
     */
    trigger(event, data) {
        const customEvent = new CustomEvent(`sound:${event}`, { detail: data });
        document.dispatchEvent(customEvent);
    }
    
    /**
     * Listen to sound events
     */
    on(event, callback) {
        document.addEventListener(`sound:${event}`, (e) => callback(e.detail));
    }
    
    /**
     * Check if sound is supported
     */
    isSupported() {
        return 'Audio' in window;
    }
    
    /**
     * Get sound status
     */
    getStatus() {
        return {
            enabled: this.enabled,
            volume: this.volume,
            soundPack: this.soundPack,
            packName: this.packNames[this.soundPack],
            preloaded: this.preloaded,
            userInteracted: this.userInteracted,
            supported: this.isSupported(),
            loadedSounds: {
                effects: Object.keys(this.sounds).filter(k => this.sounds[k] && k !== 'numbers').length,
                numbers: this.sounds.numbers.size
            }
        };
    }
}

// Create global instance
const soundManager = new SoundManager();

// Auto-preload on page load (after user interaction)
document.addEventListener('DOMContentLoaded', () => {
    // Don't preload immediately - wait for user interaction
    // This is handled by the handleUserInteraction method
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = soundManager;
}