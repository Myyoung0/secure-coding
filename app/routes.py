from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Product, Report
from app.forms import ReportForm

report_bp = Blueprint('report', __name__)

@report_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def report_user(user_id):
    """사용자 신고 페이지"""
    # 자기 자신은 신고할 수 없음
    if user_id == current_user.id:
        flash('자기 자신은 신고할 수 없습니다.')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    form = ReportForm()
    
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            reported_user_id=user_id,
            reason=form.reason.data
        )
        db.session.add(report)
        db.session.commit()
        
        flash('신고가 접수되었습니다. 관리자 검토 후 조치될 예정입니다.')
        return redirect(url_for('auth.profile', user_id=user_id))
    
    return render_template('report/report_user.html', title='사용자 신고', form=form, user=user)

@report_bp.route('/product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def report_product(product_id):
    """상품 신고 페이지"""
    product = Product.query.get_or_404(product_id)
    
    # 자신의 상품은 신고할 수 없음
    if product.seller_id == current_user.id:
        flash('자신의 상품은 신고할 수 없습니다.')
        return redirect(url_for('product.view_product', product_id=product_id))
    
    form = ReportForm()
    
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            product_id=product_id,
            reason=form.reason.data
        )
        db.session.add(report)
        db.session.commit()
        
        flash('신고가 접수되었습니다. 관리자 검토 후 조치될 예정입니다.')
        return redirect(url_for('product.view_product', product_id=product_id))
    
    return render_template('report/report_product.html', title='상품 신고', form=form, product=product)

# 관리자용 신고 관리 라우트
@report_bp.route('/admin', methods=['GET'])
@login_required
def admin_reports():
    """관리자용 신고 목록 페이지"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    # 상태별 필터링
    query = Report.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    reports = query.order_by(Report.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/reports.html', title='신고 관리', reports=reports, current_status=status)

@report_bp.route('/admin/<int:report_id>', methods=['GET', 'POST'])
@login_required
def admin_report_detail(report_id):
    """관리자용 신고 상세 페이지"""
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.')
        return redirect(url_for('main.index'))
    
    report = Report.query.get_or_404(report_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action in ['review', 'dismiss']:
            report.status = 'reviewed' if action == 'review' else 'dismissed'
            db.session.commit()
            
            flash('신고 상태가 업데이트되었습니다.')
            return redirect(url_for('report.admin_report_detail', report_id=report_id))
    
    return render_template('admin/report_detail.html', title=f'신고 #{report.id}', report=report) 