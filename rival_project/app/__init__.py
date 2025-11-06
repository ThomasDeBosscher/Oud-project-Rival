from flask import Flask, session, g
from app.config import Config
from app.extensions import init_extensions, db
from app.models.user import User

def create_app(config_class: type = Config):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    # DB, migrations, etc.
    init_extensions(app)
    # Ensure new tables (like CompanyFinance) exist without requiring an immediate migration run
    with app.app_context():
        db.create_all()

    # Blueprints
    from app.blueprints.main import init_app as init_main
    init_main(app)
    from app.blueprints.auth import init_app as init_auth
    init_auth(app)
    from app.blueprints.api import init_app as init_api
    init_api(app)
    from app.blueprints.admin import init_app as init_admin
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