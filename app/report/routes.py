from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.report import bp
from app.report.forms import ReportForm
from app.models import User, Product, Report
from app.auth.utils import token_required
from sqlalchemy import func

@bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def report_user(user_id):
    """사용자 신고 페이지"""
    user = User.query.get_or_404(user_id)
    
    # 자기 자신 신고 불가
    if user.id == current_user.id:
        flash('자기 자신을 신고할 수 없습니다.')
        return redirect(url_for('main.index'))
    
    form = ReportForm()
    
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            reported_id=user.id,
            reason=f"{form.reason_type.data}: {form.reason.data}"
        )
        db.session.add(report)
        db.session.commit()
        
        # 누적 신고 수 확인
        report_count = Report.query.filter_by(reported_id=user.id, status='pending').count()
        
        # 누적 신고가 일정 수준 이상이면 자동 숨김 처리
        if report_count >= 5:
            # 해당 사용자의 모든 상품 숨김 처리
            Product.query.filter_by(seller_id=user.id).update({Product.status: 'hidden'})
            db.session.commit()
        
        flash('신고가 접수되었습니다. 검토 후 조치하겠습니다.')
        return redirect(url_for('main.index'))
    
    return render_template('report/report_user.html', title='사용자 신고', form=form, user=user)

@bp.route('/product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def report_product(product_id):
    """상품 신고 페이지"""
    product = Product.query.get_or_404(product_id)
    
    # 자신의 상품 신고 불가
    if product.seller_id == current_user.id:
        flash('자신의 상품을 신고할 수 없습니다.')
        return redirect(url_for('product.view_product', product_id=product_id))
    
    form = ReportForm()
    
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            reported_id=product.seller_id,
            product_id=product.id,
            reason=f"{form.reason_type.data}: {form.reason.data}"
        )
        db.session.add(report)
        db.session.commit()
        
        # 누적 신고 수 확인
        report_count = Report.query.filter_by(product_id=product.id, status='pending').count()
        
        # 누적 신고가 일정 수준 이상이면 자동 숨김 처리
        if report_count >= 3:
            product.status = 'hidden'
            db.session.commit()
        
        flash('신고가 접수되었습니다. 검토 후 조치하겠습니다.')
        return redirect(url_for('product.view_product', product_id=product_id))
    
    return render_template('report/report_product.html', title='상품 신고', form=form, product=product)

# API 엔드포인트
@bp.route('/api/report/user/<int:user_id>', methods=['POST'])
@token_required
def api_report_user(current_user, user_id):
    """사용자 신고 API"""
    user = User.query.get_or_404(user_id)
    
    # 자기 자신 신고 불가
    if user.id == current_user.id:
        return jsonify({'error': '자기 자신을 신고할 수 없습니다.'}), 400
    
    data = request.get_json() or {}
    
    if 'reason' not in data:
        return jsonify({'error': '신고 사유를 입력해주세요.'}), 400
    
    report = Report(
        reporter_id=current_user.id,
        reported_id=user.id,
        reason=data['reason']
    )
    db.session.add(report)
    db.session.commit()
    
    # 누적 신고 수 확인
    report_count = Report.query.filter_by(reported_id=user.id, status='pending').count()
    
    # 누적 신고가 일정 수준 이상이면 자동 숨김 처리
    if report_count >= 5:
        # 해당 사용자의 모든 상품 숨김 처리
        Product.query.filter_by(seller_id=user.id).update({Product.status: 'hidden'})
        db.session.commit()
    
    return jsonify({'message': '신고가 접수되었습니다.'}), 201

@bp.route('/api/report/product/<int:product_id>', methods=['POST'])
@token_required
def api_report_product(current_user, product_id):
    """상품 신고 API"""
    product = Product.query.get_or_404(product_id)
    
    # 자신의 상품 신고 불가
    if product.seller_id == current_user.id:
        return jsonify({'error': '자신의 상품을 신고할 수 없습니다.'}), 400
    
    data = request.get_json() or {}
    
    if 'reason' not in data:
        return jsonify({'error': '신고 사유를 입력해주세요.'}), 400
    
    report = Report(
        reporter_id=current_user.id,
        reported_id=product.seller_id,
        product_id=product.id,
        reason=data['reason']
    )
    db.session.add(report)
    db.session.commit()
    
    # 누적 신고 수 확인
    report_count = Report.query.filter_by(product_id=product.id, status='pending').count()
    
    # 누적 신고가 일정 수준 이상이면 자동 숨김 처리
    if report_count >= 3:
        product.status = 'hidden'
        db.session.commit()
    
    return jsonify({'message': '신고가 접수되었습니다.'}), 201 