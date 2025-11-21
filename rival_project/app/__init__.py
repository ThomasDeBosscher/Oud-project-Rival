from flask import Flask, session, g
import os
from .config import Config
from .extensions import init_extensions, db
from .models.user import User
from .models.analytics import Metric, Report, AuditLog, ChangeEvent
from dotenv import load_dotenv

# Load environment variables (e.g., DATABASE_URL, SECRET_KEY) from a .env file if present
load_dotenv()

def create_app(config_class: type = Config):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    # Normalize engine options based on the actual DB URI (important for tests overriding to sqlite)
    uri = str(app.config.get('SQLALCHEMY_DATABASE_URI', ''))
    if uri.startswith('sqlite:'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
        }
    else:
        app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': 5,
            'max_overflow': 5,
        })

    # DB, migrations, etc.
    init_extensions(app)
    # Ensure new tables exist for local dev when using SQLite.
    # We still avoid auto-creation for Postgres/Supabase unless explicitly allowed.
    with app.app_context():
        uri_now = str(app.config.get('SQLALCHEMY_DATABASE_URI', ''))
        if uri_now.startswith('sqlite:'):
            db.create_all()
        elif os.getenv('ALLOW_CREATE_ALL') == '1':
            db.create_all()

    # Blueprints
    from .blueprints.main import init_app as init_main
    init_main(app)
    from .blueprints.auth import init_app as init_auth
    init_auth(app)
    from .blueprints.api import init_app as init_api
    init_api(app)
    from .blueprints.admin import init_app as init_admin
    init_admin(app)

    @app.before_request
    def load_current_user():
        user_id = session.get('user_id')
        g.current_user = User.query.get(user_id) if user_id else None

    @app.context_processor
    def inject_user():
        return {'current_user': getattr(g, 'current_user', None)}

    def _humanize_number(n):
        try:
            n = float(n)
        except Exception:
            return n
        for unit in ['','K','M','B','T']:
            if abs(n) < 1000.0:
                return f"{n:3.1f}{unit}".strip()
            n /= 1000.0
        return f"{n:.1f}P"

    app.jinja_env.filters['humanize'] = _humanize_number

    return app