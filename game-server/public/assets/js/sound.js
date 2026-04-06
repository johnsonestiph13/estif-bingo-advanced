// assets/js/sound.js - Sound Management System

class SoundManager {
    constructor() {
        this.soundPack = localStorage.getItem('soundPack') || 'pack1';
        this.sounds = {
            win: null,
            select: null,
            countdown: null,
            numbers: {}
        };
        this.enabled = true;
        this.volume = 0.7;
        this.preloaded = false;
    }
    
    /**
     * Set sound pack
     */
    setSoundPack(pack) {
        this.soundPack = pack;
        localStorage.setItem('soundPack', pack);
        this.preloaded = false;
        this.preload();
    }
    
    /**
     * Enable/disable sounds
     */
    setEnabled(enabled) {
        this.enabled = enabled;
    }
    
    /**
     * Set volume (0-1)
     */
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
    }
    
    /**
     * Preload critical sounds
     */
    preload() {
        if (this.preloaded) return;
        
        // Preload win and select sounds
        this.sounds.win = new Audio(`/sounds/${this.soundPack}/win.mp3`);
        this.sounds.select = new Audio(`/sounds/${this.soundPack}/select.mp3`);
        this.sounds.countdown = new Audio(`/sounds/${this.soundPack}/countdown.mp3`);
        
        // Set volume
        this.sounds.win.volume = this.volume;
        this.sounds.select.volume = this.volume;
        this.sounds.countdown.volume = this.volume;
        
        // Preload first 10 numbers
        for (let i = 1; i <= 10; i++) {
            this.preloadNumber(i);
        }
        
        this.preloaded = true;
        console.log(`🔊 Sound pack loaded: ${this.soundPack}`);
    }
    
    /**
     * Preload a specific number sound
     */
    preloadNumber(number) {
        if (!this.sounds.numbers[number]) {
            this.sounds.numbers[number] = new Audio(`/sounds/${this.soundPack}/${number}.mp3`);
            this.sounds.numbers[number].volume = this.volume;
        }
    }
    
    /**
     * Play number drawn sound
     */
    playNumber(number) {
        if (!this.enabled) return;
        
        this.preloadNumber(number);
        const sound = this.sounds.numbers[number];
        if (sound) {
            sound.currentTime = 0;
            sound.play().catch(e => console.log('Audio play blocked:', e));
        }
    }
    
    /**
     * Play win sound
     */
    playWin() {
        if (!this.enabled) return;
        if (this.sounds.win) {
            this.sounds.win.currentTime = 0;
            this.sounds.win.play().catch(e => console.log('Audio play blocked:', e));
        }
    }
    
    /**
     * Play select sound (cartela click)
     */
    playSelect() {
        if (!this.enabled) return;
        if (this.sounds.select) {
            this.sounds.select.currentTime = 0;
            this.sounds.select.play().catch(e => console.log('Audio play blocked:', e));
        }
    }
    
    /**
     * Play countdown tick
     */
    playCountdown() {
        if (!this.enabled) return;
        if (this.sounds.countdown) {
            this.sounds.countdown.currentTime = 0;
            this.sounds.countdown.play().catch(e => console.log('Audio play blocked:', e));
        }
    }
    
    /**
     * Stop all sounds
     */
    stopAll() {
        if (this.sounds.win) {
            this.sounds.win.pause();
            this.sounds.win.currentTime = 0;
        }
        if (this.sounds.select) {
            this.sounds.select.pause();
            this.sounds.select.currentTime = 0;
        }
        if (this.sounds.countdown) {
            this.sounds.countdown.pause();
            this.sounds.countdown.currentTime = 0;
        }
        for (const num in this.sounds.numbers) {
            if (this.sounds.numbers[num]) {
                this.sounds.numbers[num].pause();
                this.sounds.numbers[num].currentTime = 0;
            }
        }
    }
}

// Create global instance
const soundManager = new SoundManager();