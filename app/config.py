import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration."""
    
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    MAX_CONTENT_LENGTH: int = 1 * 1024 * 1024  # 1MB
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', 5000))
    
    SUPPORTED_EXTENSIONS: tuple = ('.py', '.js', '.cs')


config = Config()