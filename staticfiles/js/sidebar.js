document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function(e) {
            sidebar.classList.toggle('show');
            e.stopPropagation();
        });
        
        // Close sidebar when clicking outside of it on mobile
        document.addEventListener('click', function(event) {
            const isClickInside = sidebar.contains(event.target) || menuToggle.contains(event.target);
            if (!isClickInside && sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
            }
        });
    }
});
