/**
 * MashupHandler - manages multiple audio track slots for mashup generation.
 * Supports 2–5 tracks, each uploadable via file or direct URL.
 */
class MashupHandler {
    constructor() {
        this.MAX_TRACKS = 5;
        this.MIN_TRACKS = 2;
        this.tracks = [];          // array of { url: string|null, status: 'empty'|'ready' }
        this.container = null;
        this.template = null;
        this.addBtn = null;
        this.trackCount = 0;
    }

    /**
     * Initialize with DOM references. Call after DOMContentLoaded.
     * @param {object} elements  { container, template, addBtn }
     */
    initialize({ container, template, addBtn }) {
        this.container = container;
        this.template  = template;
        this.addBtn    = addBtn;

        if (this.addBtn) {
            this.addBtn.addEventListener('click', () => this.addTrack());
        }

        // Start with 2 empty slots
        this.reset();
    }

    /** Reset back to 2 empty slots. */
    reset() {
        if (!this.container) return;
        this.container.innerHTML = '';
        this.tracks = [];
        this.trackCount = 0;
        this._addSlot();
        this._addSlot();
    }

    /** Add a track slot (up to MAX_TRACKS). */
    addTrack() {
        if (this.tracks.length >= this.MAX_TRACKS) {
            if (typeof showNotification === 'function') {
                showNotification(`Maximum ${this.MAX_TRACKS} tracks allowed`, 'warning');
            }
            return;
        }
        this._addSlot();
        this._updateAddBtn();
    }

    /** Remove a track slot by its 0-based index. */
    removeTrack(index) {
        if (this.tracks.length <= this.MIN_TRACKS) {
            if (typeof showNotification === 'function') {
                showNotification(`At least ${this.MIN_TRACKS} tracks are required`, 'warning');
            }
            return;
        }
        const el = this.container.querySelector(`[data-track-index="${index}"]`);
        if (el) el.remove();
        this.tracks.splice(index, 1);
        this._reIndex();
        this._updateAddBtn();
    }

    /**
     * Returns array of ready URLs, or null if any track is still empty.
     * @returns {string[]|null}
     */
    getUploadUrlList() {
        if (this.tracks.some(t => !t.url)) {
            return null;
        }
        return this.tracks.map(t => t.url);
    }

    /** Returns true only when every track has a URL set. */
    isReady() {
        return this.tracks.length >= this.MIN_TRACKS && this.tracks.every(t => !!t.url);
    }

    // ── Private helpers ────────────────────────────────────────────────────────

    _addSlot() {
        const index = this.tracks.length;
        this.tracks.push({ url: null, status: 'empty' });
        this.trackCount++;

        const frag  = this.template.content.cloneNode(true);
        const el    = frag.querySelector('[data-track-slot]');
        el.dataset.trackIndex = index;

        // Label
        el.querySelector('[data-track-label]').textContent = `Track ${index + 1}`;

        // Remove button
        const removeBtn = el.querySelector('[data-remove-btn]');
        removeBtn.addEventListener('click', () => this.removeTrack(
            parseInt(el.dataset.trackIndex, 10)
        ));

        // Source tabs
        const uploadTabBtn  = el.querySelector('[data-upload-tab]');
        const urlTabBtn     = el.querySelector('[data-url-tab]');
        const uploadSection = el.querySelector('[data-upload-section]');
        const urlSection    = el.querySelector('[data-url-section]');

        uploadTabBtn.addEventListener('click', () => {
            uploadTabBtn.classList.add('active');
            urlTabBtn.classList.remove('active');
            uploadSection.classList.remove('hidden');
            urlSection.classList.add('hidden');
        });

        urlTabBtn.addEventListener('click', () => {
            urlTabBtn.classList.add('active');
            uploadTabBtn.classList.remove('active');
            urlSection.classList.remove('hidden');
            uploadSection.classList.add('hidden');
        });

        // File upload
        const fileInput  = el.querySelector('[data-file-input]');
        const uploadBtn  = el.querySelector('[data-upload-btn]');
        const browseBtn  = el.querySelector('[data-browse-btn]');
        const progressEl = el.querySelector('[data-progress-bar]');
        const progressTx = el.querySelector('[data-progress-text]');
        const statusEl   = el.querySelector('[data-slot-status]');

        if (browseBtn) {
            browseBtn.addEventListener('click', () => fileInput && fileInput.click());
        }
        if (fileInput) {
            fileInput.addEventListener('change', () => {
                const file = fileInput.files[0];
                if (file) {
                    uploadBtn.disabled = false;
                    statusEl.textContent = file.name;
                }
            });
        }
        if (uploadBtn) {
            uploadBtn.addEventListener('click', async () => {
                const file = fileInput && fileInput.files[0];
                if (!file) return;
                const i = parseInt(el.dataset.trackIndex, 10);
                await this._uploadFile(i, file, el, progressEl, progressTx, statusEl);
            });
        }

        // Drag-and-drop on the upload area
        const uploadArea = el.querySelector('[data-upload-area]');
        if (uploadArea) {
            uploadArea.addEventListener('dragover', e => { e.preventDefault(); uploadArea.classList.add('drag-over'); });
            uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
            uploadArea.addEventListener('drop', e => {
                e.preventDefault();
                uploadArea.classList.remove('drag-over');
                const file = e.dataTransfer.files[0];
                if (file && fileInput) {
                    // Manually transfer to input
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    fileInput.files = dt.files;
                    uploadBtn.disabled = false;
                    statusEl.textContent = file.name;
                }
            });
        }

        // URL section
        const urlInput  = el.querySelector('[data-url-input]');
        const testBtn   = el.querySelector('[data-test-btn]');
        const useUrlBtn = el.querySelector('[data-use-url-btn]');
        const urlStatus = el.querySelector('[data-url-status]');

        if (testBtn) {
            testBtn.addEventListener('click', async () => {
                const url = urlInput.value.trim();
                if (!url) return;
                urlStatus.textContent = 'Testing…';
                urlStatus.className = 'text-xs text-slate-500 mt-1';
                try {
                    const res = await fetch(url, { method: 'HEAD', mode: 'no-cors' });
                    urlStatus.textContent = '✓ URL seems reachable';
                    urlStatus.className = 'text-xs text-green-600 mt-1';
                } catch {
                    urlStatus.textContent = '✓ URL entered (cannot verify cross-origin)';
                    urlStatus.className = 'text-xs text-amber-500 mt-1';
                }
            });
        }

        if (useUrlBtn) {
            useUrlBtn.addEventListener('click', () => {
                const url = urlInput.value.trim();
                if (!url) {
                    urlStatus.textContent = 'Please enter a URL';
                    urlStatus.className = 'text-xs text-red-500 mt-1';
                    return;
                }
                const i = parseInt(el.dataset.trackIndex, 10);
                this._setTrackReady(i, url, el, `URL: ${url.length > 50 ? url.slice(0, 47) + '…' : url}`);
            });
        }

        this.container.appendChild(frag);
        this._updateRemoveBtns();
        this._updateAddBtn();
    }

    async _uploadFile(index, file, slotEl, progressEl, progressTx, statusEl) {
        const uploadBtn = slotEl.querySelector('[data-upload-btn]');
        if (uploadBtn) uploadBtn.disabled = true;
        statusEl.textContent = 'Uploading…';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const xhr  = new XMLHttpRequest();
            const url  = await new Promise((resolve, reject) => {
                xhr.open('POST', '/upload');
                if (window.csrfToken) {
                    xhr.setRequestHeader('X-CSRFToken', window.csrfToken);
                }
                xhr.upload.addEventListener('progress', e => {
                    if (e.lengthComputable && progressEl && progressTx) {
                        const pct = Math.round((e.loaded / e.total) * 100);
                        progressEl.style.width = pct + '%';
                        progressTx.textContent = pct + '%';
                    }
                });
                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const data = JSON.parse(xhr.responseText);
                            const fileUrl = data?.data?.file_url || data?.file_url;
                            if (fileUrl) resolve(fileUrl);
                            else reject(new Error('No file_url in response'));
                        } catch { reject(new Error('Invalid JSON response')); }
                    } else {
                        reject(new Error(`Upload failed: ${xhr.status}`));
                    }
                });
                xhr.addEventListener('error', () => reject(new Error('Network error')));
                xhr.send(formData);
            });

            this._setTrackReady(index, url, slotEl, `✓ ${file.name}`);
        } catch (err) {
            statusEl.textContent = `✗ ${err.message}`;
            statusEl.classList.add('text-red-500');
            if (uploadBtn) uploadBtn.disabled = false;
        }
    }

    _setTrackReady(index, url, slotEl, label) {
        this.tracks[index].url    = url;
        this.tracks[index].status = 'ready';

        const statusEl   = slotEl.querySelector('[data-slot-status]');
        const readyBadge = slotEl.querySelector('[data-ready-badge]');
        const clearBtn   = slotEl.querySelector('[data-clear-btn]');

        if (statusEl)   { statusEl.textContent = label; statusEl.classList.add('text-green-600'); }
        if (readyBadge) { readyBadge.classList.remove('hidden'); }
        if (clearBtn) {
            clearBtn.classList.remove('hidden');
            clearBtn.addEventListener('click', () => this._clearTrack(index, slotEl), { once: true });
        }
        // Notify parent if callback set
        if (typeof this.onReadyChange === 'function') this.onReadyChange();
    }

    _clearTrack(index, slotEl) {
        this.tracks[index].url    = null;
        this.tracks[index].status = 'empty';

        const statusEl   = slotEl.querySelector('[data-slot-status]');
        const readyBadge = slotEl.querySelector('[data-ready-badge]');
        const clearBtn   = slotEl.querySelector('[data-clear-btn]');
        const progressEl = slotEl.querySelector('[data-progress-bar]');
        const progressTx = slotEl.querySelector('[data-progress-text]');
        const fileInput  = slotEl.querySelector('[data-file-input]');
        const urlInput   = slotEl.querySelector('[data-url-input]');
        const uploadBtn  = slotEl.querySelector('[data-upload-btn]');
        const urlStatus  = slotEl.querySelector('[data-url-status]');

        if (statusEl)   { statusEl.textContent = 'No file selected'; statusEl.className = 'text-sm text-slate-500 mt-1 truncate'; }
        if (readyBadge) { readyBadge.classList.add('hidden'); }
        if (clearBtn)   { clearBtn.classList.add('hidden'); }
        if (progressEl) { progressEl.style.width = '0%'; }
        if (progressTx) { progressTx.textContent = '0%'; }
        if (fileInput)  { fileInput.value = ''; }
        if (urlInput)   { urlInput.value = ''; }
        if (uploadBtn)  { uploadBtn.disabled = true; }
        if (urlStatus)  { urlStatus.textContent = ''; }

        if (typeof this.onReadyChange === 'function') this.onReadyChange();
    }

    _reIndex() {
        const slots = this.container.querySelectorAll('[data-track-slot]');
        slots.forEach((slot, i) => {
            slot.dataset.trackIndex = i;
            const label = slot.querySelector('[data-track-label]');
            if (label) label.textContent = `Track ${i + 1}`;
        });
        this._updateRemoveBtns();
    }

    _updateRemoveBtns() {
        const slots = this.container.querySelectorAll('[data-track-slot]');
        slots.forEach(slot => {
            const btn = slot.querySelector('[data-remove-btn]');
            if (btn) btn.disabled = this.tracks.length <= this.MIN_TRACKS;
        });
    }

    _updateAddBtn() {
        if (!this.addBtn) return;
        this.addBtn.disabled = this.tracks.length >= this.MAX_TRACKS;
        const countEl = this.addBtn.querySelector('[data-track-count]');
        if (countEl) countEl.textContent = `${this.tracks.length}/${this.MAX_TRACKS}`;
    }
}

// Expose globally
window.MashupHandler = MashupHandler;
