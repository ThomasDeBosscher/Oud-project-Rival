from flask import render_template, Blueprint

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

def init_app(app):
    app.register_blueprint(bp)
