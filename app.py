from flask import Flask, session, request, redirect
from flask.json.provider import DefaultJSONProvider
from database import init_db, get_db
from extensions import limiter
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.api import api_bp
import sqlite3
import os
import json
from datetime import datetime

# ── Load translations ────────────────────────────────────────────────────────
TRANSLATIONS = {}
for _lang in ('en', 'hu', 'es', 'de'):
    _path = os.path.join(os.path.dirname(__file__), 'translations', f'{_lang}.json')
    with open(_path, encoding='utf-8') as _f:
        TRANSLATIONS[_lang] = json.load(_f)


class Row2DictProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, sqlite3.Row):
            return dict(obj)
        return super().default(obj)


_DEFAULT_SECRET = 'fp-secret-change-in-production-2024'

app = Flask(__name__)
app.json_provider_class = Row2DictProvider
app.json = Row2DictProvider(app)
app.secret_key = os.environ.get('SECRET_KEY', _DEFAULT_SECRET)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('RAILWAY_ENVIRONMENT') is not None
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB upload limit

limiter.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(api_bp, url_prefix='/api')


# ── Security headers ──────────────────────────────────────────────────────────
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    return response


# ── Translation helper ───────────────────────────────────────────────────────
@app.context_processor
def inject_t():
    def t(key):
        lang = session.get('language', 'en')
        return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(
            key, TRANSLATIONS['en'].get(key, key)
        )
    # JS-relevant keys for inline script injection
    lang = session.get('language', 'en')
    trans_js = {k: v for k, v in TRANSLATIONS.get(lang, TRANSLATIONS['en']).items()
                if k.startswith('js_')}
    # Only return translation key if it actually exists — don't reflect arbitrary URL params
    def t_safe(key):
        result = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key)
        if result is None:
            result = TRANSLATIONS['en'].get(key, '')
        return result

    return dict(t=t_safe, trans_js=trans_js, current_lang=session.get('language', 'en'))


# ── Language switch ──────────────────────────────────────────────────────────
@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in ('en', 'hu', 'es', 'de'):
        session['language'] = lang
        if 'user_id' in session:
            with get_db() as conn:
                conn.execute('UPDATE users SET language=? WHERE id=?',
                             (lang, session['user_id']))
                conn.commit()
    return redirect(request.referrer or '/')


# ── Template filters ─────────────────────────────────────────────────────────
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
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.strftime('%Y-%m-%dT%H:%M')
    except Exception:
        return str(value)


@app.template_filter('is_locked')
def is_locked(match_date):
    try:
        return datetime.now() >= datetime.fromisoformat(str(match_date))
    except Exception:
        return True


if __name__ == '__main__':
    init_db()
    if app.secret_key == _DEFAULT_SECRET:
        print('\n  ⚠️  WARNING: Using default SECRET_KEY. Set SECRET_KEY environment variable in production!')
    port = int(os.environ.get('PORT', 3000))
    print(f'\n⚽  Football Pool  →  http://localhost:{port}')
    print(f'   Admin login: admin / admin123\n')
    app.run(debug=False, port=port, host='0.0.0.0')
