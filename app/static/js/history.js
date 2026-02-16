// History page JavaScript
// Loads and displays callback history with 15-day retention
console.log('history.js loaded v2');

// DOM Elements
const historyContainer = document.getElementById('historyContainer');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');
const errorState = document.getElementById('errorState');
const statsTotal = document.getElementById('statsTotal');
const statsToday = document.getElementById('statsToday');
const statsSuccess = document.getElementById('statsSuccess');
const statsFailed = document.getElementById('statsFailed');
const refreshBtn = document.getElementById('refreshBtn');
const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
const cleanupBtn = document.getElementById('cleanupBtn');
const filterSelect = document.getElementById('filterSelect');
const searchInput = document.getElementById('searchInput');
const historyModal = document.getElementById('historyModal');
const modalCloseBtn = document.getElementById('modalCloseBtn');
const modalContent = document.getElementById('modalContent');
const historyCount = document.getElementById('historyCount');

// Global variables
let allHistory = [];
let filteredHistory = [];
const selectedEntryIds = new Set();
let openCardMenu = null;

// Initialize
function initHistory() {
    // Set up event listeners with null checks
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadHistory);
    } else {
        console.warn('refreshBtn not found in DOM');
    }
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener('click', handleDeleteSelected);
    }
    if (cleanupBtn) {
        cleanupBtn.addEventListener('click', cleanupHistory);
    } else {
        console.warn('cleanupBtn not found in DOM');
    }
    if (filterSelect) {
        filterSelect.addEventListener('change', filterHistory);
    } else {
        console.warn('filterSelect not found in DOM');
    }
    if (searchInput) {
        searchInput.addEventListener('input', searchHistory);
    } else {
        console.warn('searchInput not found in DOM');
    }
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeModal);
    } else {
        console.warn('modalCloseBtn not found in DOM');
    }
    
    // Set up modal click outside to close
    if (historyModal) {
        const modalContentDiv = historyModal.querySelector('.modal-content');
        if (modalContentDiv) {
            modalContentDiv.addEventListener('click', (e) => e.stopPropagation());
        }
        historyModal.addEventListener('click', closeModal);
    }
    
    // Set up retry button
    const retryBtn = document.getElementById('retryHistoryBtn');
    if (retryBtn) {
        retryBtn.addEventListener('click', loadHistory);
    }
    
    
    // Set up video modal buttons
    const closeVideoModalBtn = document.getElementById('closeVideoModalBtn');
    if (closeVideoModalBtn) {
        closeVideoModalBtn.addEventListener('click', closeVideoModal);
    } else {
        console.warn('closeVideoModalBtn not found in DOM');
    }
    
    const cancelVideoBtn = document.getElementById('cancelVideoBtn');
    if (cancelVideoBtn) {
        cancelVideoBtn.addEventListener('click', closeVideoModal);
    } else {
        console.warn('cancelVideoBtn not found in DOM');
    }
    
    const createVideoBtn = document.getElementById('createVideoBtn');
    if (createVideoBtn) {
        createVideoBtn.addEventListener('click', handleModalCreateVideo);
    } else {
        console.warn('createVideoBtn not found in DOM');
    }
    
    // Load initial history
    loadHistory();
    
    // Set up theme toggle if exists
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Set up mobile menu if exists
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHistory);
} else {
    // DOM already loaded
    initHistory();
}

// Theme toggle
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.classList.contains('dark');
    if (isDark) {
        html.classList.remove('dark');
        themeToggle.innerHTML = '<span class="material-symbols-outlined">light_mode</span>';
    } else {
        html.classList.add('dark');
        themeToggle.innerHTML = '<span class="material-symbols-outlined">dark_mode</span>';
    }
}

// Mobile menu
function toggleMobileMenu() {
    const sidebar = document.querySelector('aside');
    sidebar.classList.toggle('hidden');
    sidebar.classList.toggle('md:flex');
}

// UI State Management
function showLoading() {
    if (loadingState) loadingState.classList.remove('hidden');
    if (emptyState) emptyState.classList.add('hidden');
    if (errorState) errorState.classList.add('hidden');
    if (historyContainer) historyContainer.classList.add('hidden');
}

function showEmpty() {
    if (loadingState) loadingState.classList.add('hidden');
    if (emptyState) emptyState.classList.remove('hidden');
    if (errorState) errorState.classList.add('hidden');
    if (historyContainer) historyContainer.classList.add('hidden');
}

function showError(message) {
    if (loadingState) loadingState.classList.add('hidden');
    if (emptyState) emptyState.classList.add('hidden');
    if (errorState) {
        errorState.classList.remove('hidden');
        const errorMessage = document.getElementById('errorMessage');
        if (errorMessage && message) {
            errorMessage.textContent = message;
        }
    }
    if (historyContainer) historyContainer.classList.add('hidden');
}

function showContent() {
    console.log('showContent called');
    console.log('historyContainer:', historyContainer);
    console.log('loadingState:', loadingState);
    if (loadingState) loadingState.classList.add('hidden');
    if (emptyState) emptyState.classList.add('hidden');
    if (errorState) errorState.classList.add('hidden');
    if (historyContainer) {
        console.log('Removing hidden class from historyContainer');
        historyContainer.classList.remove('hidden');
    } else {
        console.error('historyContainer is null');
    }
}

// Load history from API
async function loadHistory() {
    console.log('loadHistory called');
    showLoading();
    
    try {
        console.log('Fetching /api/history');
        const response = await fetch('/api/history');
        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Data received, success:', data.success, 'count:', data.data?.count);
        
        if (response.ok && data.success) {
            allHistory = data.data?.history || [];
            filteredHistory = [...allHistory];
            selectedEntryIds.clear();
            updateDeleteSelectedButton();
            console.log('allHistory length:', allHistory.length);
            
            // DEBUG: log processed_data of each entry
            allHistory.forEach((entry, idx) => {
                console.log(`Entry ${idx}: id=${entry.id}, processed_data=`, entry.processed_data);
            });
            
            updateStats();
            renderHistory();
            
            if (allHistory.length === 0) {
                console.log('No history, showing empty');
                showEmpty();
            } else {
                console.log('History exists, showing content');
                showContent();
            }
        } else {
            throw new Error(data.error || 'Failed to load history');
        }
    } catch (error) {
        console.error('Error loading history:', error);
        showError(`Failed to load history: ${error.message}`);
    }
}

// Update statistics
function updateStats() {
    console.log('updateStats called, allHistory length:', allHistory.length);
    console.log('statsTotal element:', statsTotal);
    
    if (!allHistory.length) {
        if (statsTotal) statsTotal.textContent = '0';
        if (statsToday) statsToday.textContent = '0';
        if (statsSuccess) statsSuccess.textContent = '0';
        if (statsFailed) statsFailed.textContent = '0';
        return;
    }
    
    const today = new Date().toISOString().split('T')[0];
    const todayCount = allHistory.filter(entry => {
        const entryDate = new Date(entry.timestamp).toISOString().split('T')[0];
        return entryDate === today;
    }).length;
    
    const successCount = allHistory.filter(entry =>
        entry.status_code === 200 || entry.status === 'success'
    ).length;
    
    const failedCount = allHistory.filter(entry =>
        entry.status_code && entry.status_code !== 200
    ).length;
    
    console.log('Stats calculated:', {
        total: allHistory.length,
        today: todayCount,
        success: successCount,
        failed: failedCount
    });
    
    if (statsTotal) statsTotal.textContent = allHistory.length;
    if (statsToday) statsToday.textContent = todayCount;
    if (statsSuccess) statsSuccess.textContent = successCount;
    if (statsFailed) statsFailed.textContent = failedCount;
    if (historyCount) historyCount.textContent = String(allHistory.length);
}

// Render history cards
function renderHistory() {
    console.log('renderHistory called, filteredHistory length:', filteredHistory.length);
    if (!historyContainer) {
        console.error('historyContainer is null');
        return;
    }
    
    historyContainer.innerHTML = '';
    
    filteredHistory.forEach(entry => {
        const card = createHistoryCard(entry);
        historyContainer.appendChild(card);
    });
    console.log('renderHistory completed');
}

function closeOpenMenu() {
    if (openCardMenu) {
        openCardMenu.classList.add('hidden');
        openCardMenu = null;
    }
}

document.addEventListener('click', () => {
    closeOpenMenu();
});

// Create a history card element
function createHistoryCard(entry) {
    const card = document.createElement('div');
    card.className = 'history-card bg-white dark:bg-surface-dark rounded-xl border border-slate-200 dark:border-border-dark p-4 hover:shadow-lg transition-all cursor-pointer';
    card.dataset.id = entry.id;
    
    // Format timestamp
    const timestamp = new Date(entry.timestamp);
    const timeStr = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const dateStr = timestamp.toLocaleDateString();
    
    // Determine status badge color
    let statusColor = 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    let statusText = entry.status || 'unknown';
    
    if (entry.status_code === 200) {
        statusColor = 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
        statusText = 'success';
    } else if (entry.status_code && entry.status_code !== 200) {
        statusColor = 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
        statusText = 'error';
    }
    
    // Determine callback type badge
    let callbackTypeColor = 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
    let callbackTypeText = entry.callback_type || 'unknown';
    
    if (entry.callback_type === 'complete') {
        callbackTypeColor = 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
    } else if (entry.callback_type === 'first') {
        callbackTypeColor = 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    } else if (entry.callback_type === 'text') {
        callbackTypeColor = 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400';
    }
    
    // Get task ID for display
    const taskId = entry.task_id || 'N/A';
    const shortTaskId = taskId.length > 12 ? taskId.substring(0, 12) + '...' : taskId;
    
    // Get song title from first track
    let songTitle = shortTaskId; // fallback to task ID
    if (entry.processed_data && entry.processed_data.tracks && entry.processed_data.tracks.length > 0) {
        const firstTrack = entry.processed_data.tracks[0];
        if (firstTrack.title) {
            songTitle = firstTrack.title;
        }
    }
    
    // Get tracks count
    const tracksCount = entry.tracks_count || 0;

    const isSelectedForDeletion = selectedEntryIds.has(String(entry.id));
    if (isSelectedForDeletion) {
        card.classList.add('ring-2', 'ring-red-500');
    }
    
    // Build card HTML
    const cardHTML = `
        <div class="flex flex-col gap-3">
            <div class="flex items-start justify-between gap-3">
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="material-symbols-outlined text-primary text-lg">history</span>
                        <h4 class="font-bold text-slate-900 dark:text-white truncate">Task: ${songTitle}</h4>
                    </div>
                    <p class="text-xs text-slate-500 dark:text-slate-400">${dateStr} at ${timeStr}</p>
                </div>
                <div class="flex items-start gap-2">
                    <div class="flex flex-col items-end gap-1">
                        <span class="inline-block px-2 py-1 rounded text-xs font-medium ${statusColor}">
                            ${statusText}
                        </span>
                        <span class="inline-block px-2 py-1 rounded text-xs font-medium ${callbackTypeColor}">
                            ${callbackTypeText}
                        </span>
                    </div>
                    <div class="relative">
                        <button class="card-menu-btn p-1 rounded-lg text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Menu">
                            <span class="material-symbols-outlined">more_vert</span>
                        </button>
                        <div class="card-menu hidden absolute right-0 mt-2 w-56 bg-white dark:bg-surface-dark border border-slate-200 dark:border-border-dark rounded-lg shadow-lg overflow-hidden z-20">
                            <button class="card-menu-select w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800">
                                ${isSelectedForDeletion ? 'Unselect' : 'Select for deletion'}
                            </button>
                            <button class="card-menu-delete-now w-full text-left px-4 py-2 text-sm text-red-700 dark:text-red-400 hover:bg-slate-50 dark:hover:bg-slate-800">
                                Delete this entry
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-2 text-sm">
                <div class="flex items-center gap-1">
                    <span class="material-symbols-outlined text-slate-500 text-sm">queue_music</span>
                    <span class="text-slate-600 dark:text-slate-400">${tracksCount} track(s)</span>
                </div>
                <div class="flex items-center gap-1">
                    <span class="material-symbols-outlined text-slate-500 text-sm">schedule</span>
                    <span class="text-slate-600 dark:text-slate-400">${formatTimeAgo(timestamp)}</span>
                </div>
            </div>
            
            <div class="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 dark:border-border-dark">
                <button class="view-detail-btn text-xs text-primary hover:text-primary-dark font-medium flex items-center gap-1">
                    <span class="material-symbols-outlined text-sm">visibility</span>
                    View Details
                </button>
            </div>
        </div>
    `;
    
    card.innerHTML = cardHTML;
    
    // Add event listeners
    const viewDetailBtn = card.querySelector('.view-detail-btn');
    viewDetailBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        showEntryDetails(entry);
    });

    const menuBtn = card.querySelector('.card-menu-btn');
    const menu = card.querySelector('.card-menu');
    const menuSelectBtn = card.querySelector('.card-menu-select');
    const menuDeleteNowBtn = card.querySelector('.card-menu-delete-now');

    if (menuBtn && menu) {
        menuBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (openCardMenu && openCardMenu !== menu) {
                closeOpenMenu();
            }
            const isHidden = menu.classList.contains('hidden');
            if (isHidden) {
                menu.classList.remove('hidden');
                openCardMenu = menu;
            } else {
                menu.classList.add('hidden');
                openCardMenu = null;
            }
        });
    }

    if (menu) {
        menu.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    if (menuSelectBtn) {
        menuSelectBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            toggleEntrySelectedForDeletion(entry.id, card, menuSelectBtn);
            closeOpenMenu();
        });
    }

    if (menuDeleteNowBtn) {
        menuDeleteNowBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            closeOpenMenu();
            await deleteEntriesById([String(entry.id)]);
        });
    }
    
    card.addEventListener('click', () => {
        showEntryDetails(entry);
    });
    
    return card;
}

function toggleEntrySelectedForDeletion(entryId, cardEl, menuSelectBtn) {
    const idStr = String(entryId);
    const isSelected = selectedEntryIds.has(idStr);
    if (isSelected) {
        selectedEntryIds.delete(idStr);
        if (cardEl) {
            cardEl.classList.remove('ring-2', 'ring-red-500');
        }
        if (menuSelectBtn) {
            menuSelectBtn.textContent = 'Select for deletion';
        }
    } else {
        selectedEntryIds.add(idStr);
        if (cardEl) {
            cardEl.classList.add('ring-2', 'ring-red-500');
        }
        if (menuSelectBtn) {
            menuSelectBtn.textContent = 'Unselect';
        }
    }
    updateDeleteSelectedButton();
}

async function handleDeleteSelected() {
    const ids = Array.from(selectedEntryIds);
    if (!ids.length) return;
    if (!confirm(`Delete ${ids.length} selected entr${ids.length === 1 ? 'y' : 'ies'}? This action cannot be undone.`)) {
        return;
    }
    await deleteEntriesById(ids);
}

async function deleteEntriesById(ids) {
    if (!ids || !ids.length) return;

    if (deleteSelectedBtn) {
        deleteSelectedBtn.disabled = true;
        deleteSelectedBtn.classList.add('opacity-50', 'cursor-not-allowed');
    }

    try {
        const response = await fetch('/api/history/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids })
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to delete history entries');
        }

        const idsSet = new Set(ids.map(String));
        allHistory = allHistory.filter(e => !idsSet.has(String(e.id)));
        filteredHistory = filteredHistory.filter(e => !idsSet.has(String(e.id)));
        idsSet.forEach(id => selectedEntryIds.delete(id));

        updateStats();
        renderHistory();
        updateDeleteSelectedButton();

        if (allHistory.length === 0) {
            showEmpty();
        } else {
            showContent();
        }
    } catch (error) {
        console.error('Error deleting history entries:', error);
        alert(`Delete failed: ${error.message}`);
    } finally {
        updateDeleteSelectedButton();
    }
}

function updateDeleteSelectedButton() {
    if (!deleteSelectedBtn) return;
    const count = selectedEntryIds.size;
    deleteSelectedBtn.disabled = count === 0;
    if (count === 0) {
        deleteSelectedBtn.classList.add('opacity-50', 'cursor-not-allowed');
        deleteSelectedBtn.classList.remove('cursor-pointer');
        deleteSelectedBtn.innerHTML = '<span class="material-symbols-outlined mr-2">delete</span>Delete Selected';
        return;
    }
    deleteSelectedBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    deleteSelectedBtn.classList.add('cursor-pointer');
    deleteSelectedBtn.innerHTML = `<span class="material-symbols-outlined mr-2">delete</span>Delete Selected (${count})`;
}

// Format time ago
function formatTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return `${Math.floor(diffDays / 7)}w ago`;
}

// Filter history by status
function filterHistory() {
    const filterValue = filterSelect.value;
    
    if (filterValue === 'all') {
        filteredHistory = [...allHistory];
    } else if (filterValue === 'success') {
        filteredHistory = allHistory.filter(entry =>
            entry.status_code === 200 || entry.status === 'success'
        );
    } else if (filterValue === 'failed') {
        filteredHistory = allHistory.filter(entry =>
            entry.status_code && entry.status_code !== 200
        );
    } else if (filterValue === 'today') {
        const today = new Date().toISOString().split('T')[0];
        filteredHistory = allHistory.filter(entry => {
            const entryDate = new Date(entry.timestamp).toISOString().split('T')[0];
            return entryDate === today;
        });
    } else if (filterValue === 'has_audio') {
        filteredHistory = allHistory.filter(entry =>
            entry.has_audio_urls === true
        );
    }
    
    renderHistory();
}

// Search history
function searchHistory() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    
    if (!searchTerm) {
        filteredHistory = [...allHistory];
    } else {
        filteredHistory = allHistory.filter(entry => {
            const taskId = (entry.task_id || '').toLowerCase();
            const statusMessage = (entry.status_message || '').toLowerCase();
            const callbackType = (entry.callback_type || '').toLowerCase();
            
            // Get song title for search
            let songTitle = '';
            if (entry.processed_data && entry.processed_data.tracks && entry.processed_data.tracks.length > 0) {
                const firstTrack = entry.processed_data.tracks[0];
                if (firstTrack.title) {
                    songTitle = firstTrack.title.toLowerCase();
                }
            }
            
            return taskId.includes(searchTerm) || 
                   statusMessage.includes(searchTerm) || 
                   callbackType.includes(searchTerm) ||
                   songTitle.includes(searchTerm);
        });
    }
    
    renderHistory();
}

// Show entry details in modal with audio or video players
function showEntryDetails(entry) {
    console.log('=== showEntryDetails called for entry ===', entry.id);
    console.log('Entry keys:', Object.keys(entry));
    console.log('Entry processed_data raw:', entry.processed_data);
    console.log('processed_data keys:', Object.keys(entry.processed_data || {}));
    console.log('Entry callback_type:', entry.callback_type);
    console.log('Entry is_video_callback:', entry.is_video_callback);
    console.log('Entry video_url:', entry.video_url);
    console.log('historyModal:', !!historyModal, 'modalContent:', !!modalContent);
    
    if (!historyModal || !modalContent) {
        console.error('Modal elements not found');
        return;
    }
    
    // Format timestamp
    const timestamp = new Date(entry.timestamp);
    const formattedTime = timestamp.toLocaleString();
    
    // Get data
    const rawData = entry.raw_data || entry.data || {};
    const processedData = entry.processed_data || {};
    const tracks = processedData.tracks || [];
    console.log('DEBUG tracks:', tracks, 'length:', tracks.length);
    const isVideoCallback = entry.is_video_callback || false;
    const videoUrl = entry.video_url || processedData.video_url;
    
    console.log('Entry processedData:', processedData);
    console.log('Entry tracks:', tracks);
    console.log('Is video callback:', isVideoCallback);
    console.log('Video URL:', videoUrl);
    console.log('Number of tracks:', tracks.length);
    console.log('First track (if any):', tracks[0]);
    console.log('processedData.tracks property?', processedData.tracks);

    tracks.forEach((track, idx) => {
        console.log(`Track ${idx}:`, track);
        console.log(`  audio_urls:`, track.audio_urls);
        console.log(`  image_urls:`, track.image_urls);
    });
    
    // Create modal content
    const modalHTML = `
        <div class="space-y-6">
            <div class="flex items-center justify-center">
                <span class="text-xs text-slate-500">${formattedTime}</span>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Task ID</label>
                        <code class="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-sm break-all">${entry.task_id || 'N/A'}</code>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Entry ID</label>
                        <code class="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-sm break-all">${entry.id || 'N/A'}</code>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Callback Type</label>
                        <span class="inline-block px-2 py-1 rounded text-sm font-medium
                            ${entry.callback_type === 'complete' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                              entry.callback_type === 'first' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                              entry.callback_type === 'text' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                              entry.callback_type === 'video_complete' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400' :
                              'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'}">
                            ${entry.callback_type || 'unknown'}
                        </span>
                    </div>
                </div>
                
                <div class="space-y-2">
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Status Code</label>
                        <span class="inline-block px-2 py-1 rounded text-sm font-medium
                            ${entry.status_code === 200 || entry.status_code === 0 ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                              'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}">
                            ${entry.status_code || 'N/A'}
                        </span>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Status</label>
                        <span class="text-sm text-slate-700 dark:text-slate-300">${entry.status || 'unknown'}</span>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Type</label>
                        <span class="text-sm text-slate-700 dark:text-slate-300">
                            ${isVideoCallback ? 'Video' : 'Audio'} (${tracks.length || 0} track(s))
                        </span>
                    </div>
                </div>
            </div>
            
            <!-- Content Section (Audio or Video) -->
            <div class="mt-6">
                ${isVideoCallback ? `
                    <!-- Video Section -->
                    <div class="flex items-center gap-2 mb-4">
                        <span class="material-symbols-outlined text-primary">movie</span>
                        <h4 class="font-bold text-slate-900 dark:text-white">Generated Video</h4>
                        <span class="text-xs px-2 py-1 bg-purple-500/10 text-purple-500 rounded-full">Video</span>
                    </div>
                    
                    <div id="videoPlayerContainer" class="space-y-4">
                        <!-- Video player will be dynamically inserted here -->
                    </div>
                ` : `
                    <!-- Audio Section -->
                    <div class="flex items-center gap-2 mb-4">
                        <span class="material-symbols-outlined text-primary">queue_music</span>
                        <h4 class="font-bold text-slate-900 dark:text-white">Generated Songs</h4>
                        <span class="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full">${tracks.length} track(s)</span>
                    </div>
                    
                    <div id="audioPlayersContainer" class="space-y-4">
                        <!-- Audio players will be dynamically inserted here -->
                    </div>
                    
                    ${tracks.length === 0 ? `
                        <div class="text-center py-8 bg-slate-50 dark:bg-slate-900 rounded-lg">
                            <span class="material-symbols-outlined text-4xl text-slate-400 mb-3">music_off</span>
                            <p class="text-slate-500 dark:text-slate-400">No audio tracks available for this entry. (Debug: tracks.length=${tracks.length})</p>
                        </div>
                    ` : ''}
                `}
            </div>
            
            <!-- Debug Section -->
            <div class="mt-6 border border-yellow-300 bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                <h4 class="font-bold text-slate-900 dark:text-white text-sm mb-2">Debug Info</h4>
                <div class="text-xs">
                    <div>processed_data exists: ${!!processedData}</div>
                    <div>processed_data keys: ${Object.keys(processedData || {}).join(', ')}</div>
                    <div>processed_data.tracks length: ${processedData.tracks ? processedData.tracks.length : 0}</div>
                    <div>entry.processed_data exists: ${!!entry.processed_data}</div>
                </div>
            </div>
            
            <!-- Raw Data Section (Collapsible) -->
            <div class="mt-6">
                <button id="toggleRawData" class="flex items-center gap-2 text-slate-500 hover:text-slate-900 dark:hover:text-white mb-2">
                    <span class="material-symbols-outlined text-sm">expand_more</span>
                    <span class="text-sm font-medium">Raw Data</span>
                </button>
                <div id="rawDataContent" class="hidden">
                    <pre class="text-xs bg-slate-100 dark:bg-slate-800 p-3 rounded max-h-60 overflow-y-auto">${JSON.stringify(rawData, null, 2)}</pre>
                </div>
            </div>
        </div>
    `;
    
    modalContent.innerHTML = modalHTML;
    
    if (isVideoCallback) {
        console.log('=== Processing video callback ===');
        console.log('Video URL:', videoUrl);
        // Add video player
        const videoPlayerContainer = document.getElementById('videoPlayerContainer');
        console.log('videoPlayerContainer:', videoPlayerContainer);
        console.log('videoPlayerContainer found:', !!videoPlayerContainer);
        
        if (videoUrl) {
            console.log('Creating video player for URL:', videoUrl);
            try {
                const videoPlayer = createVideoPlayerForHistoryEntry(entry, videoUrl);
                console.log('Video player created:', !!videoPlayer);
                if (videoPlayer && videoPlayerContainer) {
                    console.log('Appending video player to container');
                    videoPlayerContainer.appendChild(videoPlayer);
                    console.log('Video player appended successfully');
                } else {
                    console.error('Failed to create video player or container not found');
                    console.error('videoPlayer:', videoPlayer);
                    console.error('videoPlayerContainer:', videoPlayerContainer);
                }
            } catch (error) {
                console.error('Error creating video player:', error);
                console.error('Error stack:', error.stack);
                console.error('Error message:', error.message);
            }
        } else {
            console.log('No video URL available');
            // No video URL available
            const noVideoHTML = `
                <div class="text-center py-8 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <span class="material-symbols-outlined text-4xl text-slate-400 mb-3">movie_off</span>
                    <p class="text-slate-500 dark:text-slate-400">Video URL not available for this entry.</p>
                </div>
            `;
            if (videoPlayerContainer) {
                videoPlayerContainer.innerHTML = noVideoHTML;
            }
        }
    } else {
        // Add audio players for each track
        console.log('Audio players block: tracks.length=', tracks.length);
        if (tracks.length > 0) {
            const audioPlayersContainer = document.getElementById('audioPlayersContainer');
            console.log('audioPlayersContainer:', audioPlayersContainer);
            
            tracks.forEach((track, index) => {
                console.log(`Creating audio player for track ${index + 1}:`, track);
                try {
                    // Add the entry's task ID to the track object for video creation
                    const trackWithTaskId = { ...track, task_id: entry.task_id };
                    const audioPlayer = createAudioPlayer(trackWithTaskId, index + 1);
                    if (audioPlayer && audioPlayersContainer) {
                        audioPlayersContainer.appendChild(audioPlayer);
                    } else {
                        console.error('Failed to create audio player or container not found');
                    }
                } catch (error) {
                    console.error(`Error creating audio player for track ${index + 1}:`, error);
                    console.error('Error stack:', error.stack);
                    console.error('Error message:', error.message);
                }
            });
        }
    }
    
    // Set up raw data toggle
    const toggleRawDataBtn = document.getElementById('toggleRawData');
    const rawDataContent = document.getElementById('rawDataContent');
    
    if (toggleRawDataBtn && rawDataContent) {
        toggleRawDataBtn.addEventListener('click', () => {
            const isHidden = rawDataContent.classList.contains('hidden');
            rawDataContent.classList.toggle('hidden');
            toggleRawDataBtn.querySelector('.material-symbols-outlined').textContent =
                isHidden ? 'expand_less' : 'expand_more';
        });
    }
    
    // Show modal
    console.log('Showing modal');
    historyModal.classList.remove('hidden');
}

// Create an audio player element for a track
function createAudioPlayer(track, trackNumber) {
    console.log(`=== createAudioPlayer called for track ${trackNumber} ===`);
    console.log('Track data:', track);
    console.log('Track keys:', Object.keys(track));
    console.log('Track has task_id:', track.task_id);
    
    const template = document.getElementById('audioPlayerTemplate');
    console.log('audioPlayerTemplate found:', !!template);
    
    if (!template) {
        console.error('Audio player template not found');
        return document.createElement('div');
    }
    
    const player = template.content.cloneNode(true);
    const playerElement = player.querySelector('.audio-player');
    console.log('playerElement found:', !!playerElement);
    
    if (!playerElement) {
        console.error('Could not find .audio-player element in template');
        return document.createElement('div');
    }
    
    // Set track information
    const title = track.title || track.name || `Track ${trackNumber}`;
    const model = track.model || 'unknown';
    
    // Handle tags - could be array, string, or undefined
    let tags = 'No tags';
    if (track.tags) {
        if (Array.isArray(track.tags)) {
            tags = track.tags.join(', ');
        } else if (typeof track.tags === 'string') {
            tags = track.tags;
        } else {
            tags = String(track.tags);
        }
    }
    
    const prompt = track.prompt || 'No lyrics available';
    const created = track.created_at ? new Date(track.created_at).toLocaleString() : 'N/A';
    
    // Get audio URLs
    const audioUrls = track.audio_urls || {};
    const generatedAudioUrl = audioUrls.generated || audioUrls.audio || '';
    const sourceAudioUrl = audioUrls.source || '';
    
    console.log(`Track ${trackNumber} audio URLs:`, { generatedAudioUrl, sourceAudioUrl });
    
    // Set text content
    const titleEl = playerElement.querySelector('[data-track-title]');
    const numberEl = playerElement.querySelector('[data-track-number]');
    const modelEl = playerElement.querySelector('[data-track-model]');
    const tagsEl = playerElement.querySelector('[data-track-tags]');
    const promptEl = playerElement.querySelector('[data-track-prompt]');
    const createdEl = playerElement.querySelector('[data-track-created]');
    
    if (titleEl) titleEl.textContent = title;
    if (numberEl) numberEl.textContent = `Track ${trackNumber}`;
    if (modelEl) modelEl.textContent = model;
    if (tagsEl) tagsEl.textContent = tags;
    if (promptEl) {
        // Format lyrics line by line
        if (prompt && prompt !== 'No lyrics available') {
            promptEl.innerHTML = prompt.split('\n').map(line => {
                if (line.trim() === '') return '<br>';
                return `<div class="lyric-line py-0.5 border-b border-slate-100 dark:border-slate-700/50 last:border-b-0 text-xs">${line}</div>`;
            }).join('');
        } else {
            promptEl.textContent = prompt;
        }
    }
    if (createdEl) createdEl.textContent = created;
    
    // Set audio URLs
    const audioUrlElement = playerElement.querySelector('[data-audio-url]');
    const sourceAudioUrlElement = playerElement.querySelector('[data-source-audio-url]');
    
    if (generatedAudioUrl && audioUrlElement) {
        audioUrlElement.href = generatedAudioUrl;
        audioUrlElement.textContent = generatedAudioUrl.length > 50 ?
            generatedAudioUrl.substring(0, 50) + '...' : generatedAudioUrl;
    } else if (audioUrlElement && audioUrlElement.parentElement) {
        audioUrlElement.parentElement.classList.add('hidden');
    }
    
    if (sourceAudioUrl && sourceAudioUrlElement) {
        sourceAudioUrlElement.href = sourceAudioUrl;
        sourceAudioUrlElement.textContent = sourceAudioUrl.length > 50 ?
            sourceAudioUrl.substring(0, 50) + '...' : sourceAudioUrl;
    } else if (sourceAudioUrlElement && sourceAudioUrlElement.parentElement) {
        sourceAudioUrlElement.parentElement.classList.add('hidden');
    }
    
    // Set up audio player controls
    const audioElement = playerElement.querySelector('[data-audio-element]');
    const playPauseBtn = playerElement.querySelector('.play-pause-btn');
    const progressBar = playerElement.querySelector('.audio-progress');
    const currentTimeEl = playerElement.querySelector('.current-time');
    const durationEl = playerElement.querySelector('.duration');
    const volumeSlider = playerElement.querySelector('.volume-slider');
    const volumeBtn = playerElement.querySelector('.volume-btn');
    
    console.log('Audio player elements found:', {
        audioElement: !!audioElement,
        playPauseBtn: !!playPauseBtn,
        progressBar: !!progressBar,
        currentTimeEl: !!currentTimeEl,
        durationEl: !!durationEl,
        volumeSlider: !!volumeSlider,
        volumeBtn: !!volumeBtn
    });
    
    if (generatedAudioUrl && audioElement) {
        audioElement.src = generatedAudioUrl;
        
        // Set up audio event listeners
        audioElement.addEventListener('loadedmetadata', () => {
            const duration = audioElement.duration;
            const minutes = Math.floor(duration / 60);
            const seconds = Math.floor(duration % 60);
            if (durationEl) durationEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            const durationDataEl = playerElement.querySelector('[data-track-duration]');
            if (durationDataEl) durationDataEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        });
        
        audioElement.addEventListener('timeupdate', () => {
            const currentTime = audioElement.currentTime;
            const duration = audioElement.duration;
            const progress = (currentTime / duration) * 100;
            if (progressBar) progressBar.style.width = `${progress}%`;
            
            const minutes = Math.floor(currentTime / 60);
            const seconds = Math.floor(currentTime % 60);
            if (currentTimeEl) currentTimeEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        });
        
        // Play/pause button
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', () => {
                if (audioElement.paused) {
                    audioElement.play();
                    playPauseBtn.innerHTML = '<span class="material-symbols-outlined">pause</span>';
                } else {
                    audioElement.pause();
                    playPauseBtn.innerHTML = '<span class="material-symbols-outlined">play_arrow</span>';
                }
            });
        }
        
        // Volume controls
        if (volumeSlider) {
            volumeSlider.addEventListener('input', () => {
                audioElement.volume = volumeSlider.value / 100;
            });
        }
        
        if (volumeBtn) {
            volumeBtn.addEventListener('click', () => {
                if (audioElement.volume > 0) {
                    audioElement.volume = 0;
                    if (volumeSlider) volumeSlider.value = 0;
                    volumeBtn.innerHTML = '<span class="material-symbols-outlined">volume_off</span>';
                } else {
                    audioElement.volume = 0.8;
                    if (volumeSlider) volumeSlider.value = 80;
                    volumeBtn.innerHTML = '<span class="material-symbols-outlined">volume_up</span>';
                }
            });
        }
        
        // Progress bar click
        const progressContainer = playerElement.querySelector('.audio-progress-bar');
        if (progressContainer) {
            progressContainer.addEventListener('click', (e) => {
                const rect = progressContainer.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const width = rect.width;
                const percentage = clickX / width;
                audioElement.currentTime = percentage * audioElement.duration;
            });
        }
        
        // Audio ended
        audioElement.addEventListener('ended', () => {
            if (playPauseBtn) playPauseBtn.innerHTML = '<span class="material-symbols-outlined">play_arrow</span>';
            if (progressBar) progressBar.style.width = '0%';
            if (currentTimeEl) currentTimeEl.textContent = '0:00';
        });
    } else {
        // No audio URL available
        if (playPauseBtn) {
            playPauseBtn.disabled = true;
            playPauseBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
        const durationDataEl = playerElement.querySelector('[data-track-duration]');
        if (durationDataEl) durationDataEl.textContent = 'N/A';
        if (durationEl) durationEl.textContent = 'N/A';
    }
    
    // Set up download button
    const downloadBtn = playerElement.querySelector('.download-audio-btn');
    console.log(`Download button found for track ${trackNumber}:`, !!downloadBtn);

    // Inject TrackOptions
    if (typeof TrackOptions !== 'undefined' && downloadBtn && downloadBtn.parentElement) {
        try {
            const trackOptions = new TrackOptions();
            // Ensure track object has all necessary data for library
            const trackData = {
                ...track,
                task_id: track.task_id || (typeof entry !== 'undefined' ? entry.task_id : null)
            };
            const menuElement = trackOptions.render(trackData);
            menuElement.classList.add('self-end', 'mb-2'); // Align to right and add spacing
            downloadBtn.parentElement.insertBefore(menuElement, downloadBtn.parentElement.firstChild);
        } catch (e) {
            console.error('Error injecting TrackOptions:', e);
        }
    }
    
    if (downloadBtn) {
        if (generatedAudioUrl) {
            console.log(`Attaching download event listener for track ${trackNumber}, URL:`, generatedAudioUrl);
            downloadBtn.addEventListener('click', (e) => {
                console.log(`Download button clicked for track ${trackNumber}`);
                e.preventDefault();
                e.stopPropagation();
                handleDownloadAudio(generatedAudioUrl, title, e);
            });
        } else {
            downloadBtn.disabled = true;
            downloadBtn.classList.add('opacity-50', 'cursor-not-allowed');
            downloadBtn.textContent = 'No audio available';
        }
    } else {
        console.error(`Download button not found for track ${trackNumber}`);
    }
    
    // Handle image display - similar to app.js
    const imageDisplay = playerElement.querySelector('[data-image-display]');
    const imagePlaceholder = playerElement.querySelector('[data-image-placeholder]');
    const imageUrlLink = playerElement.querySelector('[data-image-url]');
    
    let imageUrl = '';
    
    // Try different possible image URL structures (same as in app.js)
    if (track.image_url) {
        imageUrl = track.image_url;  // From user's JSON example
    } else if (track.imageUrl) {
        imageUrl = track.imageUrl;  // From current code
    } else if (track.image_urls && track.image_urls.generated) {
        imageUrl = track.image_urls.generated;  // From process_callback_data
    } else if (track.source_image_url) {
        imageUrl = track.source_image_url;  // Alternative from user's JSON
    } else if (track.sourceImageUrl) {
        imageUrl = track.sourceImageUrl;  // From current code
    } else if (track.cover_image) {
        imageUrl = track.cover_image;  // Alternative field
    }
    
    if (imageUrl) {
        // Set image source and show it
        if (imageDisplay) {
            imageDisplay.src = imageUrl;
            imageDisplay.classList.remove('hidden');
            imageDisplay.style.display = 'block';
        }
        if (imagePlaceholder) {
            imagePlaceholder.style.display = 'none';
        }
        
        // Set the link to view full image
        if (imageUrlLink) {
            imageUrlLink.href = imageUrl;
            imageUrlLink.style.display = 'block';
            imageUrlLink.textContent = 'View full image';
        }
        
        // Add error handling for broken images
        if (imageDisplay) {
            imageDisplay.onerror = function() {
                this.style.display = 'none';
                this.classList.add('hidden');
                if (imagePlaceholder) {
                    imagePlaceholder.style.display = 'flex';
                    imagePlaceholder.innerHTML = '<span class="material-symbols-outlined text-slate-400 text-4xl">broken_image</span>';
                }
                if (imageUrlLink) {
                    imageUrlLink.textContent = 'Image failed to load';
                }
            };
        }
    } else {
        // No image available
        if (imageDisplay) {
            imageDisplay.style.display = 'none';
            imageDisplay.classList.add('hidden');
        }
        if (imagePlaceholder) {
            imagePlaceholder.style.display = 'flex';
            imagePlaceholder.innerHTML = '<span class="material-symbols-outlined text-slate-400 text-4xl">image</span><span class="text-slate-500 ml-2">No image available</span>';
        }
        if (imageUrlLink) {
            imageUrlLink.style.display = 'none';
        }
    }
    
    // Add video button functionality - similar to app.js
    const videoBtn = playerElement.querySelector('[data-video-btn]');
    console.log(`=== Video button check for track ${trackNumber} ===`);
    console.log('Video button element found:', !!videoBtn);
    console.log('Image URL:', imageUrl);
    console.log('Track has image_urls:', track.image_urls);
    
    if (videoBtn) {
        console.log(`Video button details:`, {
            className: videoBtn.className,
            styleDisplay: videoBtn.style.display,
            hasHiddenClass: videoBtn.classList.contains('hidden'),
            textContent: videoBtn.textContent,
            computedStyleDisplay: window.getComputedStyle(videoBtn).display,
            parentElement: videoBtn.parentElement?.className,
            parentStyleDisplay: videoBtn.parentElement ? window.getComputedStyle(videoBtn.parentElement).display : 'no parent'
        });
        
        // TEMPORARY: Always show video button for testing
        console.log(`Showing video button for track ${trackNumber} (temporarily always shown)`);
        videoBtn.style.display = 'block';
        videoBtn.style.visibility = 'visible';
        videoBtn.classList.remove('hidden');
        
        // Force display by setting important
        videoBtn.style.setProperty('display', 'block', 'important');
        
        console.log(`After showing - style.display: ${videoBtn.style.display}, has hidden class: ${videoBtn.classList.contains('hidden')}, computed display: ${window.getComputedStyle(videoBtn).display}`);
        
        videoBtn.addEventListener('click', (e) => {
            console.log(`=== Video button clicked for track ${trackNumber} ===`);
            console.log('Event:', e);
            console.log('Track:', track);
            e.preventDefault();
            e.stopPropagation();
            handleCreateMusicVideoForHistory(track, videoBtn);
        });
        
        console.log(`Event listener added to video button for track ${trackNumber}`);
    } else {
        console.log(`=== ERROR: No video button found in template for track ${trackNumber} ===`);
        // Debug: list all buttons in the player
        const allButtons = playerElement.querySelectorAll('button');
        console.log(`All buttons in player (${allButtons.length}):`);
        Array.from(allButtons).forEach((b, i) => {
            console.log(`Button ${i}:`, {
                className: b.className,
                text: b.textContent?.trim(),
                hasDataVideoBtn: b.hasAttribute('data-video-btn'),
                styleDisplay: b.style.display,
                computedStyleDisplay: window.getComputedStyle(b).display
            });
        });
        
        // Also check for any elements with data-video-btn attribute
        const allVideoBtnElements = playerElement.querySelectorAll('[data-video-btn]');
        console.log(`All elements with data-video-btn attribute: ${allVideoBtnElements.length}`);
        
        // Debug the template HTML
        console.log('Player element HTML:', playerElement.innerHTML);
    }
    
    console.log(`Audio player created successfully for track ${trackNumber}`);
    return playerElement;
}

// Handle audio download
async function handleDownloadAudio(audioUrl, filename, event) {
    console.log('handleDownloadAudio called:', { audioUrl, filename, event });
    
    if (!audioUrl) {
        alert('No audio URL available for download');
        return;
    }
    
    // Extract filename from URL or use provided filename
    let downloadFilename = filename || 'audio';
    
    // Ensure filename has .mp3 extension
    if (!downloadFilename.toLowerCase().endsWith('.mp3')) {
        downloadFilename += '.mp3';
    }
    
    // Clean filename for download
    downloadFilename = downloadFilename.replace(/[^a-zA-Z0-9._-]/g, '_');
    
    console.log('Download filename:', downloadFilename);
    
    // Use server-side proxy for all downloads
    await downloadViaServerProxy(audioUrl, downloadFilename, event);
}

// Download audio using server-side proxy
async function downloadViaServerProxy(audioUrl, filename, event) {
    console.log('Using server-side proxy for:', audioUrl);
    
    try {
        // Show loading state
        const downloadBtn = event?.target;
        if (downloadBtn) {
            const originalText = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '<span class="material-symbols-outlined align-middle mr-2">sync</span> Preparing download...';
            downloadBtn.disabled = true;
        }
        
        // Call our server endpoint to download and stream the audio
        const response = await fetch('/api/download-audio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: audioUrl,
                filename: filename
            })
        });
        
        console.log('Download audio API response status:', response.status);
        
        if (response.ok) {
            // Get the blob from the response
            const blob = await response.blob();
            
            // Create download link and trigger download
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Clean up the object URL
            setTimeout(() => {
                window.URL.revokeObjectURL(url);
            }, 100);
            
            // Show success message
            showDownloadStatus('success', 'Download started! The file will be saved as: ' + filename);
            
        } else {
            // API returned an error
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            console.error('Download audio API error:', errorData);
            const errorMsg = errorData.error || errorData.msg || `Server error: ${response.status}`;
            
            // Try direct download as fallback
            console.log('Falling back to direct download');
            downloadDirectly(audioUrl, filename);
        }
        
    } catch (error) {
        console.error('Error downloading via server proxy:', error);
        
        // Fall back to direct download
        console.log('Falling back to direct download due to error');
        downloadDirectly(audioUrl, filename);
        
    } finally {
        // Restore button state
        const downloadBtn = event?.target;
        if (downloadBtn) {
            downloadBtn.innerHTML = '<span class="material-symbols-outlined align-middle mr-2">download</span> Download';
            downloadBtn.disabled = false;
        }
    }
}

// Direct download fallback
function downloadDirectly(audioUrl, filename) {
    console.log('Direct download fallback for:', audioUrl);
    
    // Try the download attribute
    const link = document.createElement('a');
    link.href = audioUrl;
    link.download = filename;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Show a notification that we're using direct download
    showDownloadStatus('info', 'Using direct download method. If download doesn\'t start, try right-clicking the audio player and selecting "Save as".');
}


// Show download status notification
function showDownloadStatus(type, message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-[100] px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 ${
        type === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
        type === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
        'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
    }`;
    
    const icon = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info';
    notification.innerHTML = `
        <span class="material-symbols-outlined">${icon}</span>
        <span class="font-medium">${message}</span>
        <button class="close-notification ml-4 text-lg">&times;</button>
    `;
    
    // Remove any existing notification
    const existingNotification = document.getElementById('downloadStatusNotification');
    if (existingNotification) {
        document.body.removeChild(existingNotification);
    }
    
    notification.id = 'downloadStatusNotification';
    document.body.appendChild(notification);
    
    // Set up close button
    const closeBtn = notification.querySelector('.close-notification');
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(notification);
    });
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    }, 5000);
}

// Expose NotificationSystem for TrackOptions component
if (!window.NotificationSystem) {
    window.NotificationSystem = {
        showSuccess: showSuccess,
        showError: showError,
        showInfo: (msg) => showNotification('info', msg),
        showWarning: (msg) => showNotification('warning', msg)
    };
}

// Close modal
function closeModal() {
    if (historyModal) {
        historyModal.classList.add('hidden');
    }
}

// Cleanup old history (15+ days)
async function cleanupHistory() {
    if (!confirm('Clean up history entries older than 15 days? This action cannot be undone.')) {
        return;
    }
    
    if (cleanupBtn) {
        cleanupBtn.disabled = true;
        cleanupBtn.innerHTML = '<span class="material-symbols-outlined mr-2">sync</span> Cleaning...';
    }
    
    try {
        const response = await fetch('/api/history/cleanup?days=15&auto=true', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (response.ok && data.success) {
            alert(`History cleanup completed. Removed ${data.removed_count} entries older than 15 days. ${data.remaining_count} entries remain.`);
            loadHistory(); // Reload history
        } else {
            throw new Error(data.error || 'Cleanup failed');
        }
    } catch (error) {
        console.error('Error cleaning up history:', error);
        alert(`Cleanup failed: ${error.message}`);
    } finally {
        if (cleanupBtn) {
            cleanupBtn.disabled = false;
            cleanupBtn.innerHTML = '<span class="material-symbols-outlined mr-2">delete</span> Cleanup';
        }
    }
}

// Video Modal Functions for History Page
let videoCreationModal = null;
let closeVideoModalBtn = null;
let cancelVideoBtn = null;
let createVideoBtn = null;
let modalTaskId = null;
let modalAudioId = null;
let modalSongTitleContainer = null;
let modalSongTitle = null;
let modalStatusMessage = null;
let modalStatusText = null;
let modalAuthor = null;
let modalDomainName = null;

function initVideoModalElements() {
    if (!videoCreationModal) {
        videoCreationModal = document.getElementById('videoCreationModal');
        closeVideoModalBtn = document.getElementById('closeVideoModalBtn');
        cancelVideoBtn = document.getElementById('cancelVideoBtn');
        createVideoBtn = document.getElementById('createVideoBtn');
        modalTaskId = document.getElementById('modalTaskId');
        modalAudioId = document.getElementById('modalAudioId');
        modalSongTitleContainer = document.getElementById('modalSongTitleContainer');
        modalSongTitle = document.getElementById('modalSongTitle');
        modalStatusMessage = document.getElementById('modalStatusMessage');
        modalStatusText = document.getElementById('modalStatusText');
        modalAuthor = document.getElementById('modalAuthor');
        modalDomainName = document.getElementById('modalDomainName');
    }
}

function showVideoModal(song) {
    console.log('showVideoModal called with song:', song);
    
    // Initialize modal elements if needed
    initVideoModalElements();
    
    if (!videoCreationModal || !modalTaskId || !modalAudioId) {
        console.error('Modal elements not found.');
        return;
    }
    
    // Get the task ID from the song
    const taskId = song.task_id;
    const audioId = song.id;
    
    console.log('Task ID:', taskId, 'Audio ID:', audioId);
    
    if (!taskId || !audioId) {
        console.error('Missing task ID or audio ID:', { taskId, audioId });
        showError('Cannot create music video: Missing task ID or audio ID');
        return;
    }
    
    // Populate modal fields
    modalTaskId.value = taskId;
    modalAudioId.value = audioId;
    
    // Show song title if available
    if (song.title) {
        modalSongTitle.textContent = song.title;
        modalSongTitleContainer.classList.remove('hidden');
        console.log('Song title shown:', song.title);
    } else {
        modalSongTitleContainer.classList.add('hidden');
    }
    
    // Set empty values for author and domain name (user will fill them)
    if (modalAuthor) {
        modalAuthor.value = '';
    }
    if (modalDomainName) {
        modalDomainName.value = '';
    }
    
    // Hide status message
    modalStatusMessage.classList.add('hidden');
    
    // Store the current song data on the create button
    createVideoBtn.dataset.song = JSON.stringify(song);
    createVideoBtn.disabled = false;
    createVideoBtn.innerHTML = '<span class="material-symbols-outlined mr-2 text-sm">movie</span> Create Video';
    
    // Show modal
    console.log('Showing modal...');
    videoCreationModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    console.log('Modal should be visible now');
}

function closeVideoModal() {
    initVideoModalElements();
    if (videoCreationModal) {
        videoCreationModal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

async function handleModalCreateVideo() {
    // Initialize modal elements if needed
    initVideoModalElements();
    
    if (!createVideoBtn || !createVideoBtn.dataset.song) {
        showError('No song data available');
        return;
    }
    
    try {
        const song = JSON.parse(createVideoBtn.dataset.song);
        
        // Check for image URL using all possible property names
        const hasImageUrl = song.image_url ||
                           song.imageUrl ||
                           (song.image_urls && song.image_urls.generated) ||
                           song.source_image_url ||
                           song.sourceImageUrl;
        
        // Validate required fields
        if (!song.id || !hasImageUrl) {
            showError('Cannot create music video: Missing audio ID or image URL');
            closeVideoModal();
            return;
        }
        
        const taskId = song.task_id;
        if (!taskId) {
            showError('Cannot create music video: Missing task ID');
            closeVideoModal();
            return;
        }
        
        // Show loading state in modal
        createVideoBtn.disabled = true;
        createVideoBtn.innerHTML = '<span class="material-symbols-outlined mr-2 text-sm">sync</span> Creating...';
        
        // Show status message
        if (modalStatusText) {
            modalStatusText.textContent = 'Starting video generation...';
        }
        if (modalStatusMessage) {
            modalStatusMessage.classList.remove('hidden');
        }
        
        // Call the actual video creation function
        await createVideoFromModal(taskId, song);
        
    } catch (error) {
        console.error('Error parsing song data:', error);
        showError('Failed to parse song data');
        closeVideoModal();
    }
}

async function createVideoFromModal(taskId, song) {
    try {
        // Initialize modal elements if needed
        initVideoModalElements();
        
        // Get values from input fields
        const author = modalAuthor ? modalAuthor.value.trim() : 'Music Cover Generator';
        const domainName = modalDomainName ? modalDomainName.value.trim() : (window.location.hostname || 'music.example.com');
        
        // Request video generation
        const response = await fetch('/api/generate-music-video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task_id: taskId,
                audio_id: song.id,
                author: author,
                domain_name: domainName
            })
        });
        
        const data = await response.json();
        
        // Check for success - accept either code 0 or 200 (based on API documentation)
        // Handle both taskId (camelCase) and task_id (snake_case) from API responses
        const videoTaskId = data.data?.taskId || data.data?.task_id;
        const isSuccess = response.ok && data.data && videoTaskId && (data.code === 0 || data.code === 200);
        
        if (isSuccess) {
            // Update modal status
            modalStatusText.textContent = 'Video generation started! Task ID: ' + videoTaskId;
            modalStatusMessage.classList.remove('hidden');
            
            // Close modal after a short delay
            setTimeout(() => {
                closeVideoModal();
                showSuccess('Music video generation started! Tracking progress...');
                
                // Note: Video player creation and polling would be implemented here
                // createVideoPlayer(song, videoTaskId);
                // pollVideoStatus(videoTaskId, song);
                
            }, 1500);
            
        } else {
            throw new Error(data.msg || `Video generation failed (code: ${data.code})`);
        }
    } catch (error) {
        console.error('Video creation error:', error);
        if (modalStatusText) {
            modalStatusText.textContent = 'Error: ' + error.message;
        }
        if (modalStatusMessage) {
            modalStatusMessage.classList.remove('hidden');
        }
        
        // Reset button state
        if (createVideoBtn) {
            createVideoBtn.disabled = false;
            createVideoBtn.innerHTML = '<span class="material-symbols-outlined mr-2 text-sm">movie</span> Create Video';
        }
        
        // Show error notification
        setTimeout(() => {
            showError(`Failed to create music video: ${error.message}`);
        }, 500);
    }
}

// Music Video Generation Functions for History Modal
function handleCreateMusicVideoForHistory(track, videoBtn) {
    console.log('=== handleCreateMusicVideoForHistory called ===');
    console.log('Track:', track);
    console.log('Video button:', videoBtn);
    
    // Get image URL using the same logic as createAudioPlayer
    let imageUrl = '';
    if (track.image_url) {
        imageUrl = track.image_url;
    } else if (track.imageUrl) {
        imageUrl = track.imageUrl;
    } else if (track.image_urls && track.image_urls.generated) {
        imageUrl = track.image_urls.generated;
    } else if (track.source_image_url) {
        imageUrl = track.source_image_url;
    } else if (track.sourceImageUrl) {
        imageUrl = track.sourceImageUrl;
    } else if (track.cover_image) {
        imageUrl = track.cover_image;
    }
    
    console.log('Image URL found:', imageUrl);
    console.log('Track ID:', track.id);
    console.log('Task ID:', track.task_id);
    
    if (!track.id || !imageUrl) {
        console.error('Cannot create music video: Missing audio ID or image URL');
        showError('Cannot create music video: Missing audio ID or image URL');
        return;
    }
    
    // Get task ID from the track (added in createAudioPlayer)
    const taskId = track.task_id;
    if (!taskId) {
        console.error('Cannot create music video: Missing task ID');
        showError('Cannot create music video: Missing task ID');
        return;
    }
    
    // Create a song object compatible with showVideoModal
    const song = {
        id: track.id,
        task_id: taskId,
        image_url: imageUrl,
        title: track.title || track.name || 'Generated Track'
    };
    
    console.log('Created song object:', song);
    
    // Show the modal dialog
    console.log('Calling showVideoModal...');
    showVideoModal(song);
}

// Fallback function for direct video creation (if modal not available)
async function createVideoDirectly(taskId, track, videoBtn) {
    try {
        // Show loading state
        if (videoBtn) {
            videoBtn.disabled = true;
            videoBtn.innerHTML = '<span class="material-symbols-outlined mr-2">sync</span> Creating Video...';
        }
        
        // Request video generation
        const response = await fetch('/api/generate-music-video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task_id: taskId,
                audio_id: track.id,
                author: 'Music Cover Generator',
                domain_name: window.location.hostname || 'music.example.com'
            })
        });
        
        const data = await response.json();
        
        // Handle both taskId (camelCase) and task_id (snake_case) from API responses
        const videoTaskId = data.data?.taskId || data.data?.task_id;
        if (response.ok && data.code === 0 && data.data && videoTaskId) {
            showSuccess('Music video generation started! Tracking progress...');
            
            // Create and display video player
            createVideoPlayerForHistory(track, videoTaskId, videoBtn);
            
            // Start polling for video status
            pollVideoStatusForHistory(videoTaskId, track);
        } else {
            throw new Error(data.msg || 'Video generation failed');
        }
    } catch (error) {
        showError(`Failed to create music video: ${error.message}`);
        
        // Reset button state
        if (videoBtn) {
            videoBtn.disabled = false;
            videoBtn.innerHTML = '<span class="material-symbols-outlined mr-2">movie</span> Create Music Video';
        }
    }
}

function createVideoPlayerForHistory(track, videoTaskId, videoBtn) {
    const container = document.getElementById('audioPlayersContainer');
    const template = document.getElementById('videoPlayerTemplate');
    
    if (!template) {
        console.error('Video player template not found');
        return;
    }
    
    const clone = template.content.cloneNode(true);
    
    // Set video title
    const videoTitle = clone.querySelector('[data-video-title]');
    videoTitle.textContent = `Music Video: ${track.title || 'Generated Track'}`;
    
    // Set video task ID
    const taskIdElement = clone.querySelector('[data-video-task-id]');
    taskIdElement.textContent = videoTaskId;
    
    // Store references for updates
    const videoPlayer = clone.querySelector('.video-player');
    videoPlayer.dataset.videoTaskId = videoTaskId;
    videoPlayer.dataset.audioId = track.id;
    
    // Find the corresponding audio player and insert video player after it
    const audioPlayer = videoBtn.closest('.audio-player');
    if (audioPlayer) {
        audioPlayer.insertAdjacentElement('afterend', videoPlayer);
    } else {
        // If can't find specific audio player, append to container
        container.appendChild(videoPlayer);
    }
}

async function pollVideoStatusForHistory(videoTaskId, track) {
    const pollInterval = 10000; // 10 seconds for video generation
    
    const poll = async () => {
        try {
            // Note: We need a video status endpoint, but for now we'll simulate
            // In a real implementation, we would call a video status API
            // For now, we'll simulate progress and assume success after some time
            
            const videoPlayer = document.querySelector(`.video-player[data-video-task-id="${videoTaskId}"]`);
            if (!videoPlayer) {
                console.log('Video player not found, stopping polling');
                return;
            }
            
            const progressBar = videoPlayer.querySelector('[data-video-progress]');
            const statusText = videoPlayer.querySelector('[data-video-status-text]');
            const statusContainer = videoPlayer.querySelector('[data-video-status-container]');
            const videoContainer = videoPlayer.querySelector('[data-video-container]');
            const videoElement = videoPlayer.querySelector('[data-video]');
            const videoUrlLink = videoPlayer.querySelector('[data-video-url]');
            const downloadBtn = videoPlayer.querySelector('[data-video-download-btn]');
            
            // Simulate progress (in real implementation, call API)
            const currentProgress = parseInt(progressBar.value) || 0;
            let newProgress = currentProgress + 20;
            
            if (newProgress >= 100) {
                newProgress = 100;
                
                // Simulate video URL (in real implementation, get from API response)
                const mockVideoUrl = 'https://example.com/generated-video.mp4';
                
                // Update UI for completed video
                progressBar.value = 100;
                statusText.textContent = 'Video generation complete!';
                statusContainer.style.display = 'none';
                videoContainer.style.display = 'block';
                
                // Set video source
                videoElement.src = mockVideoUrl;
                videoUrlLink.href = mockVideoUrl;
                videoUrlLink.style.display = 'block';
                videoUrlLink.textContent = 'View video';
                
                // Show download button
                downloadBtn.style.display = 'block';
                downloadBtn.addEventListener('click', () => {
                    handleDownloadVideoForHistory(mockVideoUrl, `${track.title || 'music-video'}.mp4`);
                });
                
                showSuccess('Music video generated successfully!');
                return; // Stop polling
            } else {
                progressBar.value = newProgress;
                statusText.textContent = `Processing video... ${newProgress}%`;
                
                // Continue polling
                setTimeout(poll, pollInterval);
            }
        } catch (error) {
            console.error('Error polling video status:', error);
            // Retry after delay
            setTimeout(poll, pollInterval);
        }
    };
    
    // Start polling
    setTimeout(poll, 2000);
}

function handleDownloadVideoForHistory(videoUrl, filename) {
    if (!videoUrl) {
        showError('No video URL available for download');
        return;
    }
    
    // Create download link
    const a = document.createElement('a');
    a.href = videoUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    showSuccess('Video download started!');
}

// Helper function to show success/error notifications in history modal
function showSuccess(message) {
    console.log('Success:', message);
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-md';
    notification.innerHTML = `
        <div class="flex items-center">
            <span class="material-symbols-outlined mr-2">check_circle</span>
            <span class="font-medium">${message}</span>
            <button class="ml-auto text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                <span class="material-symbols-outlined">close</span>
            </button>
        </div>
    `;
    document.body.appendChild(notification);
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function showError(message) {
    console.error('Error:', message);
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-md';
    notification.innerHTML = `
        <div class="flex items-center">
            <span class="material-symbols-outlined mr-2">error</span>
            <span class="font-medium">${message}</span>
            <button class="ml-auto text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                <span class="material-symbols-outlined">close</span>
            </button>
        </div>
    `;
    document.body.appendChild(notification);
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Create video player for history entry
function createVideoPlayerForHistoryEntry(entry, videoUrl) {
    console.log('=== createVideoPlayerForHistoryEntry called ===');
    console.log('Entry:', entry);
    console.log('Video URL:', videoUrl);
    
    // Debug: List all templates in document
    const allTemplates = document.querySelectorAll('template');
    console.log(`Total templates in document: ${allTemplates.length}`);
    allTemplates.forEach((t, i) => {
        console.log(`Template ${i}: id="${t.id}"`);
    });
    
    const template = document.getElementById('videoPlayerTemplate');
    console.log('videoPlayerTemplate found:', !!template);
    console.log('template element:', template);
    
    if (!template) {
        console.error('Video player template not found. Available templates:');
        const templates = document.querySelectorAll('template');
        templates.forEach(t => console.log(`- ${t.id || 'no-id'}`));
        
        // Try to create a simple video player as fallback
        console.log('Creating fallback video player');
        const fallbackPlayer = document.createElement('div');
        fallbackPlayer.className = 'video-player border border-blue-200 dark:border-blue-800 rounded-lg p-4 bg-blue-50 dark:bg-blue-900/20 mt-6';
        fallbackPlayer.innerHTML = `
            <div class="flex justify-between items-start mb-3">
                <div>
                    <h5 class="font-bold text-slate-900 dark:text-white text-lg">Music Video</h5>
                    <div class="flex items-center gap-3 mt-1">
                        <span class="text-xs px-2 py-1 bg-blue-500/10 text-blue-500 rounded-full">Video</span>
                        <span class="text-xs text-slate-500">Ready</span>
                    </div>
                </div>
                <button class="btn-video-download px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors flex items-center justify-center">
                    <span class="material-symbols-outlined mr-2">download</span>
                    Download MP4
                </button>
            </div>
            
            <div class="video-player-container mb-3">
                <video controls class="w-full rounded-lg">
                    <source src="${videoUrl}" type="video/mp4">
                    Your browser does not support the video element.
                </video>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                    <label class="block text-sm font-medium mb-1">Video Task ID</label>
                    <code class="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-sm">${entry.task_id || 'N/A'}</code>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Video URL</label>
                    <a href="${videoUrl}" target="_blank" class="text-blue-500 hover:underline break-all text-sm">View video</a>
                </div>
            </div>
        `;
        
        // Add download button event listener
        const downloadBtn = fallbackPlayer.querySelector('.btn-video-download');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                handleDownloadVideoForHistory(videoUrl, `music-video-${entry.task_id || 'generated'}.mp4`);
            });
        }
        
        return fallbackPlayer;
    }
    
    const player = template.content.cloneNode(true);
    const playerElement = player.querySelector('.video-player');
    console.log('playerElement found:', !!playerElement);
    
    if (!playerElement) {
        console.error('Could not find .video-player element in template');
        // Debug: List all elements in the cloned content
        const allElements = player.querySelectorAll('*');
        console.log(`Elements in cloned content: ${allElements.length}`);
        allElements.forEach((el, i) => {
            console.log(`Element ${i}: ${el.tagName} class="${el.className}"`);
        });
        return document.createElement('div');
    }
    
    // Set video information
    const videoTitle = playerElement.querySelector('[data-video-title]');
    const taskIdElement = playerElement.querySelector('[data-video-task-id]');
    const videoUrlLink = playerElement.querySelector('[data-video-url]');
    const videoElement = playerElement.querySelector('[data-video]');
    const videoContainer = playerElement.querySelector('[data-video-container]');
    const videoStatusContainer = playerElement.querySelector('[data-video-status-container]');
    const videoProgress = playerElement.querySelector('[data-video-progress]');
    const videoStatusText = playerElement.querySelector('[data-video-status-text]');
    const downloadBtn = playerElement.querySelector('[data-video-download-btn]');
    
    console.log('Video player elements found:', {
        videoTitle: !!videoTitle,
        taskIdElement: !!taskIdElement,
        videoUrlLink: !!videoUrlLink,
        videoElement: !!videoElement,
        videoContainer: !!videoContainer,
        videoStatusContainer: !!videoStatusContainer,
        videoProgress: !!videoProgress,
        videoStatusText: !!videoStatusText,
        downloadBtn: !!downloadBtn
    });
    
    // Set title
    if (videoTitle) {
        videoTitle.textContent = 'Generated Music Video';
    }
    
    // Set task ID
    if (taskIdElement) {
        taskIdElement.textContent = entry.task_id || 'N/A';
    }
    
    if (videoUrl) {
        // Video is available
        if (videoUrlLink) {
            videoUrlLink.href = videoUrl;
            videoUrlLink.textContent = videoUrl.length > 50 ? videoUrl.substring(0, 50) + '...' : videoUrl;
            videoUrlLink.style.display = 'block';
        }
        
        if (videoElement) {
            videoElement.src = videoUrl;
        }
        
        // Show video container, hide status container
        if (videoContainer) {
            videoContainer.style.display = 'block';
        }
        if (videoStatusContainer) {
            videoStatusContainer.style.display = 'none';
        }
        
        // Set progress to 100%
        if (videoProgress) {
            videoProgress.value = 100;
        }
        if (videoStatusText) {
            videoStatusText.textContent = 'Video generation complete!';
        }
        
        // Show download button
        if (downloadBtn) {
            downloadBtn.style.display = 'block';
            downloadBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                handleDownloadVideoForHistory(videoUrl, `music-video-${entry.task_id || 'generated'}.mp4`);
            });
        }
    } else {
        // Video is still processing or failed
        if (videoStatusText) {
            videoStatusText.textContent = entry.status_message || 'Video generation in progress...';
        }
        
        // Hide video container, show status container
        if (videoContainer) {
            videoContainer.style.display = 'none';
        }
        if (videoStatusContainer) {
            videoStatusContainer.style.display = 'block';
        }
        
        // Hide download button
        if (downloadBtn) {
            downloadBtn.style.display = 'none';
        }
    }
    
    console.log('Video player created successfully');
    return playerElement;
}


// Helper function to show notification
function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-[100] px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 ${
        type === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
        type === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
        'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
    }`;
    
    const icon = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info';
    notification.innerHTML = `
        <span class="material-symbols-outlined">${icon}</span>
        <span class="font-medium">${message}</span>
        <button class="close-notification ml-4 text-lg">&times;</button>
    `;
    
    // Remove any existing notification
    const existingNotification = document.getElementById('globalNotification');
    if (existingNotification) {
        document.body.removeChild(existingNotification);
    }
    
    notification.id = 'globalNotification';
    document.body.appendChild(notification);
    
    // Set up close button
    const closeBtn = notification.querySelector('.close-notification');
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(notification);
    });
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    }, 5000);
}