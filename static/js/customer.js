// Toggle dropdown
document.getElementById('profileBtn').addEventListener('click', function () {
    const dropdown = document.getElementById('dropdownContent');
    dropdown.classList.toggle('show');
});

// Close dropdown if clicked outside
window.addEventListener('click', function(e) {
    if (!e.target.matches('#profileBtn')) {
        const dropdown = document.getElementById('dropdownContent');
        if (dropdown.classList.contains('show')) {
            dropdown.classList.remove('show');
        }
    }
}); 