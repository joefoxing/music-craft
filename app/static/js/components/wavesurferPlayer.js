/**
 * Unified WaveSurfer Audio Player
 * Single audio player component used across the entire application.
 * Replaces all previous custom audio players with a consistent waveform-based UI.
 *
 * Usage:
 *   const player = new UnifiedAudioPlayer(containerEl, audioUrl, options);
 *   player.destroy();   // cleanup
 *
 * Options:
 *   height        - Waveform height in px (default: 48)
 *   barWidth      - Width of each bar in the waveform (default: 2)
 *   barGap        - Gap between bars (default: 1)
 *   barRadius     - Border radius of bars (default: 2)
 *   waveColor     - Color of the unplayed waveform (default: '#94a3b8')
 *   progressColor - Color of the played waveform (default: '#6366f1')
 *   cursorWidth   - Width of the playback cursor (default: 0)
 *   compact       - Use a compact layout, e.g. sticky player (default: false)
 *   showVolume    - Whether to show volume controls (default: true)
 *   showTime      - Whether to show time labels (default: true)
 *   onPlay        - Callback when playback starts
 *   onPause       - Callback when playback pauses
 *   onFinish      - Callback when playback finishes
 *   onReady       - Callback when waveform is ready
 *   onTimeUpdate  - Callback(currentTime, duration) on each time update
 */

class UnifiedAudioPlayer {
    /**
     * Registry of all active player instances for global pause management.
     * @type {Set<UnifiedAudioPlayer>}
     */
    static instances = new Set();

    /**
     * @param {HTMLElement} container - DOM element to render the player into
     * @param {string} audioUrl - URL of the audio file
     * @param {Object} options - Player options (see class docs)
     */
    constructor(container, audioUrl, options = {}) {
        this.container = container;
        this.audioUrl = audioUrl || '';
        this.options = {
            height: 48,
            barWidth: 2,
            barGap: 1,
            barRadius: 2,
            waveColor: '#94a3b8',
            progressColor: '#6366f1',
            cursorWidth: 0,
            compact: false,
            showVolume: true,
            showTime: true,
            onPlay: null,
            onPause: null,
            onFinish: null,
            onReady: null,
            onTimeUpdate: null,
            ...options,
        };

        this.wavesurfer = null;
        this.isPlaying = false;
        this.isReady = false;
        this.duration = 0;
        this.currentTime = 0;

        // DOM references (populated in _buildUI)
        this.playBtn = null;
        this.currentTimeEl = null;
        this.durationEl = null;
        this.volumeBtn = null;
        this.volumeSlider = null;
        this.waveContainer = null;
        this._previousVolume = 0.8;

        this._buildUI();
        if (this.audioUrl) {
            this._initWaveSurfer();
        } else {
            this._showDisabled();
        }

        UnifiedAudioPlayer.instances.add(this);
    }

    // ─── UI BUILD ──────────────────────────────────────────────────────

    _buildUI() {
        this.container.innerHTML = '';
        const compact = this.options.compact;

        // Root wrapper
        const root = document.createElement('div');
        root.className = compact
            ? 'ws-player ws-player--compact flex items-center gap-2'
            : 'ws-player flex items-center gap-3 bg-slate-100 dark:bg-slate-800 p-3 rounded-lg';

        // Play / Pause button
        this.playBtn = document.createElement('button');
        this.playBtn.className = compact
            ? 'ws-play-btn size-10 bg-white text-black rounded-full flex items-center justify-center flex-shrink-0'
            : 'ws-play-btn p-2 bg-primary hover:bg-primary-dark text-white rounded-full transition-colors flex-shrink-0';
        this.playBtn.setAttribute('aria-label', 'Play');
        this.playBtn.innerHTML = '<span class="material-symbols-outlined ws-play-icon">play_arrow</span>';
        root.appendChild(this.playBtn);

        // Centre column: waveform + time labels
        const centre = document.createElement('div');
        centre.className = 'flex-1 min-w-0';

        // Waveform container
        this.waveContainer = document.createElement('div');
        this.waveContainer.className = 'ws-waveform rounded overflow-hidden';
        centre.appendChild(this.waveContainer);

        // Time row
        if (this.options.showTime) {
            const timeRow = document.createElement('div');
            timeRow.className = 'flex justify-between text-xs text-slate-500 dark:text-slate-400 mt-1';
            this.currentTimeEl = document.createElement('span');
            this.currentTimeEl.className = 'ws-current-time';
            this.currentTimeEl.textContent = '0:00';
            this.durationEl = document.createElement('span');
            this.durationEl.className = 'ws-duration';
            this.durationEl.textContent = '0:00';
            timeRow.appendChild(this.currentTimeEl);
            timeRow.appendChild(this.durationEl);
            centre.appendChild(timeRow);
        }

        root.appendChild(centre);

        // Volume controls
        if (this.options.showVolume && !compact) {
            const volWrap = document.createElement('div');
            volWrap.className = 'flex items-center gap-2 flex-shrink-0';

            this.volumeBtn = document.createElement('button');
            this.volumeBtn.className = 'ws-volume-btn p-1 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300';
            this.volumeBtn.setAttribute('aria-label', 'Mute');
            this.volumeBtn.innerHTML = '<span class="material-symbols-outlined text-sm">volume_up</span>';

            this.volumeSlider = document.createElement('input');
            this.volumeSlider.type = 'range';
            this.volumeSlider.min = '0';
            this.volumeSlider.max = '100';
            this.volumeSlider.value = '80';
            this.volumeSlider.className = 'ws-volume-slider w-16 accent-primary';
            this.volumeSlider.setAttribute('aria-label', 'Volume');

            volWrap.appendChild(this.volumeBtn);
            volWrap.appendChild(this.volumeSlider);
            root.appendChild(volWrap);
        }

        this.container.appendChild(root);
        this._bindUIEvents();
    }

    // ─── EVENT BINDING ─────────────────────────────────────────────────

    _bindUIEvents() {
        // Play / pause
        this.playBtn.addEventListener('click', () => this.togglePlayPause());

        // Volume slider
        if (this.volumeSlider) {
            this.volumeSlider.addEventListener('input', (e) => {
                const vol = Number(e.target.value) / 100;
                this.setVolume(vol);
            });
        }

        // Volume mute toggle
        if (this.volumeBtn) {
            this.volumeBtn.addEventListener('click', () => {
                if (this.wavesurfer) {
                    const currentVol = this.wavesurfer.getVolume();
                    if (currentVol > 0) {
                        this._previousVolume = currentVol;
                        this.setVolume(0);
                        if (this.volumeSlider) this.volumeSlider.value = '0';
                    } else {
                        this.setVolume(this._previousVolume);
                        if (this.volumeSlider) this.volumeSlider.value = String(Math.round(this._previousVolume * 100));
                    }
                }
            });
        }
    }

    // ─── WAVESURFER INIT ───────────────────────────────────────────────

    _initWaveSurfer() {
        if (typeof WaveSurfer === 'undefined') {
            console.error('WaveSurfer.js is not loaded. Falling back to simple player.');
            this._fallbackPlayer();
            return;
        }

        // Check if the container is visible (has non-zero dimensions).
        // WaveSurfer needs a visible container to render correctly.
        const rect = this.waveContainer.getBoundingClientRect();
        if (rect.width === 0) {
            this._deferUntilVisible();
            return;
        }

        this._createWaveSurfer();
    }

    /**
     * Defers WaveSurfer creation until the container becomes visible.
     * Uses IntersectionObserver if available, falls back to polling.
     */
    _deferUntilVisible() {
        if (this._visibilityObserver) return; // already waiting

        if (typeof IntersectionObserver !== 'undefined') {
            this._visibilityObserver = new IntersectionObserver((entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting || entry.boundingClientRect.width > 0) {
                        this._visibilityObserver.disconnect();
                        this._visibilityObserver = null;
                        // Use rAF to ensure layout is fully computed
                        requestAnimationFrame(() => this._createWaveSurfer());
                        break;
                    }
                }
            }, { threshold: 0 });
            this._visibilityObserver.observe(this.waveContainer);
        } else {
            // Fallback: poll every 200ms
            this._visibilityPoll = setInterval(() => {
                const rect = this.waveContainer.getBoundingClientRect();
                if (rect.width > 0) {
                    clearInterval(this._visibilityPoll);
                    this._visibilityPoll = null;
                    requestAnimationFrame(() => this._createWaveSurfer());
                }
            }, 200);
        }
    }

    _createWaveSurfer() {
        if (this.wavesurfer) return; // prevent double init

        this.wavesurfer = WaveSurfer.create({
            container: this.waveContainer,
            height: this.options.height,
            barWidth: this.options.barWidth,
            barGap: this.options.barGap,
            barRadius: this.options.barRadius,
            waveColor: this.options.waveColor,
            progressColor: this.options.progressColor,
            cursorWidth: this.options.cursorWidth,
            normalize: true,
            url: this.audioUrl,
        });

        // Ready
        this.wavesurfer.on('ready', () => {
            this.isReady = true;
            this.duration = this.wavesurfer.getDuration();
            if (this.durationEl) this.durationEl.textContent = this._formatTime(this.duration);
            this.wavesurfer.setVolume(0.8);
            if (this.options.onReady) this.options.onReady(this);
        });

        // Time update
        this.wavesurfer.on('timeupdate', (currentTime) => {
            this.currentTime = currentTime;
            if (this.currentTimeEl) this.currentTimeEl.textContent = this._formatTime(currentTime);
            if (this.options.onTimeUpdate) this.options.onTimeUpdate(currentTime, this.duration);
        });

        // Play
        this.wavesurfer.on('play', () => {
            this.isPlaying = true;
            this._updatePlayIcon(true);
            if (this.options.onPlay) this.options.onPlay(this);
        });

        // Pause
        this.wavesurfer.on('pause', () => {
            this.isPlaying = false;
            this._updatePlayIcon(false);
            if (this.options.onPause) this.options.onPause(this);
        });

        // Finish
        this.wavesurfer.on('finish', () => {
            this.isPlaying = false;
            this._updatePlayIcon(false);
            if (this.currentTimeEl) this.currentTimeEl.textContent = '0:00';
            if (this.options.onFinish) this.options.onFinish(this);
        });

        // Error
        this.wavesurfer.on('error', (err) => {
            console.error('WaveSurfer error:', err);
        });
    }

    // ─── FALLBACK (no WaveSurfer available) ────────────────────────────

    _fallbackPlayer() {
        // Simple HTML5 <audio> fallback if WaveSurfer fails to load
        this.waveContainer.innerHTML = '';
        const audio = document.createElement('audio');
        audio.controls = true;
        audio.className = 'w-full';
        audio.src = this.audioUrl;
        this.waveContainer.appendChild(audio);
    }

    // ─── DISABLED STATE ────────────────────────────────────────────────

    _showDisabled() {
        this.playBtn.disabled = true;
        this.playBtn.classList.add('opacity-50', 'cursor-not-allowed');
        if (this.durationEl) this.durationEl.textContent = 'N/A';
    }

    // ─── PUBLIC API ────────────────────────────────────────────────────

    /** Toggle play/pause. Pauses other instances first. */
    togglePlayPause() {
        if (!this.wavesurfer || !this.isReady) return;

        // Pause all other players
        UnifiedAudioPlayer.instances.forEach((p) => {
            if (p !== this && p.isPlaying) p.pause();
        });

        this.wavesurfer.playPause();
    }

    play() {
        if (!this.wavesurfer || !this.isReady) return;
        // Pause all other instances
        UnifiedAudioPlayer.instances.forEach((p) => {
            if (p !== this && p.isPlaying) p.pause();
        });
        this.wavesurfer.play();
    }

    pause() {
        if (this.wavesurfer) this.wavesurfer.pause();
    }

    stop() {
        if (this.wavesurfer) {
            this.wavesurfer.stop();
            this.isPlaying = false;
            this._updatePlayIcon(false);
        }
    }

    /** @param {number} vol - 0.0 to 1.0 */
    setVolume(vol) {
        if (this.wavesurfer) {
            this.wavesurfer.setVolume(vol);
            this._updateVolumeIcon(vol);
        }
    }

    /** @param {number} time - seconds */
    seekTo(time) {
        if (this.wavesurfer && this.duration) {
            this.wavesurfer.seekTo(time / this.duration);
        }
    }

    /** Load a new audio source */
    load(url) {
        this.audioUrl = url;
        if (this.wavesurfer) {
            this.wavesurfer.load(url);
        } else if (url) {
            this._initWaveSurfer();
        }
    }

    /** Get current playback time in seconds */
    getCurrentTime() {
        return this.wavesurfer ? this.wavesurfer.getCurrentTime() : 0;
    }

    /** Get total duration in seconds */
    getDuration() {
        return this.duration;
    }

    /** Clean up WaveSurfer instance and remove from registry */
    destroy() {
        UnifiedAudioPlayer.instances.delete(this);
        if (this._visibilityObserver) {
            this._visibilityObserver.disconnect();
            this._visibilityObserver = null;
        }
        if (this._visibilityPoll) {
            clearInterval(this._visibilityPoll);
            this._visibilityPoll = null;
        }
        if (this.wavesurfer) {
            this.wavesurfer.destroy();
            this.wavesurfer = null;
        }
    }

    // ─── HELPERS ───────────────────────────────────────────────────────

    _formatTime(seconds) {
        if (isNaN(seconds) || !isFinite(seconds)) return '0:00';
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${s.toString().padStart(2, '0')}`;
    }

    _updatePlayIcon(playing) {
        const icon = this.playBtn.querySelector('.ws-play-icon');
        if (icon) {
            icon.textContent = playing ? 'pause' : 'play_arrow';
        }
        this.playBtn.setAttribute('aria-label', playing ? 'Pause' : 'Play');
    }

    _updateVolumeIcon(vol) {
        if (!this.volumeBtn) return;
        const iconName = vol === 0 ? 'volume_off' : vol < 0.5 ? 'volume_down' : 'volume_up';
        this.volumeBtn.innerHTML = `<span class="material-symbols-outlined text-sm">${iconName}</span>`;
    }

    // ─── STATIC HELPERS ────────────────────────────────────────────────

    /** Pause all players globally */
    static pauseAll() {
        UnifiedAudioPlayer.instances.forEach((p) => p.pause());
    }

    /** Destroy all players globally */
    static destroyAll() {
        UnifiedAudioPlayer.instances.forEach((p) => p.destroy());
    }

    /**
     * Resolve audio URL from a song/track data object.
     * Handles the many possible property names across the app.
     */
    static resolveAudioUrl(data) {
        if (!data) return '';
        return data.audioUrl || data.audio_url ||
            (data.audio_urls && (data.audio_urls.generated || data.audio_urls.audio ||
                data.audio_urls.source || data.audio_urls.stream ||
                data.audio_urls.source_stream)) ||
            data.sourceAudioUrl || data.source_audio_url ||
            data.streamAudioUrl || data.stream_audio_url ||
            data.sourceStreamAudioUrl || data.source_stream_audio_url ||
            data.stream_url || '';
    }
}

// ─── EXPORT ────────────────────────────────────────────────────────────
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedAudioPlayer;
} else {
    window.UnifiedAudioPlayer = UnifiedAudioPlayer;
}
