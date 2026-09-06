import os
import logging
from flask import Flask
from app.config import config
from app.routes import routes


def create_app() -> Flask:
    """Application factory."""
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if config.DEBUG else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get the absolute path to the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static')
    )
    
    # Configuration
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    
    # Register routes
    app.register_blueprint(routes)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)