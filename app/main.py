from flask import Flask
from app.config import config
from app.routes import routes


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    
    # Register routes
    app.register_blueprint(routes)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)