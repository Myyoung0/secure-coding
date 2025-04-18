import jwt
import datetime
from flask import current_app
from functools import wraps
from flask import request, jsonify
from app.models import User

def create_jwt_token(user_id):
    """사용자 ID로 JWT 토큰 생성"""
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )
    except Exception as e:
        return str(e)

def token_required(f):
    """API 요청에서 JWT 토큰 검증 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            if ' ' in auth_header:
                token = auth_header.split(' ')[1]
            else:
                token = auth_header
        
        if not token:
            return jsonify({'error': '토큰이 필요합니다.'}), 401
        
        try:
            payload = jwt.decode(
                token,
                current_app.config.get('SECRET_KEY'),
                algorithms=['HS256']
            )
            current_user = User.query.get(payload['sub'])
            
            if not current_user:
                return jsonify({'error': '유효하지 않은 토큰입니다.'}), 401
                
            if not current_user.is_active:
                return jsonify({'error': '계정이 비활성화되었습니다.'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '토큰이 만료되었습니다. 다시 로그인해주세요.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '유효하지 않은 토큰입니다.'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated 