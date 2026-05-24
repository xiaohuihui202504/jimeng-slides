"""
Simplified Flask Application Entry Point
"""
import os
import sys
import logging
from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

# Load environment variables BEFORE importing anything else
load_dotenv()

from flask import Flask
from flask_cors import CORS
from models import db
from config import Config
from controllers.material_controller import material_bp, material_global_bp
from controllers.reference_file_controller import reference_file_bp
from controllers import project_bp, page_bp, template_bp, user_template_bp, export_bp, file_bp


# Enable SQLite WAL mode for all connections
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Enable WAL mode and related PRAGMAs for each SQLite connection.
    Registered once at import time to avoid duplicate handlers when
    create_app() is called multiple times.
    """
    # Only apply to SQLite connections
    if not isinstance(dbapi_conn, sqlite3.Connection):
        return

    cursor = dbapi_conn.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")  # 30 seconds timeout
    finally:
        cursor.close()


def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Database configuration (use absolute path)
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(backend_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    
    db_path = os.path.join(instance_dir, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    # File storage configuration
    project_root = os.path.dirname(backend_dir)
    upload_folder = os.path.join(project_root, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    app.config['ALLOWED_REFERENCE_FILE_EXTENSIONS'] = Config.ALLOWED_REFERENCE_FILE_EXTENSIONS
    
    # AI configuration
    app.config['DEEPSEEK_API_KEY'] = os.getenv('DEEPSEEK_API_KEY', '')
    app.config['DEEPSEEK_API_BASE'] = os.getenv('DEEPSEEK_API_BASE', 'https://api-inference.modelscope.cn/v1')
    app.config['DEEPSEEK_MODEL'] = os.getenv('DEEPSEEK_MODEL', 'deepseek-ai/DeepSeek-V3.2')

    app.config['JIMENG_API_KEY'] = os.getenv('JIMENG_API_KEY', '')
    app.config['JIMENG_API_BASE'] = os.getenv('JIMENG_API_BASE', 'https://jimeng1.duckcloud.fun/v1')
    app.config['JIMENG_MODEL'] = os.getenv('JIMENG_MODEL', 'jimeng-4.5')
    app.config['MAX_DESCRIPTION_WORKERS'] = int(os.getenv('MAX_DESCRIPTION_WORKERS', '5'))
    app.config['MAX_IMAGE_WORKERS'] = int(os.getenv('MAX_IMAGE_WORKERS', '8'))
    app.config['DEFAULT_ASPECT_RATIO'] = "16:9"
    app.config['DEFAULT_RESOLUTION'] = "2K"
    app.config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # MinerU configuration
    app.config['MINERU_TOKEN'] = os.getenv('MINERU_TOKEN', '')
    app.config['MINERU_API_BASE'] = os.getenv('MINERU_API_BASE', 'https://mineru.net')
    app.config['IMAGE_CAPTION_MODEL'] = os.getenv('IMAGE_CAPTION_MODEL', 'gemini-2.5-flash')
    
    # CORS configuration
    raw_cors = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
    if raw_cors.strip() == '*':
        cors_origins = '*'
    else:
        cors_origins = [o.strip() for o in raw_cors.split(',') if o.strip()]
    app.config['CORS_ORIGINS'] = cors_origins
    
    # Initialize logging (log to stdout so Docker can capture it)
    log_level = getattr(logging, app.config['LOG_LEVEL'], logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    
    # 设置第三方库的日志级别，避免过多的DEBUG日志
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.INFO)  # Flask开发服务器日志保持INFO

    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=cors_origins)
    
    # Register blueprints
    app.register_blueprint(project_bp)
    app.register_blueprint(page_bp)
    app.register_blueprint(template_bp)
    app.register_blueprint(user_template_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(material_bp)
    app.register_blueprint(material_global_bp)
    app.register_blueprint(reference_file_bp, url_prefix='/api/reference-files')
    
    with app.app_context():
        db.create_all()
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'message': 'Banana Slides API is running'}
    
    # Root endpoint
    @app.route('/')
    def index():
        return {
            'name': 'Banana Slides API',
            'version': '1.0.0',
            'description': 'AI-powered PPT generation service',
            'endpoints': {
                'health': '/health',
                'api_docs': '/api',
                'projects': '/api/projects'
            }
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == '__main__':
    # Run development server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    logging.info(
        "\n"
        "╔══════════════════════════════════════╗\n"
        "║   🍌 Banana Slides API Server 🍌   ║\n"
        "╚══════════════════════════════════════╝\n"
        f"Server starting on: http://localhost:{port}\n"
        f"Environment: {os.getenv('FLASK_ENV', 'development')}\n"
        f"Debug mode: {debug}\n"
        f"API Base URL: http://localhost:{port}/api\n"
        f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}\n"
        f"Uploads: {app.config['UPLOAD_FOLDER']}"
    )
    
    # Enable reloader for hot reload in development
    # Using absolute paths for database, so WSL path issues should not occur
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=True)

