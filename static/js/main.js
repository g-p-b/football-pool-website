// ── Toast Notifications ──────────────────────────────────────────────────
function showToast(msg, type = 'success') {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.className = `toast ${type} show`;
    clearTimeout(t._timer);
    t._timer = setTimeout(() => { t.className = 'toast'; }, 3200);
}

// ── Modal ────────────────────────────────────────────────────────────────
function setModal(title, bodyHtml) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('modal');
    if (!overlay || !modal) return;
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHtml;
    overlay.classList.add('open');
    modal.classList.add('open');
    const first = modal.querySelector('input, select, textarea');
    if (first) setTimeout(() => first.focus(), 60);
}

function closeModal() {
    document.getElementById('modal-overlay')?.classList.remove('open');
    document.getElementById('modal')?.classList.remove('open');
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
});

// ── HTML Escaping helper ─────────────────────────────────────────────────
function escHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
