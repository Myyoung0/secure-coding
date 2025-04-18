from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models import Product, SearchLog
from sqlalchemy import desc

@bp.route('/')
def index():
    """메인 페이지"""
    # 최신 상품 목록 (최대 8개)
    latest_products = Product.query.filter_by(status='active').order_by(desc(Product.created_at)).limit(8).all()
    return render_template('index.html', title='홈', products=latest_products)

@bp.route('/search')
def search():
    """상품 검색 페이지"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', 0, type=int)
    max_price = request.args.get('max_price', 0, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # 검색 쿼리 처리
    products_query = Product.query.filter_by(status='active')
    
    if query:
        products_query = products_query.filter(Product.title.contains(query) | Product.description.contains(query))
        
        # 검색 로그 저장
        if current_user.is_authenticated:
            search_log = SearchLog(user_id=current_user.id, query=query)
        else:
            search_log = SearchLog(query=query)
        db.session.add(search_log)
        db.session.commit()
    
    if category:
        products_query = products_query.filter_by(category=category)
    
    if location:
        products_query = products_query.filter_by(location=location)
    
    if min_price:
        products_query = products_query.filter(Product.price >= min_price)
    
    if max_price:
        products_query = products_query.filter(Product.price <= max_price)
    
    # 페이지네이션 적용
    products = products_query.order_by(desc(Product.created_at)).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('search.html', title='검색결과', products=products, query=query)

# API 엔드포인트
@bp.route('/api/search', methods=['GET'])
def api_search():
    """상품 검색 API"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', 0, type=int)
    max_price = request.args.get('max_price', 0, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # 검색 쿼리 처리
    products_query = Product.query.filter_by(status='active')
    
    if query:
        products_query = products_query.filter(Product.title.contains(query) | Product.description.contains(query))
        
        # 검색 로그 저장
        if current_user.is_authenticated:
            search_log = SearchLog(user_id=current_user.id, query=query)
        else:
            search_log = SearchLog(query=query)
        db.session.add(search_log)
        db.session.commit()
    
    if category:
        products_query = products_query.filter_by(category=category)
    
    if location:
        products_query = products_query.filter_by(location=location)
    
    if min_price:
        products_query = products_query.filter(Product.price >= min_price)
    
    if max_price:
        products_query = products_query.filter(Product.price <= max_price)
    
    # 페이지네이션 적용
    products_page = products_query.order_by(desc(Product.created_at)).paginate(page=page, per_page=per_page, error_out=False)
    
    # 응답 생성
    result = {
        'items': [],
        'total': products_page.total,
        'pages': products_page.pages,
        'current_page': page
    }
    
    for product in products_page.items:
        # 대표 이미지 가져오기
        image = product.images.first()
        image_url = url_for('static', filename=f'uploads/{image.image_path}') if image else None
        
        result['items'].append({
            'id': product.id,
            'title': product.title,
            'price': product.price,
            'location': product.location,
            'category': product.category,
            'image_url': image_url,
            'created_at': product.created_at.isoformat()
        })
    
    return jsonify(result) 