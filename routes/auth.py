from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db
from extensions import limiter
from functools import wraps

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('admin.dashboard') if session.get('is_admin') else url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if 'user_id' in session:
        return redirect(url_for('auth.index'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        with get_db() as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? AND is_active = 1', (username,)
            ).fetchone()
        if user and check_password_hash(user['password'], password):
            session.clear()  # Prevent session fixation
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['display_name'] = user['display_name']
            session['is_admin'] = bool(user['is_admin'])
            session['language'] = user['language'] if user['language'] else 'en'
            return redirect(url_for('admin.dashboard') if user['is_admin'] else url_for('auth.dashboard'))
        error = 'Invalid username or password'
    return render_template('login.html', error=error)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    with get_db() as conn:
        season = conn.execute('SELECT * FROM seasons WHERE is_active = 1').fetchone()
        if not season:
            return render_template('dashboard.html',
                matches=[], leaderboard=[],
                stats={'rank': '-', 'points': 0, 'bets': 0, 'exact_scores': 0},
                season=None)

        matches = conn.execute('''
            SELECT m.*,
                b.home_score as bet_home, b.away_score as bet_away, b.points as bet_points
            FROM matches m
            LEFT JOIN bets b ON b.match_id = m.id AND b.user_id = ?
            WHERE m.season_id = ?
            ORDER BY m.match_date ASC
        ''', (session['user_id'], season['id'])).fetchall()

        leaderboard = conn.execute('''
            SELECT u.id, u.display_name,
                COALESCE(SUM(b.points), 0) as total_points,
                COUNT(CASE WHEN b.points = 3 THEN 1 END) as exact_scores,
                COUNT(CASE WHEN b.points >= 1 THEN 1 END) as correct_results,
                COUNT(b.id) as total_bets
            FROM users u
            LEFT JOIN bets b ON b.user_id = u.id
            LEFT JOIN matches m ON m.id = b.match_id AND m.season_id = ?
            WHERE u.is_admin = 0 AND u.is_active = 1
            GROUP BY u.id
            ORDER BY total_points DESC, exact_scores DESC
        ''', (season['id'],)).fetchall()

    rank = next((i + 1 for i, e in enumerate(leaderboard) if e['id'] == session['user_id']), '-')
    user_entry = next((e for e in leaderboard if e['id'] == session['user_id']), None)
    stats = {
        'rank': rank,
        'points': user_entry['total_points'] if user_entry else 0,
        'bets': user_entry['total_bets'] if user_entry else 0,
        'exact_scores': user_entry['exact_scores'] if user_entry else 0,
    }
    return render_template('dashboard.html',
        matches=matches, leaderboard=leaderboard,
        stats=stats, season=season)


@auth_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    error = None
    success = None
    if request.method == 'POST':
        current_pw  = request.form.get('current_password', '')
        new_pw      = request.form.get('new_password', '')[:200]
        confirm_pw  = request.form.get('confirm_password', '')[:200]
        if not current_pw or not new_pw or not confirm_pw:
            error = 'err_all_fields'
        elif new_pw != confirm_pw:
            error = 'err_passwords_no_match'
        elif len(new_pw) < 4:
            error = 'err_password_too_short'
        else:
            with get_db() as conn:
                user = conn.execute('SELECT * FROM users WHERE id=?',
                                    (session['user_id'],)).fetchone()
                if not check_password_hash(user['password'], current_pw):
                    error = 'err_wrong_password'
                else:
                    conn.execute('UPDATE users SET password=? WHERE id=?',
                                 (generate_password_hash(new_pw, method='pbkdf2:sha256'),
                                  session['user_id']))
                    conn.commit()
                    success = 'msg_password_changed'
    return render_template('account.html', error=error, success=success)


@auth_bp.route('/rankings')
@login_required
def rankings():
    with get_db() as conn:
        seasons = conn.execute('SELECT * FROM seasons ORDER BY is_active DESC, created_at DESC').fetchall()
        active_season = conn.execute('SELECT * FROM seasons WHERE is_active = 1').fetchone()

        season_id = request.args.get('season_id', active_season['id'] if active_season else None)
        selected_season = conn.execute('SELECT * FROM seasons WHERE id = ?', (season_id,)).fetchone() if season_id else None

        leaderboard = []
        max_points = 1
        if selected_season:
            leaderboard = conn.execute('''
                SELECT u.id, u.display_name,
                    COALESCE(SUM(b.points), 0) as total_points,
                    COUNT(CASE WHEN b.points = 3 THEN 1 END) as exact_scores,
                    COUNT(CASE WHEN b.points = 1 THEN 1 END) as correct_results,
                    COUNT(CASE WHEN b.points = 0 THEN 1 END) as wrong,
                    COUNT(CASE WHEN b.points IS NOT NULL THEN 1 END) as resolved_bets,
                    COUNT(b.id) as total_bets,
                    COUNT(CASE WHEN b.points >= 1 THEN 1 END) as wins
                FROM users u
                LEFT JOIN bets b ON b.user_id = u.id
                LEFT JOIN matches m ON m.id = b.match_id AND m.season_id = ?
                WHERE u.is_admin = 0 AND u.is_active = 1
                GROUP BY u.id
                ORDER BY total_points DESC, exact_scores DESC, wins DESC
            ''', (selected_season['id'],)).fetchall()
            # Convert to dicts and assign tie-aware ranks
            lb = [dict(e) for e in leaderboard]
            for i, entry in enumerate(lb):
                if i == 0:
                    entry['rank'] = 1
                else:
                    prev = lb[i - 1]
                    if (entry['total_points'] == prev['total_points'] and
                            entry['exact_scores'] == prev['exact_scores']):
                        entry['rank'] = prev['rank']  # same rank = tie
                    else:
                        entry['rank'] = i + 1  # skip numbers for tied groups
            leaderboard = lb
            max_points = max((e['total_points'] for e in leaderboard), default=1) or 1

    return render_template('rankings.html',
        leaderboard=leaderboard, seasons=seasons,
        selected_season=selected_season, max_points=max_points)
