// ── Bet Submission ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.btn-save').forEach(btn => {
        btn.addEventListener('click', () => saveBet(btn.dataset.matchId));
    });

    // Allow pressing Enter in score inputs to save
    document.querySelectorAll('.score-input').forEach(input => {
        input.addEventListener('keydown', e => {
            if (e.key === 'Enter') saveBet(input.dataset.matchId);
        });
    });
});

async function saveBet(matchId) {
    const card = document.querySelector(`.match-card[data-match-id="${matchId}"]`);
    if (!card) return;

    const homeInput = card.querySelector('.home-input');
    const awayInput = card.querySelector('.away-input');
    const btn = card.querySelector('.btn-save');
    const statusEl = document.getElementById(`status-${matchId}`);

    if (!homeInput || !awayInput) return;

    const homeVal = homeInput.value.trim();
    const awayVal = awayInput.value.trim();

    if (homeVal === '' || awayVal === '') {
        setStatus(statusEl, 'error', '<i class="fa fa-circle-exclamation"></i> Enter both scores');
        return;
    }

    const home = parseInt(homeVal);
    const away = parseInt(awayVal);

    if (isNaN(home) || isNaN(away) || home < 0 || away < 0) {
        setStatus(statusEl, 'error', '<i class="fa fa-circle-exclamation"></i> Invalid scores');
        return;
    }

    // UI: saving state
    btn.disabled = true;
    btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> <span>Saving…</span>';
    setStatus(statusEl, 'saving', '<i class="fa fa-spinner fa-spin"></i> Saving…');

    try {
        const res = await fetch('/api/bet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ match_id: matchId, home_score: home, away_score: away })
        });
        const data = await res.json();

        if (data.ok) {
            btn.innerHTML = '<i class="fa fa-floppy-disk"></i> <span>Update</span>';
            setStatus(statusEl, 'saved', '<i class="fa fa-check"></i> Bet saved');
            showToast('Bet saved! ⚽', 'success');
        } else {
            btn.innerHTML = '<i class="fa fa-floppy-disk"></i> <span>Save Bet</span>';
            setStatus(statusEl, 'error', `<i class="fa fa-circle-exclamation"></i> ${data.error || 'Error saving'}`);
            showToast(data.error || 'Could not save bet', 'error');
        }
    } catch (err) {
        btn.innerHTML = '<i class="fa fa-floppy-disk"></i> <span>Save Bet</span>';
        setStatus(statusEl, 'error', '<i class="fa fa-wifi"></i> Network error');
        showToast('Network error, please try again', 'error');
    } finally {
        btn.disabled = false;
    }
}

function setStatus(el, type, html) {
    if (!el) return;
    el.innerHTML = `<span class="${type}-indicator">${html}</span>`;
}
