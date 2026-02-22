/* ─────────────────────────────────────────────
   Admin Dashboard — AudioCraft
   js/pages/admin.js
   ───────────────────────────────────────────── */

// ── CSRF ──────────────────────────────────────
async function ensureCsrfToken() {
    if (window.csrfToken) return window.csrfToken;
    const r = await fetch('/auth/csrf-token', { credentials: 'same-origin' });
    const d = await r.json();
    window.csrfToken = d.csrf_token;
    return window.csrfToken;
}

async function apiFetch(path, options) {
    const opts = options ? { ...options } : {};
    opts.credentials = 'same-origin';
    const method = (opts.method || 'GET').toUpperCase();
    if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
        const csrf = await ensureCsrfToken();
        opts.headers = { ...(opts.headers || {}), 'X-CSRFToken': csrf };
    }
    return fetch(path, opts);
}

// ── Error Banner ──────────────────────────────
function showAdminError(msg) {
    const el  = document.getElementById('adminError');
    const txt = document.getElementById('adminErrorText');
    if (!el || !txt) return;
    txt.textContent = msg;
    el.classList.remove('hidden');
}
function clearAdminError() {
    const el = document.getElementById('adminError');
    if (el) el.classList.add('hidden');
}

// ── Toast Notifications ───────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const styles = {
        success: 'bg-emerald-900/95 border-emerald-500/30 text-emerald-100',
        error:   'bg-red-900/95 border-red-500/30 text-red-100',
        warning: 'bg-amber-900/95 border-amber-500/30 text-amber-100',
        info:    'bg-slate-800/95 border-slate-600/30 text-slate-200',
    };
    const icons = { success: 'check_circle', error: 'error', warning: 'warning', info: 'info' };

    const toast = document.createElement('div');
    toast.className = [
        'pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl border shadow-2xl',
        'backdrop-blur-md text-sm font-medium opacity-0 translate-x-4 transition-all duration-300',
        styles[type] || styles.info,
    ].join(' ');
    toast.innerHTML = `
        <span class="material-symbols-outlined text-base shrink-0 mt-0.5 msf">${icons[type] || 'info'}</span>
        <span class="flex-1 leading-snug">${message}</span>
        <button onclick="this.closest('div').remove()" class="opacity-60 hover:opacity-100 transition-opacity shrink-0 ml-1">
            <span class="material-symbols-outlined text-sm">close</span>
        </button>
    `;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            toast.classList.remove('opacity-0', 'translate-x-4');
        });
    });

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-x-4');
        setTimeout(() => toast.remove(), 350);
    }, 4000);
}

// ── Role Badge Helpers ────────────────────────
const ROLE_COLORS = {
    admin:     'bg-violet-500/15 text-violet-300 border-violet-500/25',
    moderator: 'bg-amber-500/15 text-amber-300 border-amber-500/25',
    creator:   'bg-blue-500/15 text-blue-300 border-blue-500/25',
    premium:   'bg-emerald-500/15 text-emerald-300 border-emerald-500/25',
    user:      'bg-slate-500/15 text-slate-400 border-slate-500/25',
};
function roleClass(name) {
    return ROLE_COLORS[name.toLowerCase()] || 'bg-slate-500/15 text-slate-400 border-slate-500/25';
}
function roleBadge(name) {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${roleClass(name)}">${name}</span>`;
}
function roleBadgesHtml(roles) {
    if (!roles || roles.length === 0)
        return `<span class="text-xs text-slate-600 italic">No roles</span>`;
    return roles.map(roleBadge).join('');
}

// ── Avatar Helpers ────────────────────────────
const AVATAR_COLORS = [
    'bg-blue-600', 'bg-violet-600', 'bg-emerald-600',
    'bg-amber-600', 'bg-rose-600',  'bg-cyan-600',
    'bg-pink-600',  'bg-indigo-600',
];
function avatarColor(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) h = str.charCodeAt(i) + ((h << 5) - h);
    return AVATAR_COLORS[Math.abs(h) % AVATAR_COLORS.length];
}
function avatarInitial(u) {
    if (u.display_name) return u.display_name.charAt(0).toUpperCase();
    if (u.email)        return u.email.charAt(0).toUpperCase();
    return '?';
}

// ── Stats Counter Animation ───────────────────
function animateCounter(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    let cur = 0;
    const step = Math.max(1, Math.ceil(target / 25));
    const timer = setInterval(() => {
        cur = Math.min(cur + step, target);
        el.textContent = cur;
        if (cur >= target) clearInterval(timer);
    }, 35);
}

function renderStats(users, roleNames) {
    animateCounter('statTotalUsers', users.length);
    animateCounter('statAdmins', users.filter(u => (u.roles || []).includes('admin')).length);
    animateCounter('statRoles', roleNames.length);
}

// ── System Status ─────────────────────────────
function renderSystemStatus(checks) {
    const container = document.getElementById('statusChecks');
    if (!container) return;

    const allOk = checks.every(c => c.ok);
    const badge = document.getElementById('overallStatusBadge');
    const dot   = document.getElementById('overallStatusDot');
    const txt   = document.getElementById('overallStatusText');

    if (badge && dot && txt) {
        if (allOk) {
            badge.className = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 border border-emerald-500/20 text-emerald-300';
            dot.className   = 'w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]';
            txt.textContent = 'All Systems Operational';
        } else {
            badge.className = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 border border-red-500/20 text-red-300';
            dot.className   = 'w-1.5 h-1.5 rounded-full bg-red-400';
            txt.textContent = 'Degraded';
        }
    }

    container.innerHTML = checks.map(c => {
        const ok = c.ok;
        return `
            <div class="flex items-center gap-3 p-3 rounded-lg ${ok ? 'bg-emerald-500/5 border border-emerald-500/15' : 'bg-red-500/5 border border-red-500/15'}">
                <span class="material-symbols-outlined text-base shrink-0 msf ${ok ? 'text-emerald-400' : 'text-red-400'}">${ok ? 'check_circle' : 'error'}</span>
                <div class="min-w-0">
                    <p class="text-slate-300 text-xs font-semibold truncate">${c.name}</p>
                    <p class="text-xs ${ok ? 'text-emerald-500' : 'text-red-400'}">${ok ? 'Operational' : (c.error || 'Error')}</p>
                </div>
            </div>`;
    }).join('');
}

// ── Table Skeleton ────────────────────────────
function showTableSkeleton() {
    const container = document.getElementById('adminUsersTable');
    if (!container) return;
    const skRow = `
        <tr class="border-b border-slate-800/60">
            <td class="px-5 py-3.5">
                <div class="flex items-center gap-3">
                    <div class="skeleton w-9 h-9 rounded-full shrink-0"></div>
                    <div class="space-y-1.5 flex-1">
                        <div class="skeleton h-3 rounded w-28"></div>
                        <div class="skeleton h-2.5 rounded w-40"></div>
                    </div>
                </div>
            </td>
            <td class="px-5 py-3.5"><div class="skeleton h-5 rounded-md w-20"></div></td>
            <td class="px-5 py-3.5"><div class="flex justify-end gap-2">
                <div class="skeleton h-7 w-16 rounded-lg"></div>
                <div class="skeleton h-7 w-8 rounded-lg"></div>
            </div></td>
        </tr>`;
    container.innerHTML = `
        <table class="w-full text-sm">
            <thead class="bg-slate-950/50 border-b border-slate-800">
                <tr>
                    <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">User</th>
                    <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Roles</th>
                    <th class="px-5 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody>${skRow.repeat(5)}</tbody>
        </table>`;
}

// ── Users Table ───────────────────────────────
function renderUsersTable(users, roleNames) {
    const container = document.getElementById('adminUsersTable');
    if (!container) return;

    if (users.length === 0) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-20 text-center">
                <span class="material-symbols-outlined text-5xl text-slate-700 mb-3">person_search</span>
                <p class="text-slate-400 font-semibold">No users found</p>
                <p class="text-slate-600 text-sm mt-1">Try adjusting your search query</p>
            </div>`;
        return;
    }

    const rows = users.map(u => {
        const bg      = avatarColor(u.email || u.id || '?');
        const initial = avatarInitial(u);
        const badges  = roleBadgesHtml(u.roles);

        const checkboxes = roleNames.map(name => {
            const checked = (u.roles || []).includes(name) ? 'checked' : '';
            return `
                <label class="flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-slate-700/60 cursor-pointer select-none transition-colors">
                    <input type="checkbox" ${checked} value="${name}" data-role-checkbox class="w-3.5 h-3.5 rounded accent-blue-500 cursor-pointer">
                    <span class="text-sm text-slate-300">${name}</span>
                    <span class="ml-auto">${roleBadge(name)}</span>
                </label>`;
        }).join('');

        return `
            <tr class="border-b border-slate-800/60 hover:bg-slate-800/20 transition-colors" data-user-id="${u.id}">
                <td class="px-5 py-3.5">
                    <div class="flex items-center gap-3">
                        <div class="w-9 h-9 rounded-full ${bg} flex items-center justify-center text-white text-sm font-bold shrink-0 shadow-md">
                            ${initial}
                        </div>
                        <div class="min-w-0">
                            <p class="text-slate-200 text-sm font-medium truncate">${u.display_name || '—'}</p>
                            <p class="text-slate-500 text-xs truncate">${u.email || ''}</p>
                        </div>
                    </div>
                </td>
                <td class="px-5 py-3.5">
                    <div class="flex items-center flex-wrap gap-1" id="roleBadges-${u.id}">${badges}</div>
                </td>
                <td class="px-5 py-3.5">
                    <div class="flex items-center justify-end gap-2">
                        <!-- Roles popover trigger -->
                        <div class="relative">
                            <button data-edit-roles="${u.id}"
                                class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white hover:border-slate-600 transition-all">
                                <span class="material-symbols-outlined text-sm">tune</span>
                                Roles
                            </button>
                            <!-- Popover -->
                            <div data-role-popover="${u.id}"
                                class="hidden absolute right-0 top-full mt-1.5 z-30 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl overflow-hidden w-52 animate-fade-in">
                                <div class="px-3 py-2 border-b border-slate-700 bg-slate-900/60">
                                    <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Assign Roles</p>
                                </div>
                                <div class="p-1.5 space-y-0.5">${checkboxes}</div>
                                <div class="flex justify-end gap-1.5 p-2 border-t border-slate-700 bg-slate-900/60">
                                    <button data-cancel-roles="${u.id}"
                                        class="px-2.5 py-1 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-colors">
                                        Cancel
                                    </button>
                                    <button data-save-user-id="${u.id}"
                                        class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-blue-600 text-white hover:bg-blue-500 transition-colors">
                                        <span class="material-symbols-outlined text-xs">save</span>
                                        Save
                                    </button>
                                </div>
                            </div>
                        </div>
                        <!-- Delete -->
                        <button data-delete-user-id="${u.id}" data-user-email="${u.email}"
                            class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 border border-slate-700 text-red-400 hover:bg-red-500/10 hover:text-red-300 hover:border-red-500/30 transition-all">
                            <span class="material-symbols-outlined text-sm">delete</span>
                        </button>
                    </div>
                </td>
            </tr>`;
    }).join('');

    container.innerHTML = `
        <table class="w-full text-sm">
            <thead class="bg-slate-950/50 border-b border-slate-800">
                <tr>
                    <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">User</th>
                    <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Roles</th>
                    <th class="px-5 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/40">${rows}</tbody>
        </table>
        <div class="px-5 py-3 border-t border-slate-800 bg-slate-900/30">
            <p class="text-xs text-slate-600">${users.length} user${users.length !== 1 ? 's' : ''} displayed</p>
        </div>`;

    wireTableEvents(container);
}

function wireTableEvents(container) {
    function closePopovers() {
        container.querySelectorAll('[data-role-popover]').forEach(p => p.classList.add('hidden'));
    }

    // Toggle popover
    container.querySelectorAll('[data-edit-roles]').forEach(btn => {
        btn.addEventListener('click', e => {
            e.stopPropagation();
            const uid     = btn.dataset.editRoles;
            const popover = container.querySelector(`[data-role-popover="${uid}"]`);
            const wasHidden = popover.classList.contains('hidden');
            closePopovers();
            if (wasHidden) popover.classList.remove('hidden');
        });
    });

    // Cancel
    container.querySelectorAll('[data-cancel-roles]').forEach(btn => {
        btn.addEventListener('click', e => {
            e.stopPropagation();
            container.querySelector(`[data-role-popover="${btn.dataset.cancelRoles}"]`).classList.add('hidden');
        });
    });

    // Save roles
    container.querySelectorAll('[data-save-user-id]').forEach(btn => {
        btn.addEventListener('click', async e => {
            e.stopPropagation();
            clearAdminError();
            const uid     = btn.dataset.saveUserId;
            const popover = container.querySelector(`[data-role-popover="${uid}"]`);
            const roles   = Array.from(popover.querySelectorAll('[data-role-checkbox]:checked')).map(cb => cb.value);

            const orig = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = `<span class="material-symbols-outlined text-xs spin">refresh</span>`;

            try {
                const resp = await apiFetch(`/api/admin/users/${uid}/roles`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ roles }),
                });
                const data = await resp.json().catch(() => ({}));
                if (!resp.ok) {
                    showToast(data.error || `Failed to update roles (HTTP ${resp.status})`, 'error');
                } else {
                    showToast('Roles updated successfully', 'success');
                    const badgeEl = document.getElementById(`roleBadges-${uid}`);
                    if (badgeEl) badgeEl.innerHTML = roleBadgesHtml(roles);
                }
            } catch (err) {
                showToast(`Network error: ${err.message}`, 'error');
            }

            btn.disabled = false;
            btn.innerHTML = orig;
            popover.classList.add('hidden');
        });
    });

    // Delete
    container.querySelectorAll('[data-delete-user-id]').forEach(btn => {
        btn.addEventListener('click', () => openDeleteModal(btn.dataset.deleteUserId, btn.dataset.userEmail));
    });

    // Click outside to close popovers
    document.addEventListener('click', closePopovers, { once: false });
}

// ── Delete Modal ──────────────────────────────
let _deleteTargetId = null;

function openDeleteModal(userId, userEmail) {
    _deleteTargetId = userId;
    document.getElementById('deleteModalUserEmail').textContent  = userEmail;
    document.getElementById('deleteConfirmationInput').value     = '';
    document.getElementById('confirmDeleteBtn').disabled         = true;
    document.getElementById('deleteUserModal').classList.remove('hidden');
    setTimeout(() => document.getElementById('deleteConfirmationInput').focus(), 60);
}

function initDeleteModal() {
    const modal   = document.getElementById('deleteUserModal');
    const input   = document.getElementById('deleteConfirmationInput');
    const cancel  = document.getElementById('cancelDeleteBtn');
    const confirm = document.getElementById('confirmDeleteBtn');
    const spinner = document.getElementById('deleteSpinner');
    if (!modal) return;

    function closeModal() {
        modal.classList.add('hidden');
        input.value = '';
        _deleteTargetId = null;
        confirm.disabled = true;
    }

    input.addEventListener('input', () => { confirm.disabled = input.value !== 'DELETE'; });
    cancel.addEventListener('click', closeModal);
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

    confirm.addEventListener('click', async () => {
        if (!_deleteTargetId) return;
        confirm.disabled = true;
        spinner.classList.remove('hidden');
        try {
            const resp = await apiFetch(`/api/admin/users/${_deleteTargetId}`, { method: 'DELETE' });
            if (resp.ok) {
                showToast('User deleted', 'success');
                closeModal();
                loadAdmin();
            } else {
                const data = await resp.json().catch(() => ({}));
                showToast(data.error || `Delete failed (HTTP ${resp.status})`, 'error');
                closeModal();
            }
        } catch (err) {
            showToast(`Network error: ${err.message}`, 'error');
            closeModal();
        } finally {
            spinner.classList.add('hidden');
        }
    });
}

// ── Refresh Spinner ───────────────────────────
function setRefreshing(on) {
    const icon = document.getElementById('refreshIcon');
    if (!icon) return;
    on ? icon.classList.add('spin') : icon.classList.remove('spin');
}

function stampLastUpdated() {
    const el = document.getElementById('lastUpdated');
    const t  = document.getElementById('lastUpdatedTime');
    if (!el || !t) return;
    t.textContent = new Date().toLocaleTimeString();
    el.classList.remove('hidden');
}

// ── Main Load ─────────────────────────────────
async function loadAdmin() {
    clearAdminError();
    setRefreshing(true);
    showTableSkeleton();

    // Check auth / me
    const meResp = await apiFetch('/api/admin/me');
    const meData = await meResp.json().catch(() => ({}));
    if (!meResp.ok) {
        showAdminError(meData.error || `Forbidden (HTTP ${meResp.status})`);
        renderSystemStatus([
            { name: 'API',      ok: false, error: `HTTP ${meResp.status}` },
            { name: 'Auth',     ok: false },
            { name: 'Users DB', ok: false },
            { name: 'Roles',    ok: false },
        ]);
        setRefreshing(false);
        return;
    }

    // Load roles
    const rolesResp = await apiFetch('/api/admin/roles');
    const rolesData = await rolesResp.json().catch(() => ({}));
    if (!rolesResp.ok) {
        showAdminError(rolesData.error || `Failed to load roles (HTTP ${rolesResp.status})`);
        setRefreshing(false);
        return;
    }
    const roleNames = (rolesData.roles || []).map(r => r.name).sort();

    // Load users
    const q = (document.getElementById('adminUserSearch')?.value || '').trim();
    const url = q ? `/api/admin/users?q=${encodeURIComponent(q)}&limit=50` : '/api/admin/users?limit=50';
    const usersResp = await apiFetch(url);
    const usersData = await usersResp.json().catch(() => ({}));
    if (!usersResp.ok) {
        showAdminError(usersData.error || `Failed to load users (HTTP ${usersResp.status})`);
        setRefreshing(false);
        return;
    }
    const users = usersData.users || [];

    renderStats(users, roleNames);
    renderSystemStatus([
        { name: 'API',           ok: true },
        { name: 'Auth Service',  ok: true },
        { name: 'User Database', ok: true },
        { name: 'Role Service',  ok: true },
    ]);
    renderUsersTable(users, roleNames);
    stampLastUpdated();
    setRefreshing(false);
}

// ── Init ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initDeleteModal();

    document.getElementById('adminRefreshBtn')?.addEventListener('click', loadAdmin);

    const search = document.getElementById('adminUserSearch');
    if (search) {
        search.addEventListener('input', () => {
            clearTimeout(window.__adminSearchTimer);
            window.__adminSearchTimer = setTimeout(loadAdmin, 300);
        });
    }

    loadAdmin();
});
