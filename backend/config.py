import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with default values"""
    
    # Application Settings
    APP_NAME: str = "Intelligent Recruitment System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_HOURS: int = 24
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///recruitment.db")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    
    # File Storage
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(__file__), "uploads")
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx"}
    
    # AI/ML Model Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Sentence Transformer model
    EMBEDDING_DEVICE: str = "cuda" if os.getenv("USE_GPU", "False").lower() == "true" else "cpu"
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL: str = "llama3-70b-8192"  # Groq model name
    
    # Matching Thresholds
    MATCH_THRESHOLD: float = 0.8  # 80% match required for shortlisting
    SKILL_WEIGHT: float = 0.45
    EXPERIENCE_WEIGHT: float = 0.30
    EDUCATION_WEIGHT: float = 0.15
    CERTIFICATION_WEIGHT: float = 0.10
    
    # Email Configuration
    SMTP_CONFIG: Dict[str, Any] = {
        "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", 587)),
        "username": os.getenv("SMTP_USERNAME", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "use_tls": True
    }
    
    # Company Information
    COMPANY_INFO: Dict[str, Any] = {
        "name": os.getenv("COMPANY_NAME", "TechRecruit Inc."),
        "logo_url": os.getenv("COMPANY_LOGO_URL", ""),
        "website": os.getenv("COMPANY_WEBSITE", "https://techrecruit.example.com"),
        "contact_email": os.getenv("CONTACT_EMAIL", "hr@techrecruit.example.com")
    }
    
    # UI Settings
    DEFAULT_RESULTS_PER_PAGE: int = 10
    TEMPLATE_DIR: str = os.path.join(os.path.dirname(__file__), "templates")
    
    # Admin Credentials (Override via environment in production)
    ADMIN_CREDENTIALS: Dict[str, str] = {
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "password": os.getenv("ADMIN_PASSWORD", "securepassword123"),
        "email": os.getenv("ADMIN_EMAIL", "admin@techrecruit.example.com")
    }
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with config"""
        # Create upload folder if not exists
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        
        # Set Flask configs
        app.config.from_object(cls)
        
        # Additional production-specific configs
        if not cls.DEBUG:
            app.config["PROPAGATE_EXCEPTIONS"] = True
            app.config["SESSION_COOKIE_SECURE"] = True
            app.config["REMEMBER_COOKIE_SECURE"] = True


class DevelopmentConfig(Config):
    """Development specific configuration"""
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True


class ProductionConfig(Config):
    """Production specific configuration"""
    DEBUG = False
    PROPAGATE_EXCEPTIONS = True


# Configuration selector
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}


def get_config(config_name: str = None) -> Config:
    """
    Get configuration class based on environment
    Args:
        config_name: Name of configuration (development/production)
    Returns:
        Appropriate Config class
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    return config.get(config_name, config["default"])