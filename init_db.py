from app import create_app, db
from app.models import User, Wallet

app = create_app()

with app.app_context():
    # 데이터베이스 테이블 생성
    db.create_all()
    print("데이터베이스 테이블이 생성되었습니다.")
    
    # 기본 관리자 계정 생성
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(
            email='admin@example.com',
            username='관리자',
            is_admin=True,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        # 관리자 지갑 생성
        wallet = Wallet(user_id=admin.id, balance=100000)
        db.session.add(wallet)
        db.session.commit()
        
        print("관리자 계정이 생성되었습니다. 이메일: admin@example.com, 비밀번호: admin123")
    
    print("데이터베이스 초기화가 완료되었습니다.") 