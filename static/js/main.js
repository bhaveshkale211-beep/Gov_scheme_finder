// Navbar toggle for mobile
document.getElementById('navToggle')?.addEventListener('click', () => {
    document.getElementById('navLinks').classList.toggle('open');
});

// Tab switching on home page
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + btn.dataset.tab)?.classList.add('active');
    });
});

// Password toggle
function togglePwd(id) {
    const input = document.getElementById(id);
    input.type = input.type === 'password' ? 'text' : 'password';
}

// Table search filter
function filterTable(inputId, tableId) {
    const filter = document.getElementById(inputId).value.toLowerCase();
    const rows = document.querySelectorAll(`#${tableId} tbody tr`);
    rows.forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(filter) ? '' : 'none';
    });
}

// Auto-dismiss alerts after 4 seconds
setTimeout(() => {
    document.querySelectorAll('.alert').forEach(a => a.remove());
}, 4000);
