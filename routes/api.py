from flask import Blueprint, request, jsonify, session
from database import get_db
from routes.auth import login_required
from datetime import datetime

api_bp = Blueprint('api', __name__)


@api_bp.route('/bet', methods=['POST'])
@login_required
def place_bet():
    data = request.get_json() or request.form
    match_id = data.get('match_id')
    try:
        home_score = int(data.get('home_score'))
        away_score = int(data.get('away_score'))
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'Invalid score values'})

    if not (0 <= home_score <= 99 and 0 <= away_score <= 99):
        return jsonify({'ok': False, 'error': 'Score out of range (0–99)'})

    with get_db() as conn:
        match = conn.execute('SELECT * FROM matches WHERE id=?', (match_id,)).fetchone()
        if not match:
            return jsonify({'ok': False, 'error': 'Match not found'})
        if match['status'] == 'finished':
            return jsonify({'ok': False, 'error': 'Match already finished'})

        match_date = datetime.fromisoformat(str(match['match_date']))
        if datetime.now() >= match_date:
            return jsonify({'ok': False, 'error': 'Betting is closed for this match'})

        conn.execute('''
            INSERT INTO bets (user_id, match_id, home_score, away_score, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, match_id) DO UPDATE SET
                home_score = excluded.home_score,
                away_score = excluded.away_score,
                updated_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], match_id, home_score, away_score))
        conn.commit()

    return jsonify({'ok': True})
