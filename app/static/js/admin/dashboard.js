async function ensureCsrfToken() {
    if (window.csrfToken) return window.csrfToken;
    const r = await fetch('/auth/csrf-token', { credentials: 'same-origin' });
    const d = await r.json();
    window.csrfToken = d.csrf_token;
    return window.csrfToken;
}

function showAdminError(msg) {
    const el = document.getElementById('adminError');
    if (!el) return;
    el.textContent = msg;
    el.classList.remove('hidden');
}

function clearAdminError() {
    const el = document.getElementById('adminError');
    if (!el) return;
    el.textContent = '';
    el.classList.add('hidden');
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

let deleteTargetUserId = null;

function initDeleteModal() {
    const modal = document.getElementById('deleteUserModal');
    const input = document.getElementById('deleteConfirmationInput');
    const cancelBtn = document.getElementById('cancelDeleteBtn');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const spinner = document.getElementById('deleteSpinner');

    if (!modal || !input || !cancelBtn || !confirmBtn) return;

    function closeModal() {
        modal.classList.add('hidden');
        input.value = '';
        deleteTargetUserId = null;
        confirmBtn.disabled = true;
    }

    input.addEventListener('input', () => {
        confirmBtn.disabled = input.value !== 'DELETE';
    });

    cancelBtn.addEventListener('click', closeModal);

    confirmBtn.addEventListener('click', async () => {
        if (!deleteTargetUserId) return;

        confirmBtn.disabled = true;
        spinner.classList.remove('hidden');
        
        try {
            const resp = await apiFetch(`/api/admin/users/${deleteTargetUserId}`, {
                method: 'DELETE'
            });

            if (resp.ok) {
                closeModal();
                loadAdmin();
            } else {
                const data = await resp.json().catch(() => ({}));
                showAdminError(data.error || data.message || `Failed to delete user (HTTP ${resp.status})`);
                closeModal();
            }
        } catch (e) {
            showAdminError(`Network error: ${e.message}`);
            closeModal();
        } finally {
            spinner.classList.add('hidden');
        }
    });

    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
}

function openDeleteModal(userId, userEmail) {
    const modal = document.getElementById('deleteUserModal');
    const emailSpan = document.getElementById('deleteModalUserEmail');
    const input = document.getElementById('deleteConfirmationInput');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    
    if (!modal || !emailSpan) return;

    deleteTargetUserId = userId;
    emailSpan.textContent = userEmail;
    input.value = '';
    confirmBtn.disabled = true;
    modal.classList.remove('hidden');
    input.focus();
}

function renderUsersTable(users, roleNames) {
    const container = document.getElementById('adminUsersTable');
    if (!container) return;

    const header = `
        <table class="min-w-full text-sm">
            <thead>
                <tr class="text-left text-slate-500 dark:text-slate-400">
                    <th class="py-2 pr-4">Email</th>
                    <th class="py-2 pr-4">Name</th>
                    <th class="py-2 pr-4">Roles</th>
                    <th class="py-2">Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    const rows = users
        .map((u) => {
            const selected = new Set(u.roles || []);
            const options = roleNames
                .map((name) => {
                    const sel = selected.has(name) ? 'selected' : '';
                    return `<option value="${name}" ${sel}>${name}</option>`;
                })
                .join('');

            return `
                <tr class="border-b border-slate-200 dark:border-border-dark">
                    <td class="py-2 pr-4">${u.email || ''}</td>
                    <td class="py-2 pr-4">${u.display_name || ''}</td>
                    <td class="py-2 pr-4">
                        <select multiple data-user-id="${u.id}" class="w-64 px-2 py-1 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded">
                            ${options}
                        </select>
                    </td>
                    <td class="py-2 flex gap-2">
                        <button data-save-user-id="${u.id}" class="px-3 py-2 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors text-sm font-medium">Save</button>
                        <button data-delete-user-id="${u.id}" data-user-email="${u.email}" class="px-3 py-2 rounded-lg bg-red-500/10 text-red-600 hover:bg-red-500/20 transition-colors text-sm font-medium">Delete</button>
                    </td>
                </tr>
            `;
        })
        .join('');

    const footer = `
            </tbody>
        </table>
    `;

    container.innerHTML = header + rows + footer;

    container.querySelectorAll('button[data-save-user-id]').forEach((btn) => {
        btn.addEventListener('click', async () => {
            clearAdminError();
            const userId = btn.getAttribute('data-save-user-id');
            const select = container.querySelector(`select[data-user-id="${userId}"]`);
            const roles = Array.from(select.selectedOptions).map((o) => o.value);

            const resp = await apiFetch(`/api/admin/users/${userId}/roles`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ roles }),
            });

            const data = await resp.json().catch(() => ({}));
            if (!resp.ok) {
                showAdminError(data.error || `Failed to update roles (HTTP ${resp.status})`);
            }
        });
    });

    container.querySelectorAll('button[data-delete-user-id]').forEach((btn) => {
        btn.addEventListener('click', async () => {
            const userId = btn.getAttribute('data-delete-user-id');
            const userEmail = btn.getAttribute('data-user-email');
            openDeleteModal(userId, userEmail);
        });
    });
}

async function loadAdmin() {
    clearAdminError();

    const meResp = await apiFetch('/api/admin/me');
    const meData = await meResp.json().catch(() => ({}));
    if (!meResp.ok) {
        showAdminError(meData.error || `Forbidden (HTTP ${meResp.status})`);
        return;
    }

    const rolesResp = await apiFetch('/api/admin/roles');
    const rolesData = await rolesResp.json().catch(() => ({}));
    if (!rolesResp.ok) {
        showAdminError(rolesData.error || `Failed to load roles (HTTP ${rolesResp.status})`);
        return;
    }

    const roleNames = (rolesData.roles || []).map((r) => r.name).sort();

    const q = (document.getElementById('adminUserSearch')?.value || '').trim();
    const usersUrl = q ? `/api/admin/users?q=${encodeURIComponent(q)}&limit=50` : '/api/admin/users?limit=50';

    const usersResp = await apiFetch(usersUrl);
    const usersData = await usersResp.json().catch(() => ({}));
    if (!usersResp.ok) {
        showAdminError(usersData.error || `Failed to load users (HTTP ${usersResp.status})`);
        return;
    }

    renderUsersTable(usersData.users || [], roleNames);
}

document.addEventListener('DOMContentLoaded', () => {
    initDeleteModal();
    document.getElementById('adminRefreshBtn')?.addEventListener('click', loadAdmin);

    const search = document.getElementById('adminUserSearch');
    if (search) {
        search.addEventListener('input', () => {
            window.clearTimeout(window.__adminSearchTimer);
            window.__adminSearchTimer = window.setTimeout(loadAdmin, 300);
        });
    }

    loadAdmin();
});
