import os
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.product import bp
from app.product.forms import ProductForm
from app.models import Product, ProductImage
from app.auth.utils import token_required
import uuid
from flask_wtf.file import FileAllowed

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_product():
    """상품 등록 페이지"""
    form = ProductForm()
    
    if request.method == 'POST':
        # 상품 생성 (일반 폼 데이터 사용)
        product = Product(
            title=request.form.get('title'),
            description=request.form.get('description'),
            price=request.form.get('price'),
            category=request.form.get('category'),
            location=request.form.get('location'),
            seller_id=current_user.id
        )
        db.session.add(product)
        db.session.commit()
        
        # 이미지 저장
        images = request.files.getlist('images')
        for image in images:
            if image:
                filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
                file_path = os.path.join('products', filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
                os.makedirs(upload_path, exist_ok=True)
                image.save(os.path.join(upload_path, filename))
                
                product_image = ProductImage(product_id=product.id, image_path=file_path)
                db.session.add(product_image)
        
        db.session.commit()
        flash('상품이 등록되었습니다!')
        return redirect(url_for('product.view_product', product_id=product.id))
    
    return render_template('product/create.html', title='상품 등록', form=form)

@bp.route('/<int:product_id>', methods=['GET'])
def view_product(product_id):
    """상품 상세 페이지"""
    product = Product.query.get_or_404(product_id)
    
    # 판매 중이 아닌 상품은 판매자나 관리자만 볼 수 있음
    if product.status != 'active' and not (current_user.is_authenticated and (current_user.id == product.seller_id or current_user.is_admin)):
        flash('해당 상품을 찾을 수 없습니다.')
        return redirect(url_for('main.index'))
    
    return render_template('product/view.html', title=product.title, product=product)

@bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """상품 수정 페이지"""
    product = Product.query.get_or_404(product_id)
    
    # 판매자나 관리자만 수정 가능
    if current_user.id != product.seller_id and not current_user.is_admin:
        flash('이 상품을 수정할 권한이 없습니다.')
        return redirect(url_for('main.index'))
    
    form = ProductForm()
    
    if request.method == 'POST':
        # 상품 정보 업데이트
        product.title = request.form.get('title')
        product.description = request.form.get('description')
        product.price = request.form.get('price')
        product.category = request.form.get('category')
        product.location = request.form.get('location')
        
        # 상태 매핑 - template 상태값(available, reserved, sold)을 모델 상태값(active, reserved, sold, hidden)으로 변환
        status_map = {
            'available': 'active',  # 판매중 -> active
            'reserved': 'reserved', # 예약중 -> reserved
            'sold': 'sold'          # 판매완료 -> sold
        }
        template_status = request.form.get('status', 'available')
        product.status = status_map.get(template_status, 'active')  # 기본값은 active
        
        product.updated_at = datetime.utcnow()
        
        # 삭제할 이미지 처리
        delete_images = request.form.getlist('delete_images')
        for image_id in delete_images:
            image = ProductImage.query.get(image_id)
            if image and image.product_id == product.id:
                # 이미지가 최소 1개는 남아있는지 확인
                if product.images.count() <= 1 and len(delete_images) >= product.images.count() and not request.files.getlist('images')[0].filename:
                    flash('상품 이미지는 최소 1장 이상 필요합니다.')
                    return render_template('product/edit.html', title='상품 수정', form=form, product=product)
                
                # 파일 시스템에서 이미지 삭제
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], image.image_path))
                except:
                    pass  # 파일이 없어도 계속 진행
                
                # DB에서 이미지 삭제
                db.session.delete(image)
        
        # 새 이미지 추가
        images = request.files.getlist('images')
        for image in images:
            if image and image.filename:
                filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
                file_path = os.path.join('products', filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
                os.makedirs(upload_path, exist_ok=True)
                image.save(os.path.join(upload_path, filename))
                
                product_image = ProductImage(product_id=product.id, image_path=file_path)
                db.session.add(product_image)
        
        db.session.commit()
        flash('상품 정보가 업데이트되었습니다!')
        return redirect(url_for('product.view_product', product_id=product.id))
    
    elif request.method == 'GET':
        # 폼에 기존 데이터 채우기
        form.title.data = product.title
        form.description.data = product.description
        form.price.data = product.price
        form.category.data = product.category
        form.location.data = product.location
    
    # 폼 검증 실패 시 이미지 필드는 필수가 아니도록 설정
    form.images.validators = [FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '이미지 파일만 업로드 가능합니다.')]
    
    return render_template('product/edit.html', title='상품 수정', form=form, product=product)

@bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """상품 삭제"""
    product = Product.query.get_or_404(product_id)
    
    # 판매자나 관리자만 삭제 가능
    if current_user.id != product.seller_id and not current_user.is_admin:
        flash('이 상품을 삭제할 권한이 없습니다.')
        return redirect(url_for('main.index'))
    
    # 직접 삭제 대신 상태 변경 (soft delete)
    product.status = 'hidden'
    db.session.commit()
    
    flash('상품이 삭제되었습니다.')
    return redirect(url_for('main.index'))

@bp.route('/<int:product_id>/images/<int:image_id>/delete', methods=['POST'])
@login_required
def delete_image(product_id, image_id):
    """상품 이미지 삭제"""
    product = Product.query.get_or_404(product_id)
    image = ProductImage.query.get_or_404(image_id)
    
    # 이미지가 해당 상품의 것이고, 사용자가 판매자 또는 관리자인지 확인
    if image.product_id != product.id:
        return jsonify({'error': '이미지를 찾을 수 없습니다.'}), 404
    
    if current_user.id != product.seller_id and not current_user.is_admin:
        return jsonify({'error': '이 이미지를 삭제할 권한이 없습니다.'}), 403
    
    # 이미지 삭제 전, 전체 이미지 수 확인 (최소 한 개는 있어야 함)
    if product.images.count() <= 1:
        return jsonify({'error': '최소 한 개의 이미지는 남아있어야 합니다.'}), 400
    
    # 파일 시스템에서 이미지 삭제
    try:
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], image.image_path))
    except:
        pass  # 파일이 없어도 계속 진행
    
    # DB에서 이미지 삭제
    db.session.delete(image)
    db.session.commit()
    
    return jsonify({'success': True})

# API 엔드포인트
@bp.route('/api/products', methods=['GET'])
def api_get_products():
    """상품 목록 API"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)  # 최대 50개
    
    products_page = Product.query.filter_by(status='active').order_by(
        Product.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    result = {
        'items': [],
        'total': products_page.total,
        'pages': products_page.pages,
        'current_page': page
    }
    
    for product in products_page.items:
        # 대표 이미지 URL
        image = product.images.first()
        image_url = url_for('static', filename=f'uploads/{image.image_path}', _external=True) if image else None
        
        result['items'].append({
            'id': product.id,
            'title': product.title,
            'price': product.price,
            'location': product.location,
            'category': product.category,
            'seller_id': product.seller_id,
            'image_url': image_url,
            'created_at': product.created_at.isoformat()
        })
    
    return jsonify(result)

@bp.route('/api/products/<int:product_id>', methods=['GET'])
def api_get_product(product_id):
    """상품 상세 API"""
    product = Product.query.get_or_404(product_id)
    
    # 비활성 상품은 판매자나 관리자만 볼 수 있음
    if product.status != 'active':
        if not current_user.is_authenticated or (current_user.id != product.seller_id and not current_user.is_admin):
            return jsonify({'error': '상품을 찾을 수 없습니다.'}), 404
    
    # 이미지 URL 리스트
    images = []
    for image in product.images:
        images.append(url_for('static', filename=f'uploads/{image.image_path}', _external=True))
    
    result = {
        'id': product.id,
        'title': product.title,
        'description': product.description,
        'price': product.price,
        'category': product.category,
        'location': product.location,
        'seller_id': product.seller_id,
        'seller_name': product.seller.username,
        'status': product.status,
        'images': images,
        'created_at': product.created_at.isoformat(),
        'updated_at': product.updated_at.isoformat()
    }
    
    return jsonify(result)

@bp.route('/api/products', methods=['POST'])
@token_required
def api_create_product(current_user):
    """상품 등록 API"""
    data = request.form or {}
    
    # 필수 필드 검증
    required_fields = ['title', 'description', 'price', 'category', 'location']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} 필드가 필요합니다.'}), 400
    
    # 가격은 숫자여야 함
    try:
        price = int(data['price'])
        if price < 0:
            return jsonify({'error': '가격은 0 이상이어야 합니다.'}), 400
    except:
        return jsonify({'error': '가격은 숫자여야 합니다.'}), 400
    
    # 상품 생성
    product = Product(
        title=data['title'],
        description=data['description'],
        price=price,
        category=data['category'],
        location=data['location'],
        seller_id=current_user.id
    )
    db.session.add(product)
    db.session.commit()
    
    # 이미지 처리
    if 'images' not in request.files:
        return jsonify({'error': '최소 한 개의 이미지가 필요합니다.'}), 400
    
    images = request.files.getlist('images')
    image_paths = []
    
    for image in images:
        if image and image.filename:
            filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
            file_path = os.path.join('products', filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
            os.makedirs(upload_path, exist_ok=True)
            image.save(os.path.join(upload_path, filename))
            
            product_image = ProductImage(product_id=product.id, image_path=file_path)
            db.session.add(product_image)
            image_paths.append(file_path)
    
    if not image_paths:
        # 이미지가 없으면 상품도 삭제
        db.session.delete(product)
        db.session.commit()
        return jsonify({'error': '최소 한 개의 이미지가 필요합니다.'}), 400
    
    db.session.commit()
    
    return jsonify({
        'id': product.id,
        'title': product.title,
        'message': '상품이 등록되었습니다.'
    }), 201

@bp.route('/<int:product_id>/purchase', methods=['POST'])
@login_required
def purchase_product(product_id):
    """상품 구매 처리"""
    product = Product.query.get_or_404(product_id)
    
    # 자신의 상품은 구매할 수 없음
    if current_user.id == product.seller_id:
        flash('자신의 상품은 구매할 수 없습니다.')
        return redirect(url_for('product.view_product', product_id=product.id))
    
    # 판매 중인 상품만 구매 가능
    if product.status != 'active':
        flash('판매 중인 상품만 구매할 수 있습니다.')
        return redirect(url_for('product.view_product', product_id=product.id))
    
    # 사용자 지갑 잔액 확인
    if not hasattr(current_user, 'wallet') or current_user.wallet is None:
        flash('지갑이 없습니다. 지갑을 먼저 생성해주세요.')
        return redirect(url_for('wallet.index'))
    
    if current_user.wallet.balance < product.price:
        flash('잔액이 부족합니다. 충전 후 다시 시도해주세요.')
        return redirect(url_for('wallet.charge'))
    
    try:
        # 구매자 지갑에서 금액 차감
        current_user.wallet.balance -= product.price
        
        # 판매자 지갑에 금액 추가
        seller = product.seller
        if hasattr(seller, 'wallet') and seller.wallet is not None:
            seller.wallet.balance += product.price
        
        # 상품 상태 변경
        product.status = 'sold'
        product.buyer_id = current_user.id
        product.sold_at = datetime.utcnow()
        
        db.session.commit()
        flash('상품 구매가 완료되었습니다!')
        
        # 구매 알림 또는 이메일 전송 등 추가 작업 가능
        
        return redirect(url_for('product.view_product', product_id=product.id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'구매 처리 중 오류가 발생했습니다: {str(e)}')
        return redirect(url_for('product.view_product', product_id=product.id)) 