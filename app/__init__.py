import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS

# DB 초기화
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # 설정
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    app.config['DEBUG'] = True  # 디버그 모드 활성화
    
    # 폴더 생성
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 확장 초기화
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    CORS(app)
    
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
    
    return app 