// Optional: Client-side validation (improves UX)
document.getElementById('loginForm').addEventListener('submit', function(e) {
    var userId = document.getElementById('user_id').value.trim();
    var password = document.getElementById('password').value.trim();
    if (!userId || !password) {
        alert("Please fill in both User ID and Password.");
        e.preventDefault();
    }
});
