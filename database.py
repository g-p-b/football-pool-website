import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'football_pool.db'))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = WAL')
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                display_name TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                is_active INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER REFERENCES seasons(id),
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                match_date DATETIME NOT NULL,
                home_score INTEGER,
                away_score INTEGER,
                status TEXT DEFAULT 'upcoming',
                round TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                match_id INTEGER NOT NULL REFERENCES matches(id),
                home_score INTEGER NOT NULL,
                away_score INTEGER NOT NULL,
                points INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, match_id)
            );
        ''')
        count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        if count == 0:
            pw = generate_password_hash('admin123', method='pbkdf2:sha256')
            conn.execute(
                'INSERT INTO users (username, password, display_name, is_admin) VALUES (?,?,?,1)',
                ('admin', pw, 'Administrator')
            )
            conn.execute(
                'INSERT INTO seasons (name, is_active) VALUES (?,1)',
                ('Season 2024/25',)
            )
            conn.commit()
            print('  ✓ Default admin created: admin / admin123')


def calc_points(bet_h, bet_a, actual_h, actual_a):
    if bet_h == actual_h and bet_a == actual_a:
        return 3
    br = 'H' if bet_h > bet_a else ('A' if bet_h < bet_a else 'D')
    ar = 'H' if actual_h > actual_a else ('A' if actual_h < actual_a else 'D')
    return 1 if br == ar else 0
