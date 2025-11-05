from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    from app import routes
    routes.init_app(app)

    return app
