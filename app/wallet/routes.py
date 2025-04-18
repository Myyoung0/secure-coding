from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.wallet import bp
from app.wallet.forms import TransferForm, ChargeForm
from app.models import User, Wallet, Transfer, Product, Transaction
from app.auth.utils import token_required
from sqlalchemy import desc, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime

@bp.route('/', methods=['GET'])
@login_required
def index():
    """지갑 메인 페이지"""
    # 지갑이 없는 경우 생성
    if not current_user.wallet:
        wallet = Wallet(user_id=current_user.id)
        db.session.add(wallet)
        db.session.commit()
    
    # 최근 송금 내역 가져오기
    transfers = (Transfer.query
                .filter((Transfer.sender_id == current_user.wallet.id) | 
                        (Transfer.receiver_id == current_user.wallet.id))
                .order_by(desc(Transfer.created_at))
                .limit(10)
                .all())
    
    return render_template('wallet/index.html', title='내 지갑', transfers=transfers)

@bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    """송금 페이지"""
    form = TransferForm()
    
    if form.validate_on_submit():
        # 수신자 찾기
        receiver = User.query.filter_by(email=form.receiver_email.data).first()
        if not receiver:
            flash('해당 이메일을 가진 사용자를 찾을 수 없습니다.')
            return redirect(url_for('wallet.transfer'))
        
        # 자기 자신에게 송금 불가
        if receiver.id == current_user.id:
            flash('자신에게 송금할 수 없습니다.')
            return redirect(url_for('wallet.transfer'))
        
        # 금액 확인
        amount = form.amount.data
        if amount <= 0:
            flash('송금액은 0보다 커야 합니다.')
            return redirect(url_for('wallet.transfer'))
        
        if current_user.wallet.balance < amount:
            flash('잔액이 부족합니다.')
            return redirect(url_for('wallet.transfer'))
        
        # 트랜잭션 처리
        try:
            # 송금자 지갑 잔액 감소
            current_user.wallet.balance -= amount
            
            # 수신자 지갑 잔액 증가
            receiver.wallet.balance += amount
            
            # 송금 내역 생성
            transfer = Transfer(
                sender_id=current_user.wallet.id,
                receiver_id=receiver.wallet.id,
                amount=amount
            )
            
            db.session.add(transfer)
            db.session.commit()
            
            flash('송금이 완료되었습니다.')
            return redirect(url_for('wallet.index'))
            
        except IntegrityError:
            db.session.rollback()
            flash('송금 처리 중 오류가 발생했습니다. 다시 시도해주세요.')
            return redirect(url_for('wallet.transfer'))
    
    return render_template('wallet/transfer.html', title='송금하기', form=form)

@bp.route('/purchase/<int:product_id>', methods=['POST'])
@login_required
def purchase_product(product_id):
    """상품 구매"""
    product = Product.query.get_or_404(product_id)
    
    # 자신의 상품 구매 불가
    if product.seller_id == current_user.id:
        flash('자신의 상품은 구매할 수 없습니다.')
        return redirect(url_for('product.view_product', product_id=product_id))
    
    # 이미 판매된 상품 구매 불가
    if product.status != 'active':
        flash('이미 판매된 상품이거나 판매 중지된 상품입니다.')
        return redirect(url_for('product.view_product', product_id=product_id))
    
    # 잔액 확인
    if current_user.wallet.balance < product.price:
        flash('잔액이 부족합니다.')
        return redirect(url_for('product.view_product', product_id=product_id))
    
    # 트랜잭션 처리
    try:
        # 구매자 지갑 잔액 감소
        current_user.wallet.balance -= product.price
        
        # 판매자 지갑 잔액 증가
        seller_wallet = Wallet.query.filter_by(user_id=product.seller_id).first()
        seller_wallet.balance += product.price
        
        # 송금 내역 생성
        transfer = Transfer(
            sender_id=current_user.wallet.id,
            receiver_id=seller_wallet.id,
            amount=product.price,
            product_id=product.id
        )
        
        # 상품 상태 변경
        product.status = 'sold'
        
        db.session.add(transfer)
        db.session.commit()
        
        flash('상품 구매가 완료되었습니다.')
        return redirect(url_for('product.view_product', product_id=product_id))
        
    except IntegrityError:
        db.session.rollback()
        flash('구매 처리 중 오류가 발생했습니다. 다시 시도해주세요.')
        return redirect(url_for('product.view_product', product_id=product_id))

@bp.route('/charge', methods=['GET', 'POST'])
@login_required
def charge():
    """
    지갑 충전 페이지
    - 유효한 금액만 충전할 수 있도록 검증
    - 충전 후 송금 내역 생성
    """
    form = ChargeForm()
    
    if form.validate_on_submit():
        amount = form.amount.data
        payment_method = form.payment_method.data
        
        # 충전 금액 유효성 검사
        if amount < 1000:
            flash('최소 충전 금액은 1,000원입니다.', 'danger')
            return redirect(url_for('wallet.charge'))
        
        if amount > 1000000:
            flash('최대 충전 금액은 1,000,000원입니다.', 'danger')
            return redirect(url_for('wallet.charge'))
        
        # 확인 페이지로 이동
        return render_template('wallet/charge_confirm.html', 
                               amount=amount, 
                               payment_method=payment_method, 
                               form=form)
    
    return render_template('wallet/charge.html', form=form, title='지갑 충전')

@bp.route('/charge/confirm', methods=['POST'])
@login_required
def charge_confirm():
    """충전 확인 후 진행"""
    form = ChargeForm()
    
    if form.validate_on_submit():
        try:
            amount = form.amount.data
            payment_method = form.payment_method.data
            
            # 충전 금액 유효성 검사
            if amount < 1000:
                flash('최소 충전 금액은 1,000원입니다.', 'danger')
                return redirect(url_for('wallet.charge'))
            
            if amount > 1000000:
                flash('최대 충전 금액은 1,000,000원입니다.', 'danger')
                return redirect(url_for('wallet.charge'))
            
            # 결제 프로세스 단계로 이동
            return render_template('wallet/payment_process.html', 
                                   amount=amount,
                                   payment_method=payment_method,
                                   form=form)
        except Exception as e:
            flash(f'충전 중 오류가 발생했습니다: {str(e)}', 'danger')
            current_app.logger.error(f'충전 오류: {str(e)}')
            return redirect(url_for('wallet.charge'))
    
    flash('충전 양식이 유효하지 않습니다.', 'danger')
    return redirect(url_for('wallet.charge'))

@bp.route('/charge/process', methods=['POST'])
@login_required
def charge_process():
    """결제 처리 및 검증"""
    form = ChargeForm()
    
    if form.validate_on_submit():
        try:
            amount = form.amount.data
            payment_method = form.payment_method.data
            payment_verification_code = request.form.get('verification_code')
            
            # 간단한 결제 검증 (실제로는 PG사의 API를 통해 검증해야 함)
            # 여기서는 4자리 숫자를 입력받고, 1234일 경우에만 검증 성공으로 처리
            if not payment_verification_code or payment_verification_code != "1234":
                flash('결제 검증에 실패했습니다. 올바른 인증 코드를 입력하세요.', 'danger')
                return render_template('wallet/payment_process.html', 
                                      amount=amount,
                                      payment_method=payment_method,
                                      form=form,
                                      error=True)
            
            # 사용자 지갑 업데이트
            if not current_user.wallet:
                wallet = Wallet(user_id=current_user.id, balance=0)
                db.session.add(wallet)
                db.session.commit()
            
            current_user.wallet.balance += amount
            
            # 충전 거래 기록 생성 - Transfer 모델 사용
            transfer = Transfer(
                sender_id=current_user.wallet.id,  # 자기 자신에게서
                receiver_id=current_user.wallet.id,  # 자기 자신에게로
                amount=amount,
                status='completed'
            )
            
            db.session.add(transfer)
            db.session.commit()
            
            flash(f'{amount:,}원이 성공적으로 충전되었습니다.', 'success')
            return redirect(url_for('wallet.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'충전 중 오류가 발생했습니다: {str(e)}', 'danger')
            current_app.logger.error(f'충전 오류: {str(e)}')
            return redirect(url_for('wallet.charge'))
    
    flash('충전 양식이 유효하지 않습니다.', 'danger')
    return redirect(url_for('wallet.charge'))

@bp.route('/history', methods=['GET'])
@login_required
def history():
    """거래 내역 페이지"""
    # 필터링 옵션
    transaction_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    
    # 기본 쿼리: 현재 사용자의 지갑에서 보낸 거래 또는 받은 거래
    query = Transfer.query.filter(
        or_(
            Transfer.sender_id == current_user.wallet.id,
            Transfer.receiver_id == current_user.wallet.id
        )
    )
    
    # 거래 유형별 필터링
    if transaction_type == 'sent':
        query = query.filter(Transfer.sender_id == current_user.wallet.id)
    elif transaction_type == 'received':
        query = query.filter(Transfer.receiver_id == current_user.wallet.id)
    
    # 최신 거래순으로 정렬하여 페이지네이션
    transfers = query.order_by(desc(Transfer.created_at)).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template(
        'wallet/history.html',
        title='거래 내역',
        transfers=transfers,
        current_type=transaction_type
    )

# API 엔드포인트
@bp.route('/api/wallet', methods=['GET'])
@token_required
def api_get_wallet(current_user):
    """지갑 정보 API"""
    if not current_user.wallet:
        wallet = Wallet(user_id=current_user.id)
        db.session.add(wallet)
        db.session.commit()
    
    return jsonify({
        'balance': current_user.wallet.balance,
        'user_id': current_user.id
    })

@bp.route('/api/wallet/transfers', methods=['GET'])
@token_required
def api_get_transfers(current_user):
    """송금 내역 API"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)  # 최대 50개
    
    transfers_query = Transfer.query.filter(
        (Transfer.sender_id == current_user.wallet.id) | 
        (Transfer.receiver_id == current_user.wallet.id)
    ).order_by(desc(Transfer.created_at))
    
    transfers_page = transfers_query.paginate(page=page, per_page=per_page, error_out=False)
    
    result = {
        'items': [],
        'total': transfers_page.total,
        'pages': transfers_page.pages,
        'current_page': page
    }
    
    for transfer in transfers_page.items:
        is_sender = transfer.sender_id == current_user.wallet.id
        
        # 상대방 정보
        other_wallet_id = transfer.receiver_id if is_sender else transfer.sender_id
        other_wallet = Wallet.query.get(other_wallet_id)
        other_user = User.query.get(other_wallet.user_id)
        
        # 관련 상품 정보
        product_info = None
        if transfer.product_id:
            product = Product.query.get(transfer.product_id)
            if product:
                product_info = {
                    'id': product.id,
                    'title': product.title
                }
        
        result['items'].append({
            'id': transfer.id,
            'amount': transfer.amount,
            'is_sender': is_sender,
            'other_user': {
                'id': other_user.id,
                'username': other_user.username
            },
            'product': product_info,
            'status': transfer.status,
            'created_at': transfer.created_at.isoformat()
        })
    
    return jsonify(result)

@bp.route('/api/wallet/transfer', methods=['POST'])
@token_required
def api_transfer(current_user):
    """송금 API"""
    data = request.get_json() or {}
    
    # 필수 필드 검증
    if 'receiver_id' not in data or 'amount' not in data:
        return jsonify({'error': '수신자 ID와 금액이 필요합니다.'}), 400
    
    # 수신자 확인
    receiver = User.query.get(data['receiver_id'])
    if not receiver:
        return jsonify({'error': '수신자를 찾을 수 없습니다.'}), 404
    
    # 자기 자신에게 송금 불가
    if receiver.id == current_user.id:
        return jsonify({'error': '자신에게 송금할 수 없습니다.'}), 400
    
    # 금액 확인
    try:
        amount = int(data['amount'])
        if amount <= 0:
            return jsonify({'error': '송금액은 0보다 커야 합니다.'}), 400
    except:
        return jsonify({'error': '유효한 금액을 입력해주세요.'}), 400
    
    if current_user.wallet.balance < amount:
        return jsonify({'error': '잔액이 부족합니다.'}), 400
    
    # 트랜잭션 처리
    try:
        # 송금자 지갑 잔액 감소
        current_user.wallet.balance -= amount
        
        # 수신자 지갑 잔액 증가
        receiver.wallet.balance += amount
        
        # 송금 내역 생성
        transfer = Transfer(
            sender_id=current_user.wallet.id,
            receiver_id=receiver.wallet.id,
            amount=amount
        )
        
        db.session.add(transfer)
        db.session.commit()
        
        return jsonify({
            'message': '송금이 완료되었습니다.',
            'transfer_id': transfer.id,
            'new_balance': current_user.wallet.balance
        }), 200
        
    except:
        db.session.rollback()
        return jsonify({'error': '송금 처리 중 오류가 발생했습니다.'}), 500

@bp.route('/api/wallet/purchase/<int:product_id>', methods=['POST'])
@token_required
def api_purchase_product(current_user, product_id):
    """상품 구매 API"""
    product = Product.query.get_or_404(product_id)
    
    # 자신의 상품 구매 불가
    if product.seller_id == current_user.id:
        return jsonify({'error': '자신의 상품은 구매할 수 없습니다.'}), 400
    
    # 이미 판매된 상품 구매 불가
    if product.status != 'active':
        return jsonify({'error': '이미 판매된 상품이거나 판매 중지된 상품입니다.'}), 400
    
    # 잔액 확인
    if current_user.wallet.balance < product.price:
        return jsonify({'error': '잔액이 부족합니다.'}), 400
    
    # 트랜잭션 처리
    try:
        # 구매자 지갑 잔액 감소
        current_user.wallet.balance -= product.price
        
        # 판매자 지갑 잔액 증가
        seller_wallet = Wallet.query.filter_by(user_id=product.seller_id).first()
        seller_wallet.balance += product.price
        
        # 송금 내역 생성
        transfer = Transfer(
            sender_id=current_user.wallet.id,
            receiver_id=seller_wallet.id,
            amount=product.price,
            product_id=product.id
        )
        
        # 상품 상태 변경
        product.status = 'sold'
        
        db.session.add(transfer)
        db.session.commit()
        
        return jsonify({
            'message': '상품 구매가 완료되었습니다.',
            'transfer_id': transfer.id,
            'new_balance': current_user.wallet.balance
        }), 200
        
    except:
        db.session.rollback()
        return jsonify({'error': '구매 처리 중 오류가 발생했습니다.'}), 500 