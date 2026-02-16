/**
 * Admin Page Initialization
 * Integrates the AdminActionsManager with the existing admin interface.
 */
document.addEventListener('DOMContentLoaded', () => {
    const toolbar = document.getElementById('admin-toolbar');
    
    // If no toolbar container exists, we can't render the menu
    if (!toolbar) {
        console.warn('Admin toolbar container (#admin-toolbar) not found.');
        return;
    }

    // 1. Identify existing actions (Update selectors if your IDs differ)
    // We look for common patterns: ID 'btn-save', type='submit', or class 'btn-delete'
    const saveBtn = document.querySelector('#btn-save, button[type="submit"], .btn-save');
    const deleteBtn = document.querySelector('#btn-delete, .btn-delete, .btn-danger');
    
    // 2. Get User ID for password reset (look for hidden input or data attribute)
    const userIdField = document.getElementById('user-id') || document.querySelector('[data-user-id]');
    const userId = userIdField ? (userIdField.value || userIdField.dataset.userId) : null;

    // 3. Initialize the Manager
    const adminActions = new AdminActionsManager();
    
    // 4. Render the Kebab Menu
    adminActions.renderKebabButton(toolbar, {
        userId: userId,
        onSave: () => {
            if (saveBtn) {
                saveBtn.click(); // Proxy the click to the original button
            } else {
                // Fallback: try to submit the first form found
                const form = document.querySelector('form');
                if (form) form.submit();
            }
        },
        onDelete: () => {
            if (deleteBtn) {
                deleteBtn.click(); // Proxy the click (preserves existing modals/confirms)
            }
        }
    });

    // 5. Hide original buttons visually (but keep in DOM so handlers still work)
    if (saveBtn) saveBtn.classList.add('hidden', '!hidden', 'invisible');
    if (deleteBtn) deleteBtn.classList.add('hidden', '!hidden', 'invisible');
});