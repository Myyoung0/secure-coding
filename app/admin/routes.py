from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import User, Product, Report, Transfer, SearchLog
from app.auth.utils import token_required
from functools import wraps
from sqlalchemy import desc, func
import datetime

def admin_required(f):
    """관리자 권한 확인 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('관리자 권한이 필요합니다.')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    """관리자 대시보드"""
    # 통계 데이터 준비
    stats = {
        'user_count': User.query.count(),
        'product_count': Product.query.count(),
        'active_product_count': Product.query.filter_by(status='active').count(),
        'sold_product_count': Product.query.filter_by(status='sold').count(),
        'report_count': Report.query.count(),
        'pending_report_count': Report.query.filter_by(status='pending').count()
    }
    
    # 오늘 통계
    today = datetime.datetime.utcnow().date()
    stats['today_users'] = User.query.filter(func.date(User.created_at) == today).count()
    stats['today_products'] = Product.query.filter(func.date(Product.created_at) == today).count()
    
    # 총 거래액
    stats['total_sales'] = db.session.query(func.sum(Transfer.amount)).filter(
        Transfer.product_id.isnot(None)
    ).scalar() or 0
    
    # 최근 가입한 사용자
    recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()
    
    # 최근 등록된 상품
    recent_products = Product.query.order_by(desc(Product.created_at)).limit(5).all()
    
    return render_template('admin/index.html', 
                          title='관리자 대시보드',
                          stats=stats, 
                          recent_users=recent_users,
                          recent_products=recent_products)

@bp.route('/users')
@login_required
@admin_required
def users():
    """사용자 관리 페이지"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = request.args.get('q', '')
    
    # 검색 쿼리 처리
    if query:
        users = User.query.filter(
            User.email.contains(query) | 
            User.username.contains(query)
        ).order_by(desc(User.created_at)).paginate(page=page, per_page=per_page, error_out=False)
    else:
        users = User.query.order_by(desc(User.created_at)).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', title='사용자 관리', users=users, query=query)

@bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_detail(user_id):
    """사용자 상세 및 편집 페이지"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'activate':
            user.is_active = True
            flash(f'사용자 {user.username}이(가) 활성화되었습니다.')
        
        elif action == 'deactivate':
            user.is_active = False
            flash(f'사용자 {user.username}이(가) 비활성화되었습니다.')
        
        elif action == 'make_admin':
            user.is_admin = True
            flash(f'사용자 {user.username}에게 관리자 권한이 부여되었습니다.')
        
        elif action == 'remove_admin':
            user.is_admin = False
            flash(f'사용자 {user.username}의 관리자 권한이 제거되었습니다.')
        
        db.session.commit()
        return redirect(url_for('admin.user_detail', user_id=user.id))
    
    # 사용자 관련 정보
    products = Product.query.filter_by(seller_id=user.id).order_by(desc(Product.created_at)).limit(5).all()
    reports_filed = Report.query.filter_by(reporter_id=user.id).order_by(desc(Report.created_at)).limit(5).all()
    reports_received = Report.query.filter_by(reported_id=user.id).order_by(desc(Report.created_at)).limit(5).all()
    
    return render_template('admin/user_detail.html', title=f'사용자 {user.username}',
                          user=user, products=products,
                          reports_filed=reports_filed, reports_received=reports_received)

@bp.route('/products')
@login_required
@admin_required
def products():
    """상품 관리 페이지"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    
    # 검색 쿼리 처리
    products_query = Product.query
    
    if query:
        products_query = products_query.filter(
            Product.title.contains(query) | 
            Product.description.contains(query)
        )
    
    if status:
        products_query = products_query.filter_by(status=status)
    
    products = products_query.order_by(desc(Product.created_at)).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/products.html', title='상품 관리', 
                          products=products, query=query, status=status)

@bp.route('/products/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def product_detail(product_id):
    """상품 상세 및 편집 페이지"""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'activate':
            product.status = 'active'
            flash('상품이 활성화되었습니다.')
        
        elif action == 'hide':
            product.status = 'hidden'
            flash('상품이 숨김 처리되었습니다.')
        
        db.session.commit()
        return redirect(url_for('admin.product_detail', product_id=product.id))
    
    # 관련 신고 내역
    reports = Report.query.filter_by(product_id=product.id).order_by(desc(Report.created_at)).all()
    
    return render_template('admin/product_detail.html', title=f'상품 {product.title}',
                          product=product, reports=reports)

@bp.route('/reports')
@login_required
@admin_required
def reports():
    """신고 관리 페이지"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    status = request.args.get('status', 'pending')
    
    # 신고 상태별 필터링
    reports_query = Report.query
    
    if status:
        reports_query = reports_query.filter_by(status=status)
    
    reports = reports_query.order_by(desc(Report.created_at)).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/reports.html', title='신고 관리', 
                          reports=reports, status=status)

@bp.route('/reports/<int:report_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def report_detail(report_id):
    """신고 상세 및 처리 페이지"""
    report = Report.query.get_or_404(report_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'dismiss':
            report.status = 'dismissed'
            flash('신고가 기각되었습니다.')
        
        elif action == 'review':
            report.status = 'reviewed'
            flash('신고가 검토 완료 처리되었습니다.')
            
            # 상품 관련 신고인 경우 상품 숨김 처리
            if report.product_id:
                product = Product.query.get(report.product_id)
                if product:
                    product.status = 'hidden'
                    flash('관련 상품이 숨김 처리되었습니다.')
        
        db.session.commit()
        return redirect(url_for('admin.report_detail', report_id=report.id))
    
    # 관련 정보
    reporter = User.query.get(report.reporter_id)
    reported = User.query.get(report.reported_id)
    product = Product.query.get(report.product_id) if report.product_id else None
    
    return render_template('admin/report_detail.html', title=f'신고 #{report.id}',
                          report=report, reporter=reporter, 
                          reported=reported, product=product)

@bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """통계 페이지"""
    # 일별 가입자 수 (최근 30일)
    thirty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    
    daily_users = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= thirty_days_ago).group_by(func.date(User.created_at)).all()
    
    # 일별 거래액 (최근 30일)
    daily_sales = db.session.query(
        func.date(Transfer.created_at).label('date'),
        func.sum(Transfer.amount).label('amount')
    ).filter(
        Transfer.created_at >= thirty_days_ago,
        Transfer.product_id.isnot(None)
    ).group_by(func.date(Transfer.created_at)).all()
    
    # 카테고리별 상품 수
    category_products = db.session.query(
        Product.category,
        func.count(Product.id).label('count')
    ).group_by(Product.category).all()
    
    # 인기 검색어 Top 10
    popular_searches = db.session.query(
        SearchLog.query,
        func.count(SearchLog.id).label('count')
    ).group_by(SearchLog.query).order_by(func.count(SearchLog.id).desc()).limit(10).all()
    
    return render_template('admin/statistics.html', title='통계',
                          daily_users=daily_users, daily_sales=daily_sales,
                          category_products=category_products, popular_searches=popular_searches)

# API 엔드포인트
@bp.route('/api/admin/users', methods=['GET'])
@token_required
def api_get_users(current_user):
    """사용자 목록 API"""
    if not current_user.is_admin:
        return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)  # 최대 50개
    
    query = request.args.get('q', '')
    
    # 검색 쿼리 처리
    users_query = User.query
    
    if query:
        users_query = users_query.filter(
            User.email.contains(query) | 
            User.username.contains(query)
        )
    
    users_page = users_query.order_by(desc(User.created_at)).paginate(page=page, per_page=per_page, error_out=False)
    
    result = {
        'items': [],
        'total': users_page.total,
        'pages': users_page.pages,
        'current_page': page
    }
    
    for user in users_page.items:
        result['items'].append({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat()
        })
    
    return jsonify(result)

@bp.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@token_required
def api_update_user(current_user, user_id):
    """사용자 정보 수정 API"""
    if not current_user.is_admin:
        return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])
    
    if 'is_admin' in data:
        user.is_admin = bool(data['is_admin'])
    
    db.session.commit()
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'is_admin': user.is_admin,
        'is_active': user.is_active
    }) 