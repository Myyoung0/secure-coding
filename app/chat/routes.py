from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import desc, or_, and_
from app import db, GLOBAL_CHAT_ROOM_ID
from app.chat import bp
from app.models import User, ChatRoom, ChatParticipant, ChatMessage, Product
from datetime import datetime

@bp.route('/', methods=['GET'])
@login_required
def index():
    """채팅 메인 페이지 - 참여 중인 채팅방 목록"""
    # global 선언을 먼저 해야 합니다
    global GLOBAL_CHAT_ROOM_ID
    
    # 글로벌 채팅방 ID 확인
    global_chat_id = GLOBAL_CHAT_ROOM_ID
    global_chat_room = None
    
    # 글로벌 채팅방 이름으로 채팅방 찾기 (name="실시간 전체 채팅")
    global_chat_room = ChatRoom.query.filter_by(name="실시간 전체 채팅").first()
    
    if not global_chat_room:
        # 글로벌 채팅방이 이름으로 존재하지 않으면 ID로 찾기
        if global_chat_id:
            global_chat_room = ChatRoom.query.get(global_chat_id)
    
    # 글로벌 채팅방이 없으면 새로 생성
    if not global_chat_room:
        try:
            global_chat_room = ChatRoom(
                name="실시간 전체 채팅",
                type="public"
            )
            db.session.add(global_chat_room)
            db.session.flush()  # ID 생성
            
            # 앱 설정 업데이트
            from app import app
            app.config['GLOBAL_CHAT_ROOM_ID'] = global_chat_room.id
            GLOBAL_CHAT_ROOM_ID = global_chat_room.id
            
            db.session.commit()
            current_app.logger.info(f'새 글로벌 채팅방이 생성되었습니다. ID: {global_chat_room.id}')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'글로벌 채팅방 생성 실패: {str(e)}')
    
    # 글로벌 채팅방에 자동 추가
    if global_chat_room:
        # 이미 참여 중인지 확인
        existing_participant = ChatParticipant.query.filter_by(
            user_id=current_user.id,
            chat_room_id=global_chat_room.id
        ).first()
        
        if not existing_participant:
            # 새 참여자 추가
            try:
                new_participant = ChatParticipant(
                    user_id=current_user.id,
                    chat_room_id=global_chat_room.id
                )
                db.session.add(new_participant)
                db.session.commit()
                current_app.logger.info(f'사용자 {current_user.username}(ID: {current_user.id})가 글로벌 채팅방에 추가됨')
            except Exception as e:
                current_app.logger.error(f'글로벌 채팅방 참여자 추가 실패: {str(e)}')

    # 사용자가 참여 중인 모든 채팅방 가져오기
    participations = ChatParticipant.query.filter_by(user_id=current_user.id).all()
    chat_room_ids = [p.chat_room_id for p in participations]
    
    # 채팅방 정보 가져오기
    chat_rooms = ChatRoom.query.filter(ChatRoom.id.in_(chat_room_ids)).all()
    
    # 1대1 채팅방과 전체 채팅방 분리
    private_rooms = []
    public_rooms = []
    
    for room in chat_rooms:
        if room.type == 'private':
            # 1대1 채팅방인 경우 상대방 정보 가져오기
            other_participant = ChatParticipant.query.filter(
                and_(
                    ChatParticipant.chat_room_id == room.id,
                    ChatParticipant.user_id != current_user.id
                )
            ).first()
            
            if other_participant:
                other_user = User.query.get(other_participant.user_id)
                private_rooms.append({
                    'room': room,
                    'other_user': other_user
                })
        else:
            # 글로벌 채팅방인지 확인 (전체 채팅방 목록에 제외)
            if global_chat_room and room.id == global_chat_room.id:
                # 글로벌 채팅방은 별도 처리
                pass
            else:
                # 일반 전체 채팅방
                public_rooms.append(room)
    
    # 전체 채팅방 (참여하지 않은 것도 포함하되, 글로벌 채팅방은 제외)
    all_public_rooms = ChatRoom.query.filter(
        ChatRoom.type == 'public'
    ).all()
    
    # 글로벌 채팅방 제외
    if global_chat_room:
        all_public_rooms = [room for room in all_public_rooms if room.id != global_chat_room.id]
    
    # 디버깅 정보
    current_app.logger.info(f'글로벌 채팅방 ID: {global_chat_room.id if global_chat_room else "None"}')
    current_app.logger.info(f'글로벌 채팅방 객체: {global_chat_room}')
    
    return render_template(
        'chat/index.html',
        title='채팅',
        private_rooms=private_rooms,
        public_rooms=public_rooms,
        all_public_rooms=all_public_rooms,
        global_chat_room=global_chat_room
    )

@bp.route('/room/<int:room_id>', methods=['GET'])
@login_required
def view_room(room_id):
    """채팅방 보기"""
    # 채팅방 정보 가져오기
    chat_room = ChatRoom.query.get_or_404(room_id)
    
    # 사용자가 채팅방에 참여했는지 확인
    participation = ChatParticipant.query.filter_by(
        user_id=current_user.id,
        chat_room_id=room_id
    ).first()
    
    # 참여하지 않은 채팅방이면 참여 처리 (public 채팅방인 경우)
    if not participation and chat_room.type == 'public':
        participation = ChatParticipant(
            user_id=current_user.id,
            chat_room_id=room_id
        )
        db.session.add(participation)
        db.session.commit()
    elif not participation:
        # private 채팅방인데 참여자가 아니면 접근 불가
        flash('접근 권한이 없는 채팅방입니다.')
        return redirect(url_for('chat.index'))
    
    # 채팅 메시지 가져오기
    messages = ChatMessage.query.filter_by(chat_room_id=room_id).order_by(ChatMessage.created_at).all()
    
    # 읽음 처리
    participation.last_read_at = datetime.utcnow()
    db.session.commit()
    
    # 1대1 채팅방인 경우 상대방 정보 가져오기
    other_user = None
    if chat_room.type == 'private':
        other_participant = ChatParticipant.query.filter(
            and_(
                ChatParticipant.chat_room_id == room_id,
                ChatParticipant.user_id != current_user.id
            )
        ).first()
        
        if other_participant:
            other_user = User.query.get(other_participant.user_id)
    
    # 참가자 목록 (전체 채팅방인 경우)
    participants = []
    if chat_room.type == 'public':
        participants = ChatParticipant.query.filter_by(chat_room_id=room_id).all()
        participant_users = [User.query.get(p.user_id) for p in participants]
        participants = participant_users
    
    return render_template(
        'chat/room.html',
        title=f'채팅방 - {chat_room.name or "1:1 채팅"}',
        chat_room=chat_room,
        messages=messages,
        other_user=other_user,
        participants=participants
    )

@bp.route('/create/<int:user_id>', methods=['GET', 'POST'])
@login_required
def create_private_chat(user_id):
    """1대1 채팅방 생성 또는 기존 채팅방으로 이동"""
    # 대화 상대 확인
    other_user = User.query.get_or_404(user_id)
    
    # 자기 자신과 채팅 불가
    if other_user.id == current_user.id:
        flash('자신과 채팅할 수 없습니다.')
        return redirect(url_for('chat.index'))
    
    # 이미 존재하는 1대1 채팅방 확인
    # 현재 사용자가 참여한 채팅방
    my_chat_rooms = ChatParticipant.query.filter_by(user_id=current_user.id).all()
    my_room_ids = [p.chat_room_id for p in my_chat_rooms]
    
    # 상대방이 참여한 채팅방
    other_chat_rooms = ChatParticipant.query.filter_by(user_id=other_user.id).all()
    other_room_ids = [p.chat_room_id for p in other_chat_rooms]
    
    # 둘 다 참여한 채팅방 중 private 타입인 것
    common_room_ids = set(my_room_ids).intersection(set(other_room_ids))
    if common_room_ids:
        for room_id in common_room_ids:
            room = ChatRoom.query.get(room_id)
            if room and room.type == 'private':
                # 기존 채팅방으로 이동
                return redirect(url_for('chat.view_room', room_id=room.id))
    
    # 새 채팅방 생성
    chat_room = ChatRoom(type='private')
    db.session.add(chat_room)
    db.session.flush()  # ID 생성을 위해 flush
    
    # 참가자 추가
    participants = [
        ChatParticipant(user_id=current_user.id, chat_room_id=chat_room.id),
        ChatParticipant(user_id=other_user.id, chat_room_id=chat_room.id)
    ]
    db.session.add_all(participants)
    db.session.commit()
    
    return redirect(url_for('chat.view_room', room_id=chat_room.id))

@bp.route('/create/public', methods=['POST'])
@login_required
def create_public_chat():
    """전체 채팅방 생성"""
    room_name = request.form.get('room_name', '').strip()
    
    if not room_name:
        flash('채팅방 이름을 입력해주세요.')
        return redirect(url_for('chat.index'))
    
    # 새 채팅방 생성
    chat_room = ChatRoom(name=room_name, type='public')
    db.session.add(chat_room)
    db.session.flush()  # ID 생성을 위해 flush
    
    # 방장(생성자) 추가
    participant = ChatParticipant(user_id=current_user.id, chat_room_id=chat_room.id)
    db.session.add(participant)
    db.session.commit()
    
    return redirect(url_for('chat.view_room', room_id=chat_room.id))

@bp.route('/send/<int:room_id>', methods=['POST'])
@login_required
def send_message(room_id):
    """메시지 전송"""
    chat_room = ChatRoom.query.get_or_404(room_id)
    
    # 참여자 확인
    participation = ChatParticipant.query.filter_by(
        user_id=current_user.id,
        chat_room_id=room_id
    ).first()
    
    if not participation:
        flash('채팅방에 참여하지 않았습니다.')
        return redirect(url_for('chat.index'))
    
    # 메시지 내용 가져오기
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('메시지 내용을 입력해주세요.')
        return redirect(url_for('chat.view_room', room_id=room_id))
    
    # 메시지 저장
    message = ChatMessage(
        chat_room_id=room_id,
        sender_id=current_user.id,
        content=content
    )
    db.session.add(message)
    
    # 읽음 처리 업데이트
    participation.last_read_at = datetime.utcnow()
    db.session.commit()
    
    # 요청이 AJAX인지 확인하는 방법 (Accept 헤더 확인)
    wants_json = 'application/json' in request.headers.get('Accept', '')
    
    if wants_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender_id': message.sender_id,
                'sender_name': current_user.username,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_self': True
            }
        })
    
    return redirect(url_for('chat.view_room', room_id=room_id))

@bp.route('/api/messages/<int:room_id>', methods=['GET'])
@login_required
def api_get_messages(room_id):
    """채팅 메시지 API"""
    # 참여자 확인
    participation = ChatParticipant.query.filter_by(
        user_id=current_user.id,
        chat_room_id=room_id
    ).first()
    
    if not participation:
        return jsonify({'error': '채팅방에 참여하지 않았습니다.', 'success': False}), 403
    
    # 마지막 메시지 ID 이후의 메시지만 가져오기
    last_id = request.args.get('last_id', 0, type=int)
    
    messages = ChatMessage.query.filter(
        ChatMessage.chat_room_id == room_id,
        ChatMessage.id > last_id
    ).order_by(ChatMessage.created_at).all()
    
    result = []
    for message in messages:
        sender = User.query.get(message.sender_id)
        result.append({
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender_id,
            'sender_name': sender.username if sender else 'Unknown',
            'is_self': message.sender_id == current_user.id,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # 읽음 처리 업데이트
    participation.last_read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(result)

@bp.route('/create', methods=['POST'])
@login_required
def create_chat():
    """상품 채팅방 생성 API"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '유효하지 않은 요청입니다.'}), 400
    
    # 안전하게 판매자 ID와 상품 ID 가져오기
    try:
        seller_id = int(data.get('seller_id', 0))
        product_id = int(data.get('product_id', 0))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '유효하지 않은 ID 값입니다.'}), 400
    
    if seller_id <= 0 or product_id <= 0:
        return jsonify({'success': False, 'message': '유효하지 않은 ID 값입니다.'}), 400
    
    # 판매자 확인
    seller = User.query.get(seller_id)
    if not seller:
        return jsonify({'success': False, 'message': '존재하지 않는 판매자입니다.'}), 404
    
    # 자기 자신과 채팅 불가
    if seller.id == current_user.id:
        return jsonify({'success': False, 'message': '자신과 채팅할 수 없습니다.'}), 400
    
    # 상품 확인
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': '존재하지 않는 상품입니다.'}), 404
    
    # 이미 존재하는 1대1 채팅방 확인
    # 현재 사용자가 참여한 채팅방
    my_chat_rooms = ChatParticipant.query.filter_by(user_id=current_user.id).all()
    my_room_ids = [p.chat_room_id for p in my_chat_rooms]
    
    # 상대방이 참여한 채팅방
    other_chat_rooms = ChatParticipant.query.filter_by(user_id=seller.id).all()
    other_room_ids = [p.chat_room_id for p in other_chat_rooms]
    
    # 둘 다 참여한 채팅방 중 private 타입인 것
    common_room_ids = set(my_room_ids).intersection(set(other_room_ids))
    for room_id in common_room_ids:
        room = ChatRoom.query.get(room_id)
        if room and room.type == 'private':
            # 기존 채팅방으로 이동
            return jsonify({
                'success': True, 
                'redirect_url': url_for('chat.view_room', room_id=room.id)
            })
    
    # 새 채팅방 생성
    chat_room = ChatRoom(type='private')
    db.session.add(chat_room)
    db.session.flush()  # ID 생성을 위해 flush
    
    # 참가자 추가
    participants = [
        ChatParticipant(user_id=current_user.id, chat_room_id=chat_room.id),
        ChatParticipant(user_id=seller.id, chat_room_id=chat_room.id)
    ]
    db.session.add_all(participants)
    
    # 시작 메시지 추가 (상품 정보 포함)
    message = ChatMessage(
        chat_room_id=chat_room.id,
        sender_id=current_user.id,
        content=f"안녕하세요, '{product.title}' 상품에 관심이 있습니다."
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'redirect_url': url_for('chat.view_room', room_id=chat_room.id)
    })

@bp.route('/users', methods=['GET'])
@login_required
def user_list():
    """채팅할 수 있는 사용자 목록 보기"""
    # 검색어가 있는 경우
    search_query = request.args.get('q', '')
    
    if search_query:
        # 사용자 이름이나 이메일로 검색
        users = User.query.filter(
            User.id != current_user.id,  # 자기 자신 제외
            User.is_active == True,      # 활성 사용자만
            (User.username.ilike(f'%{search_query}%') | User.email.ilike(f'%{search_query}%'))
        ).order_by(User.username).all()
    else:
        # 전체 사용자 목록 (자신 제외)
        users = User.query.filter(
            User.id != current_user.id,  # 자기 자신 제외
            User.is_active == True       # 활성 사용자만
        ).order_by(User.username).all()
    
    return render_template(
        'chat/user_list.html',
        title='채팅 상대 선택',
        users=users,
        search_query=search_query
    )

@bp.route('/global', methods=['GET'])
@login_required
def global_chat():
    """글로벌 채팅방 바로가기"""
    # global 선언을 먼저 해야 합니다
    global GLOBAL_CHAT_ROOM_ID
    
    # 글로벌 채팅방 찾기
    global_chat_room = ChatRoom.query.filter_by(name="실시간 전체 채팅").first()
    
    if not global_chat_room and GLOBAL_CHAT_ROOM_ID:
        # 이름으로 찾을 수 없으면 ID로 시도
        global_chat_room = ChatRoom.query.get(GLOBAL_CHAT_ROOM_ID)
    
    if not global_chat_room:
        # 글로벌 채팅방이 없으면 새로 생성
        try:
            global_chat_room = ChatRoom(
                name="실시간 전체 채팅", 
                type="public"
            )
            db.session.add(global_chat_room)
            db.session.flush()  # ID 생성
            
            # 앱 설정 업데이트
            from app import app
            app.config['GLOBAL_CHAT_ROOM_ID'] = global_chat_room.id
            GLOBAL_CHAT_ROOM_ID = global_chat_room.id
            
            db.session.commit()
            current_app.logger.info(f'새 글로벌 채팅방이 생성되었습니다. ID: {global_chat_room.id}')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'글로벌 채팅방 생성 실패: {str(e)}')
            flash('글로벌 채팅방을 찾을 수 없습니다.')
            return redirect(url_for('chat.index'))
    
    # 채팅 목록 페이지로 이동할지, 채팅방으로 바로 이동할지 확인
    direct_access = request.args.get('direct', 'true')
    
    # 사용자가 이미 참여자인지 확인
    participation = ChatParticipant.query.filter_by(
        user_id=current_user.id,
        chat_room_id=global_chat_room.id
    ).first()
    
    # 참여하지 않았다면 자동으로 추가
    if not participation:
        participation = ChatParticipant(
            user_id=current_user.id,
            chat_room_id=global_chat_room.id
        )
        db.session.add(participation)
        db.session.commit()
    
    # 채팅방으로 리디렉션 또는 채팅 목록 페이지 이동
    if direct_access == 'true':
        # 채팅방으로 직접 이동
        return redirect(url_for('chat.view_room', room_id=global_chat_room.id))
    else:
        # 실시간 채팅 탭이 열린 채팅 목록 페이지로 이동
        return redirect(url_for('chat.index', tab='live-chat')) 