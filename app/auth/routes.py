from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.auth import bp
from app.models import User, Wallet
from app.auth.forms import LoginForm, RegistrationForm, EditProfileForm
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
import os

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # 사용자 등록 후 지갑 생성
        wallet = Wallet(user_id=user.id)
        db.session.add(wallet)
        db.session.commit()
        
        flash('회원가입이 완료되었습니다!')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='회원가입', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('이메일 또는 비밀번호가 올바르지 않습니다.')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('계정이 비활성화되었습니다. 관리자에게 문의하세요.')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', title='로그인', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('로그아웃되었습니다.')
    return redirect(url_for('main.index'))

@bp.route('/profile', methods=['GET'])
@login_required
def profile():
    return render_template('auth/profile.html', title='내 프로필', user=current_user)

@bp.route('/profile/<int:user_id>', methods=['GET'])
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('auth/profile.html', title=f'{user.username}의 프로필', user=user)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        
        if form.profile_image.data:
            filename = secure_filename(form.profile_image.data.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            form.profile_image.data.save(file_path)
            current_user.profile_image = f'profiles/{filename}'
        
        db.session.commit()
        flash('프로필이 업데이트되었습니다.')
        return redirect(url_for('auth.profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
    
    return render_template('auth/edit_profile.html', title='프로필 편집', form=form)

# API 엔드포인트
@bp.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    
    if 'email' not in data or 'password' not in data or 'username' not in data:
        return jsonify({'error': '필수 필드가 누락되었습니다.'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '해당 이메일은 이미 등록되어 있습니다.'}), 400
    
    user = User(email=data['email'], username=data['username'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    
    # 지갑 생성
    wallet = Wallet(user_id=user.id)
    db.session.add(wallet)
    db.session.commit()
    
    return jsonify({'message': '회원가입이 완료되었습니다.'}), 201

@bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    
    if 'email' not in data or 'password' not in data:
        return jsonify({'error': '이메일과 비밀번호를 입력해주세요.'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user is None or not user.check_password(data['password']):
        return jsonify({'error': '이메일 또는 비밀번호가 올바르지 않습니다.'}), 401
    
    if not user.is_active:
        return jsonify({'error': '계정이 비활성화되었습니다.'}), 401
    
    # JWT 토큰 생성 함수 (별도 구현 필요)
    token = create_jwt_token(user.id)
    
    return jsonify({'token': token, 'user_id': user.id, 'username': user.username}), 200 