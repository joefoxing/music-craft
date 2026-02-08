document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    }
});

// Mobile menu
function toggleMobileMenu() {
    const sidebar = document.getElementById('main-sidebar') || document.querySelector('aside');
    if (!sidebar) return;
    
    const isHidden = sidebar.classList.contains('hidden');
    
    if (isHidden) {
        // Open sidebar
        sidebar.classList.remove('hidden');
        // Ensure flex is added for layout
        sidebar.classList.add('flex'); 
        
        // Add mobile styling
        sidebar.classList.add('fixed', 'inset-y-0', 'left-0', 'z-50', 'h-full', 'shadow-2xl');
        
        // Create backdrop
        let backdrop = document.getElementById('sidebar-backdrop');
        if (!backdrop) {
            backdrop = document.createElement('div');
            backdrop.id = 'sidebar-backdrop';
            backdrop.className = 'fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm transition-opacity opacity-0';
            backdrop.onclick = toggleMobileMenu;
            document.body.appendChild(backdrop);
            // Animate in
            requestAnimationFrame(() => backdrop.classList.remove('opacity-0'));
        }
    } else {
        // Close sidebar
        sidebar.classList.add('hidden');
        sidebar.classList.remove('flex');
        
        // Remove mobile styling
        sidebar.classList.remove('fixed', 'inset-y-0', 'left-0', 'z-50', 'h-full', 'shadow-2xl');
        
        // Remove backdrop
        const backdrop = document.getElementById('sidebar-backdrop');
        if (backdrop) {
            backdrop.classList.add('opacity-0');
            setTimeout(() => {
                if (backdrop.parentNode) backdrop.parentNode.removeChild(backdrop);
            }, 300);
        }
    }
}