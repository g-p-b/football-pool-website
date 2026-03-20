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

function tr(key) {
    return (window.TRANS && window.TRANS[key]) || key;
}

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
        setStatus(statusEl, 'error', `<i class="fa fa-circle-exclamation"></i> ${tr('js_enter_scores')}`);
        return;
    }

    const home = parseInt(homeVal);
    const away = parseInt(awayVal);

    if (isNaN(home) || isNaN(away) || home < 0 || away < 0) {
        setStatus(statusEl, 'error', `<i class="fa fa-circle-exclamation"></i> ${tr('js_invalid_scores')}`);
        return;
    }

    // UI: saving state
    btn.disabled = true;
    btn.innerHTML = `<i class="fa fa-spinner fa-spin"></i> <span>${tr('js_saving')}</span>`;
    setStatus(statusEl, 'saving', `<i class="fa fa-spinner fa-spin"></i> ${tr('js_saving')}`);

    try {
        const res = await fetch('/api/bet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ match_id: matchId, home_score: home, away_score: away })
        });
        const data = await res.json();

        if (data.ok) {
            btn.innerHTML = `<i class="fa fa-floppy-disk"></i> <span>${tr('bet_update')}</span>`;
            setStatus(statusEl, 'saved', `<i class="fa fa-check"></i> ${tr('bet_saved_indicator')}`);
            showToast(tr('js_bet_saved'), 'success');
        } else {
            btn.innerHTML = `<i class="fa fa-floppy-disk"></i> <span>${tr('bet_save')}</span>`;
            setStatus(statusEl, 'error', `<i class="fa fa-circle-exclamation"></i> ${data.error || tr('js_bet_error')}`);
            showToast(data.error || tr('js_bet_error'), 'error');
        }
    } catch (err) {
        btn.innerHTML = `<i class="fa fa-floppy-disk"></i> <span>${tr('bet_save')}</span>`;
        setStatus(statusEl, 'error', `<i class="fa fa-wifi"></i> ${tr('js_network_error')}`);
        showToast(tr('js_network_error'), 'error');
    } finally {
        btn.disabled = false;
    }
}

function setStatus(el, type, html) {
    if (!el) return;
    el.innerHTML = `<span class="${type}-indicator">${html}</span>`;
}
