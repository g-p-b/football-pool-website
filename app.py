from flask import Flask
from flask.json.provider import DefaultJSONProvider
from database import init_db
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.api import api_bp
import sqlite3
import os
from datetime import datetime


class Row2DictProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, sqlite3.Row):
            return dict(obj)
        return super().default(obj)


app = Flask(__name__)
app.json_provider_class = Row2DictProvider
app.json = Row2DictProvider(app)
app.secret_key = os.environ.get('SECRET_KEY', 'fp-secret-change-in-production-2024')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(api_bp, url_prefix='/api')


@app.template_filter('fmt_date')
def fmt_date(value):
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.strftime('%d %b %Y, %H:%M')
    except Exception:
        return str(value)


@app.template_filter('dt_local')
def dt_local(value):
    """Format for datetime-local input."""
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.strftime('%Y-%m-%dT%H:%M')
    except Exception:
        return str(value)


@app.template_filter('is_locked')
def is_locked(match_date):
    """True if match has started (betting closed)."""
    try:
        return datetime.now() >= datetime.fromisoformat(str(match_date))
    except Exception:
        return True


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 3000))
    print(f'\n⚽  Football Pool  →  http://localhost:{port}')
    print(f'   Admin login: admin / admin123\n')
    app.run(debug=False, port=port, host='0.0.0.0')
