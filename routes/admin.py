from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash
from database import get_db, calc_points
from routes.auth import admin_required
import csv
import io

admin_bp = Blueprint('admin', __name__)


@admin_bp.before_request
@admin_required
def check_admin():
    pass


@admin_bp.route('/')
def dashboard():
    with get_db() as conn:
        stats = {
            'users': conn.execute('SELECT COUNT(*) FROM users WHERE is_admin=0').fetchone()[0],
            'matches': conn.execute('SELECT COUNT(*) FROM matches').fetchone()[0],
            'bets': conn.execute('SELECT COUNT(*) FROM bets').fetchone()[0],
            'seasons': conn.execute('SELECT COUNT(*) FROM seasons').fetchone()[0],
        }
        recent_matches = conn.execute('''
            SELECT m.*, s.name as season_name
            FROM matches m JOIN seasons s ON s.id = m.season_id
            ORDER BY m.match_date DESC LIMIT 8
        ''').fetchall()
        active_season = conn.execute('SELECT * FROM seasons WHERE is_active=1').fetchone()
    return render_template('admin/dashboard.html',
        stats=stats, recent_matches=recent_matches, active_season=active_season)


# ── USERS ────────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
def users():
    with get_db() as conn:
        all_users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    return render_template('admin/users.html', users=all_users,
        error=request.args.get('error'), success=request.args.get('success'))


@admin_bp.route('/users/create', methods=['POST'])
def create_user():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    display_name = request.form.get('display_name', '').strip()
    is_admin = 1 if request.form.get('is_admin') else 0
    if not username or not password or not display_name:
        return redirect(url_for('admin.users') + '?error=err_all_fields')
    try:
        with get_db() as conn:
            conn.execute(
                'INSERT INTO users (username, password, display_name, is_admin) VALUES (?,?,?,?)',
                (username, generate_password_hash(password, method='pbkdf2:sha256'), display_name, is_admin)
            )
            conn.commit()
        return redirect(url_for('admin.users') + '?success=msg_user_created')
    except Exception:
        return redirect(url_for('admin.users') + '?error=err_username_exists')


@admin_bp.route('/users/<int:uid>/edit', methods=['POST'])
def edit_user(uid):
    display_name = request.form.get('display_name', '').strip()
    password = request.form.get('password', '')
    is_active = 1 if request.form.get('is_active') else 0
    is_admin = 1 if request.form.get('is_admin') else 0
    with get_db() as conn:
        if password:
            conn.execute(
                'UPDATE users SET display_name=?, password=?, is_active=?, is_admin=? WHERE id=?',
                (display_name, generate_password_hash(password, method='pbkdf2:sha256'), is_active, is_admin, uid)
            )
        else:
            conn.execute(
                'UPDATE users SET display_name=?, is_active=?, is_admin=? WHERE id=?',
                (display_name, is_active, is_admin, uid)
            )
        conn.commit()
    return redirect(url_for('admin.users') + '?success=msg_user_updated')


@admin_bp.route('/users/<int:uid>/delete', methods=['POST'])
def delete_user(uid):
    with get_db() as conn:
        admins = conn.execute('SELECT COUNT(*) FROM users WHERE is_admin=1').fetchone()[0]
        user = conn.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
        if user and user['is_admin'] and admins <= 1:
            return redirect(url_for('admin.users') + '?error=err_cannot_delete_admin')
        conn.execute('DELETE FROM bets WHERE user_id=?', (uid,))
        conn.execute('DELETE FROM users WHERE id=?', (uid,))
        conn.commit()
    return redirect(url_for('admin.users') + '?success=msg_user_deleted')


# ── MATCHES ──────────────────────────────────────────────────────────────────

@admin_bp.route('/matches')
def matches():
    with get_db() as conn:
        all_matches = conn.execute('''
            SELECT m.*, s.name as season_name
            FROM matches m JOIN seasons s ON s.id = m.season_id
            ORDER BY m.match_date DESC
        ''').fetchall()
        seasons = conn.execute('SELECT * FROM seasons ORDER BY created_at DESC').fetchall()
        active_season = conn.execute('SELECT * FROM seasons WHERE is_active=1').fetchone()
    return render_template('admin/matches.html',
        matches=all_matches, seasons=seasons, active_season=active_season,
        error=request.args.get('error'), success=request.args.get('success'))


@admin_bp.route('/matches/create', methods=['POST'])
def create_match():
    f = request.form
    season_id = f.get('season_id')
    home_team = f.get('home_team', '').strip()
    away_team = f.get('away_team', '').strip()
    match_date = f.get('match_date', '').replace('T', ' ')
    round_ = f.get('round', '').strip() or None
    if not all([season_id, home_team, away_team, match_date]):
        return redirect(url_for('admin.matches') + '?error=err_all_fields')
    with get_db() as conn:
        conn.execute(
            'INSERT INTO matches (season_id, home_team, away_team, match_date, round) VALUES (?,?,?,?,?)',
            (season_id, home_team, away_team, match_date, round_)
        )
        conn.commit()
    return redirect(url_for('admin.matches') + '?success=msg_match_added')


@admin_bp.route('/matches/upload', methods=['POST'])
def upload_matches():
    file = request.files.get('csvfile')
    if not file:
        return redirect(url_for('admin.matches') + '?error=err_no_file')
    with get_db() as conn:
        active = conn.execute('SELECT * FROM seasons WHERE is_active=1').fetchone()
        if not active:
            return redirect(url_for('admin.matches') + '?error=err_no_active_season')
        try:
            content = file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(content))
            count = 0
            for row in reader:
                home = row.get('Home Team') or row.get('home_team', '')
                away = row.get('Away Team') or row.get('away_team', '')
                date = (row.get('Date') or row.get('date') or row.get('match_date', '')).replace('T', ' ')
                round_ = row.get('Round') or row.get('round') or None
                if home and away and date:
                    conn.execute(
                        'INSERT INTO matches (season_id, home_team, away_team, match_date, round) VALUES (?,?,?,?,?)',
                        (active['id'], home.strip(), away.strip(), date.strip(), round_)
                    )
                    count += 1
            conn.commit()
        except Exception as e:
            return redirect(url_for('admin.matches') + '?error=err_csv_error')
    return redirect(url_for('admin.matches') + f'?success=msg_imported&count={count}')


@admin_bp.route('/matches/<int:mid>/edit', methods=['POST'])
def edit_match(mid):
    f = request.form
    with get_db() as conn:
        conn.execute(
            'UPDATE matches SET home_team=?, away_team=?, match_date=?, round=?, season_id=? WHERE id=?',
            (f.get('home_team'), f.get('away_team'),
             f.get('match_date', '').replace('T', ' '),
             f.get('round') or None, f.get('season_id'), mid)
        )
        conn.commit()
    return redirect(url_for('admin.matches') + '?success=msg_match_updated')


@admin_bp.route('/matches/<int:mid>/result', methods=['POST'])
def set_result(mid):
    home_score = int(request.form.get('home_score', 0))
    away_score = int(request.form.get('away_score', 0))
    with get_db() as conn:
        conn.execute(
            'UPDATE matches SET home_score=?, away_score=?, status=? WHERE id=?',
            (home_score, away_score, 'finished', mid)
        )
        bets = conn.execute('SELECT * FROM bets WHERE match_id=?', (mid,)).fetchall()
        for bet in bets:
            pts = calc_points(bet['home_score'], bet['away_score'], home_score, away_score)
            conn.execute('UPDATE bets SET points=? WHERE id=?', (pts, bet['id']))
        conn.commit()
    return redirect(url_for('admin.matches') + '?success=msg_result_set')


@admin_bp.route('/matches/<int:mid>/delete', methods=['POST'])
def delete_match(mid):
    with get_db() as conn:
        conn.execute('DELETE FROM bets WHERE match_id=?', (mid,))
        conn.execute('DELETE FROM matches WHERE id=?', (mid,))
        conn.commit()
    return redirect(url_for('admin.matches') + '?success=msg_match_deleted')


# ── SEASONS ──────────────────────────────────────────────────────────────────

@admin_bp.route('/seasons')
def seasons():
    with get_db() as conn:
        all_seasons = conn.execute('''
            SELECT s.*,
                (SELECT COUNT(*) FROM matches WHERE season_id = s.id) as match_count,
                (SELECT COUNT(*) FROM bets b JOIN matches m ON m.id = b.match_id WHERE m.season_id = s.id) as bet_count
            FROM seasons s ORDER BY created_at DESC
        ''').fetchall()
    return render_template('admin/seasons.html', seasons=all_seasons,
        error=request.args.get('error'), success=request.args.get('success'))


@admin_bp.route('/seasons/create', methods=['POST'])
def create_season():
    name = request.form.get('name', '').strip()
    if not name:
        return redirect(url_for('admin.seasons') + '?error=err_season_name_required')
    with get_db() as conn:
        conn.execute('INSERT INTO seasons (name) VALUES (?)', (name,))
        conn.commit()
    return redirect(url_for('admin.seasons') + '?success=msg_season_created')


@admin_bp.route('/seasons/<int:sid>/activate', methods=['POST'])
def activate_season(sid):
    with get_db() as conn:
        conn.execute('UPDATE seasons SET is_active=0')
        conn.execute('UPDATE seasons SET is_active=1 WHERE id=?', (sid,))
        conn.commit()
    return redirect(url_for('admin.seasons') + '?success=msg_season_activated')


@admin_bp.route('/seasons/<int:sid>/delete', methods=['POST'])
def delete_season(sid):
    with get_db() as conn:
        count = conn.execute('SELECT COUNT(*) FROM matches WHERE season_id=?', (sid,)).fetchone()[0]
        if count > 0:
            return redirect(url_for('admin.seasons') + '?error=err_season_has_matches')
        conn.execute('DELETE FROM seasons WHERE id=?', (sid,))
        conn.commit()
    return redirect(url_for('admin.seasons') + '?success=msg_season_deleted')
