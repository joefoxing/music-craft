/**
 * Lyrics Pipeline Handler
 *
 * Inline 3-tier lyrics search integrated into the cover-generator page.
 *
 * Tier 1 – Metadata extraction from the uploaded audio file (ID3 tags)
 * Tier 2 – LRCLIB keyword search (fast, free)
 * Tier 3 – Genius pipeline (lyricsgenius + syncedlyrics, requires GENIUS_ACCESS_TOKEN)
 *
 * When lyrics are selected/found they are stripped of LRC timestamps and
 * inserted directly into the Prompt textarea.
 */

class LyricsSearchHandler {
    constructor() {
        // ── search inputs ──────────────────────────────────
        this.trackInput   = null;
        this.artistInput  = null;
        this.searchBtn    = null;

        // ── tier sections ─────────────────────────────────
        this.tier1Section = null;
        this.tier1Artist  = null;
        this.tier1Title   = null;

        this.tier2Section   = null;
        this.tier2Header    = null;
        this.tier2Results   = null;

        this.tier3Section      = null;
        this.pipelineSearchBtn = null;
        this.tier3Result       = null;
        this.tier3Meta         = null;
        this.tier3Preview      = null;
        this.applyPipelineBtn  = null;

        // ── lyrics preview ────────────────────────────────
        this.lyricsPreview   = null;
        this.extractedLyrics = null;

        // ── legacy modal (kept for compat) ────────────────
        this.modal             = null;
        this.resultsContainer  = null;
        this.closeBtn          = null;

        // state
        this.currentAudioId       = null;
        this.autoExtractionEnabled = true;
        this._pendingPipelineData  = null; // holds Tier-3 result before "Apply"
    }

    // ── Initialise ──────────────────────────────────────────────────────────

    init() {
        // search inputs
        this.trackInput  = document.getElementById('lyricsSearchTrack');
        this.artistInput = document.getElementById('lyricsSearchArtist');
        this.searchBtn   = document.getElementById('searchLyricsBtn');

        // tier sections
        this.tier1Section = document.getElementById('tier1Section');
        this.tier1Artist  = document.getElementById('tier1Artist');
        this.tier1Title   = document.getElementById('tier1Title');

        this.tier2Section = document.getElementById('tier2Section');
        this.tier2Header  = document.getElementById('tier2Header');
        this.tier2Results = document.getElementById('tier2Results');

        this.tier3Section      = document.getElementById('tier3Section');
        this.pipelineSearchBtn = document.getElementById('pipelineSearchBtn');
        this.tier3Result       = document.getElementById('tier3Result');
        this.tier3Meta         = document.getElementById('tier3Meta');
        this.tier3Preview      = document.getElementById('tier3Preview');
        this.applyPipelineBtn  = document.getElementById('applyPipelineBtn');

        // lyrics preview
        this.lyricsPreview   = document.getElementById('lyricsPreview');
        this.extractedLyrics = document.getElementById('extractedLyrics');

        // legacy modal
        this.modal            = document.getElementById('lyricsSearchModal');
        this.resultsContainer = document.getElementById('lyricsSearchResults');
        this.closeBtn         = document.getElementById('closeLyricsModal');

        if (!this.trackInput || !this.searchBtn) {
            console.warn('[LyricsSearch] Required elements not found – skipping init');
            return;
        }

        // ── event listeners ──────────────────────────────
        this.searchBtn.addEventListener('click', () => this.handleSearch());

        [this.trackInput, this.artistInput].forEach(el => {
            if (el) el.addEventListener('keypress', e => { if (e.key === 'Enter') this.handleSearch(); });
        });

        if (this.pipelineSearchBtn) {
            this.pipelineSearchBtn.addEventListener('click', () => this.handlePipelineSearch());
        }

        if (this.applyPipelineBtn) {
            this.applyPipelineBtn.addEventListener('click', () => {
                if (this._pendingPipelineData) {
                    this.applyLyricsToPrompt(this._pendingPipelineData.lyrics, this._pendingPipelineData.track_name, this._pendingPipelineData.artist_name);
                }
            });
        }

        // legacy modal close
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.closeModal());
        }
        if (this.modal) {
            this.modal.addEventListener('click', e => { if (e.target === this.modal) this.closeModal(); });
        }
    }

    // ── Tier 1 + 2 auto-extract (called by fileHandler after upload) ────────

    async autoExtractAndSearch(audioFile) {
        if (!this.autoExtractionEnabled || !audioFile) return;
        console.log('[Lyrics T1+T2] Auto-extracting metadata from:', audioFile.name);

        try {
            // Tier 1 – extract ID3 metadata
            const formData = new FormData();
            formData.append('file', audioFile);

            const metaResp = await fetch('/api/lyrics-search/extract-metadata', {
                method: 'POST',
                body: formData
            });

            if (!metaResp.ok) {
                console.warn('[Lyrics T1] Metadata request failed:', metaResp.status);
                return;
            }

            const meta = await metaResp.json();
            console.log('[Lyrics T1] Metadata:', meta);

            // Show Tier 1
            if (meta.artist || meta.title) {
                this._showTier1(meta.artist || '', meta.title || '');
            }

            // Pre-fill search inputs
            if (meta.artist && this.artistInput) this.artistInput.value = meta.artist;
            if (meta.title  && this.trackInput)  this.trackInput.value  = meta.title;

            // Tier 2 – auto-search LRCLIB if title found
            if (meta.title) {
                await this._searchLRCLIB(meta.title, meta.artist || '', true /* auto */);
            }
        } catch (err) {
            console.error('[Lyrics T1+T2] Auto-extraction error:', err);
        }
    }

    // ── Manual search (Tier 2 LRCLIB) ───────────────────────────────────────

    async handleSearch() {
        const track  = this.trackInput  ? this.trackInput.value.trim()  : '';
        const artist = this.artistInput ? this.artistInput.value.trim() : '';

        if (!track) {
            this.showNotification('Please enter a song title', 'error');
            return;
        }

        this._setSearchBtnLoading(true);
        try {
            await this._searchLRCLIB(track, artist, false);
        } finally {
            this._setSearchBtnLoading(false);
        }
    }

    // ── Tier 2: LRCLIB search ───────────────────────────────────────────────

    async _searchLRCLIB(trackName, artistName, isAuto) {
        this._showTier2Loading(trackName, artistName);

        try {
            const resp = await fetch('/api/lyrics-search/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ track_name: trackName, artist_name: artistName })
            });

            const data = await resp.json();

            if (!resp.ok) throw new Error(data.error || 'LRCLIB search failed');

            const results = data.results || [];

            if (results.length > 0) {
                this._showTier2Results(results);
                // Always show Tier 3 option after Tier 2
                this._showTier3Section();
                if (isAuto) {
                    this.showNotification(`Found ${results.length} lyrics result(s) — select one below`, 'success');
                }
            } else {
                this._showTier2Empty();
                // Show Tier 3 as fallback
                this._showTier3Section();
                if (isAuto) {
                    this.showNotification('No LRCLIB results — try the Genius pipeline below', 'info');
                }
            }
        } catch (err) {
            console.error('[Lyrics T2] LRCLIB error:', err);
            this._showTier2Error(err.message);
            this._showTier3Section();
        }
    }

    // ── Tier 3: Genius pipeline search ──────────────────────────────────────

    async handlePipelineSearch() {
        const track  = this.trackInput  ? this.trackInput.value.trim()  : '';
        const artist = this.artistInput ? this.artistInput.value.trim() : '';

        if (!track) {
            this.showNotification('Please enter a song title first', 'error');
            return;
        }

        if (this.pipelineSearchBtn) {
            this.pipelineSearchBtn.disabled = true;
            this.pipelineSearchBtn.innerHTML =
                '<span class="material-symbols-outlined text-sm animate-spin">progress_activity</span>&nbsp;Searching Genius…';
        }
        if (this.tier3Result) this.tier3Result.classList.add('hidden');

        try {
            const resp = await fetch('/api/lyrics-search/pipeline-search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ track_name: track, artist_name: artist })
            });

            const data = await resp.json();

            if (!resp.ok) {
                throw new Error(data.error || 'Pipeline search failed');
            }

            // Store result and show preview
            this._pendingPipelineData = data;
            this._showTier3Result(data);

        } catch (err) {
            console.error('[Lyrics T3] Pipeline error:', err);
            this.showNotification('Pipeline search failed: ' + err.message, 'error');
        } finally {
            if (this.pipelineSearchBtn) {
                this.pipelineSearchBtn.disabled = false;
                this.pipelineSearchBtn.innerHTML =
                    '<span class="material-symbols-outlined text-sm">hub</span>&nbsp;Search via Genius Pipeline';
            }
        }
    }

    // ── Apply lyrics to prompt ───────────────────────────────────────────────

    applyLyricsToPrompt(lyricsRaw, trackName, artistName) {
        const clean = this.stripTimestamps(lyricsRaw);

        const promptInput = document.getElementById('promptInput');
        if (promptInput) {
            promptInput.value = clean;
            promptInput.dispatchEvent(new Event('input', { bubbles: true }));
            // Resize
            promptInput.style.height = 'auto';
            promptInput.style.height = Math.min(promptInput.scrollHeight, 400) + 'px';
        }

        // Show preview
        if (this.extractedLyrics) this.extractedLyrics.textContent = clean;
        if (this.lyricsPreview)   this.lyricsPreview.classList.remove('hidden');

        const label = [trackName, artistName].filter(Boolean).join(' – ');
        this.showNotification(`Lyrics applied${label ? ': ' + label : ''}`, 'success');
    }

    // ── Private UI helpers ───────────────────────────────────────────────────

    _showTier1(artist, title) {
        if (!this.tier1Section) return;
        if (this.tier1Artist) this.tier1Artist.value = artist || '(not found)';
        if (this.tier1Title)  this.tier1Title.value  = title  || '(not found)';
        this.tier1Section.classList.remove('hidden');
    }

    _showTier2Loading(track, artist) {
        if (!this.tier2Section) return;
        this.tier2Section.classList.remove('hidden');
        if (this.tier2Header) {
            this.tier2Header.textContent =
                `⚡ Tier 2 — LRCLIB: searching "${track}"${artist ? ` by ${artist}` : ''}…`;
        }
        if (this.tier2Results) this.tier2Results.innerHTML =
            '<p class="text-xs text-slate-500 animate-pulse">Searching LRCLIB…</p>';
    }

    _showTier2Results(results) {
        if (!this.tier2Results) return;
        if (this.tier2Header) {
            this.tier2Header.innerHTML =
                `<span class="text-green-500">✓ Tier 2 — LRCLIB: ${results.length} result(s)</span>`;
        }

        this.tier2Results.innerHTML = '';
        results.forEach(result => {
            const card = this._createTier2Card(result);
            this.tier2Results.appendChild(card);
        });
    }

    _createTier2Card(result) {
        const div = document.createElement('div');
        const duration = result.duration
            ? `${Math.floor(result.duration / 60)}:${String(result.duration % 60).padStart(2, '0')}`
            : '—';
        const badge = result.has_synced
            ? '<span class="text-green-600 dark:text-green-400">Synced</span>'
            : '<span class="text-slate-500">Plain</span>';

        div.className = 'flex items-start justify-between gap-2 p-3 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-primary dark:hover:border-primary transition-colors';
        div.innerHTML = `
            <div class="flex-1 min-w-0">
                <div class="font-medium text-sm truncate">${this.escapeHtml(result.track_name)}</div>
                <div class="text-xs text-slate-500 mt-0.5">
                    ${result.artist_name ? this.escapeHtml(result.artist_name) : 'Unknown artist'}
                    ${result.album_name  ? ` · ${this.escapeHtml(result.album_name)}`  : ''}
                    · ${duration} · ${badge}
                </div>
            </div>
            <button class="flex-shrink-0 bg-primary hover:bg-primary-dark text-white text-xs font-medium px-3 py-1.5 rounded-lg transition-colors">
                Apply
            </button>
        `;

        div.querySelector('button').addEventListener('click', () => {
            this.applyLyricsToPrompt(result.lyrics, result.track_name, result.artist_name);
        });
        return div;
    }

    _showTier2Empty() {
        if (this.tier2Header) {
            this.tier2Header.innerHTML = '<span class="text-yellow-500">⚡ Tier 2 — LRCLIB: no results found</span>';
        }
        if (this.tier2Results) {
            this.tier2Results.innerHTML = '<p class="text-xs text-slate-500">No lyrics found on LRCLIB. Try the Genius pipeline below.</p>';
        }
        if (this.tier2Section) this.tier2Section.classList.remove('hidden');
    }

    _showTier2Error(msg) {
        if (this.tier2Header) {
            this.tier2Header.innerHTML = `<span class="text-red-500">⚡ Tier 2 — LRCLIB error</span>`;
        }
        if (this.tier2Results) {
            this.tier2Results.innerHTML = `<p class="text-xs text-red-500">Error: ${this.escapeHtml(msg)}</p>`;
        }
        if (this.tier2Section) this.tier2Section.classList.remove('hidden');
    }

    _showTier3Section() {
        if (this.tier3Section) this.tier3Section.classList.remove('hidden');
    }

    _showTier3Result(data) {
        if (!this.tier3Result) return;
        if (this.tier3Meta) {
            this.tier3Meta.textContent =
                `${data.track_name || ''}${data.artist_name ? ' – ' + data.artist_name : ''}`
                + (data.has_synced ? '  ·  Synced lyrics' : '  ·  Plain lyrics');
        }
        if (this.tier3Preview) {
            const preview = this.stripTimestamps(data.lyrics || '');
            this.tier3Preview.textContent = preview.substring(0, 800) + (preview.length > 800 ? '\n…' : '');
        }
        this.tier3Result.classList.remove('hidden');
    }

    _setSearchBtnLoading(loading) {
        if (!this.searchBtn) return;
        this.searchBtn.disabled = loading;
        this.searchBtn.innerHTML = loading
            ? '<span class="material-symbols-outlined text-sm animate-spin">progress_activity</span>&nbsp;Searching…'
            : '<span class="material-symbols-outlined text-sm">search</span>&nbsp;Search Lyrics';
    }

    // ── Utility ──────────────────────────────────────────────────────────────

    setCurrentAudioId(audioId) { this.currentAudioId = audioId; }

    /** Remove LRC-format timestamps: [00:12.34] and <00:12.34> */
    stripTimestamps(lyrics) {
        if (!lyrics) return '';
        return lyrics
            .split('\n')
            .map(line => line.replace(/^\s*\[[\d:.]+\]\s*/g, '').replace(/<[\d:.]+>/g, ''))
            .join('\n')
            .trim();
    }

    escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = String(text || '');
        return d.innerHTML;
    }

    showNotification(message, type = 'info') {
        if (window.showNotification) {
            window.showNotification(message, type);
        } else if (window.NotificationManager?.show) {
            window.NotificationManager.show(message, type);
        } else if (window.NotificationSystem) {
            if (type === 'success') window.NotificationSystem.showSuccess?.(message);
            else if (type === 'error') window.NotificationSystem.showError?.(message);
            else window.NotificationSystem.showInfo?.(message);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    // ── Legacy modal helpers (kept for backward compatibility) ────────────────

    openModal()  { if (this.modal) { this.modal.classList.remove('hidden'); document.body.style.overflow = 'hidden'; } }
    closeModal() { if (this.modal) { this.modal.classList.add('hidden');    document.body.style.overflow = ''; } }

    /** Legacy: display results in modal (used by older code paths). */
    displayResults(results) {
        if (!this.resultsContainer) return;
        this.resultsContainer.innerHTML = `<div class="mb-3 text-sm text-slate-600 dark:text-slate-400">Found ${results.length} result(s)</div>`;
        results.forEach(r => {
            const card = this._createTier2Card(r);
            this.resultsContainer.appendChild(card);
        });
        this.openModal();
    }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    const handler = new LyricsSearchHandler();
    handler.init();
    window.lyricsSearchHandler = handler;
});
