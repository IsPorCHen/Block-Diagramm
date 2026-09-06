"""Block Diagramm - Automatic flowchart generator from source code."""

import os
from flask import Flask
from app.config import config
from app.routes import routes

__version__ = '2.0.0'


def create_app() -> Flask:
    """Application factory."""
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