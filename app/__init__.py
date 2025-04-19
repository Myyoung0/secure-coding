import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
from config import Config

# DB 초기화
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '이 페이지에 접근하려면 로그인이 필요합니다.'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.debug = True
    
    # 폴더 생성
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 확장 초기화
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    CORS(app)
    
    # CLI 명령어 등록
    from app import cli
    cli.init_app(app)
    
    # Jinja2 필터 등록
    @app.template_filter('format_number')
    def format_number(value):
        return "{:,}".format(int(value))
    
    @app.template_filter('format_price')
    def format_price(value):
        return "{:,}".format(int(value))
    
    @app.template_filter('date_format')
    def date_format(value):
        return value.strftime('%Y-%m-%d %H:%M')
    
    @app.template_filter('format_datetime')
    def format_datetime(value):
        return value.strftime('%Y-%m-%d %H:%M') if value else ''
    
    @app.template_filter('nl2br')
    def nl2br(value):
        return value.replace('\n', '<br>')
    
    # 블루프린트 등록
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.product import bp as product_bp
    app.register_blueprint(product_bp, url_prefix='/product')
    
    from app.wallet import bp as wallet_bp
    app.register_blueprint(wallet_bp, url_prefix='/wallet')
    
    from app.report import bp as report_bp
    app.register_blueprint(report_bp, url_prefix='/report')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.message import bp as message_bp
    app.register_blueprint(message_bp, url_prefix='/message')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.chat import bp as chat_bp
    app.register_blueprint(chat_bp, url_prefix='/chat')
    
    # 필터 등록
    app.jinja_env.filters['format_number'] = format_number
    app.jinja_env.filters['format_datetime'] = format_datetime
    
    # 에러 핸들링
    if not app.debug and not app.testing:
        # 로그 디렉토리 생성
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # 로그 파일 설정
        file_handler = RotatingFileHandler('logs/marketplace.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('중고거래 플랫폼 시작')
    
    return app

from app import models 