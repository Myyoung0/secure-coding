from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.message import bp
from app.models import User, Message, Product
from datetime import datetime

@bp.route('/send/<int:recipient_id>', methods=['POST'])
@login_required
def send(recipient_id):
    """메시지 전송 처리"""
    recipient = User.query.get_or_404(recipient_id)
    
    # 자기 자신에게 메시지 보내기 방지
    if recipient.id == current_user.id:
        flash('자기 자신에게 메시지를 보낼 수 없습니다.')
        return redirect(url_for('main.index'))
    
    content = request.form.get('content')
    if not content or content.strip() == '':
        flash('메시지 내용을 입력해주세요.')
        
        # 상품 상세 페이지에서 온 요청이면 해당 페이지로 리디렉션
        product_id = request.form.get('product_id')
        if product_id:
            return redirect(url_for('product.view_product', product_id=product_id))
        return redirect(url_for('main.index'))
    
    # 메시지 생성
    message = Message(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=content
    )
    
    # 상품 관련 메시지인 경우 상품 ID 저장
    product_id = request.form.get('product_id')
    if product_id:
        product = Product.query.get(product_id)
        if product:
            message.product_id = product.id
    
    db.session.add(message)
    db.session.commit()
    
    flash('메시지가 전송되었습니다.')
    
    # 상품 상세 페이지에서 온 요청이면 해당 페이지로 리디렉션
    if product_id:
        return redirect(url_for('product.view_product', product_id=product_id))
    
    # 아니면 메시지함으로 리디렉션
    return redirect(url_for('message.inbox'))

@bp.route('/inbox', methods=['GET'])
@login_required
def inbox():
    """받은 메시지함"""
    messages = Message.query.filter_by(recipient_id=current_user.id).order_by(
        Message.created_at.desc()
    ).all()
    
    return render_template('message/inbox.html', title='받은 메시지함', messages=messages)

@bp.route('/sent', methods=['GET'])
@login_required
def sent():
    """보낸 메시지함"""
    messages = Message.query.filter_by(sender_id=current_user.id).order_by(
        Message.created_at.desc()
    ).all()
    
    return render_template('message/sent.html', title='보낸 메시지함', messages=messages)

@bp.route('/view/<int:message_id>', methods=['GET'])
@login_required
def view(message_id):
    """메시지 상세 보기"""
    message = Message.query.get_or_404(message_id)
    
    # 권한 확인 (발신자나 수신자만 볼 수 있음)
    if message.sender_id != current_user.id and message.recipient_id != current_user.id:
        flash('이 메시지를 볼 권한이 없습니다.')
        return redirect(url_for('main.index'))
    
    # 읽음 표시 업데이트 (수신자가 보는 경우)
    if message.recipient_id == current_user.id and not message.is_read:
        message.is_read = True
        message.read_at = datetime.utcnow()
        db.session.commit()
    
    return render_template('message/view.html', title='메시지 보기', message=message) 