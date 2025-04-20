#!/usr/bin/env python3
from app import create_app, db
from app.models import Product, ChatRoom, ChatMessage, ChatParticipant

app = create_app()

def delete_test_products():
    """테스트용으로 등록한 상품들을 삭제합니다."""
    with app.app_context():
        # 테스트 상품 검색 (예: "테스트" 또는 "test"가 포함된 상품)
        test_products = Product.query.filter(
            (Product.title.like('%테스트%')) | 
            (Product.title.like('%test%')) |
            (Product.description.like('%테스트%')) |
            (Product.description.like('%test%'))
        ).all()
        
        count = len(test_products)
        
        if count == 0:
            print("삭제할 테스트 상품이 없습니다.")
            return
        
        # 상품 정보 출력 및 삭제 확인
        print(f"총 {count}개의 테스트 상품을 찾았습니다:")
        for i, product in enumerate(test_products, 1):
            print(f"{i}. {product.title} (ID: {product.id}, 판매자: {product.seller.username})")
        
        confirm = input("\n이 상품들을 모두 삭제하시겠습니까? (y/n): ")
        if confirm.lower() != 'y':
            print("상품 삭제를 취소했습니다.")
            return
        
        # 상품 삭제
        try:
            for product in test_products:
                db.session.delete(product)
            
            db.session.commit()
            print(f"{count}개의 테스트 상품을 성공적으로 삭제했습니다.")
        except Exception as e:
            db.session.rollback()
            print(f"상품 삭제 중 오류가 발생했습니다: {str(e)}")

def delete_global_chat():
    """전체 채팅방과 메시지를 삭제합니다."""
    with app.app_context():
        # 전체 채팅방 찾기
        global_chat = ChatRoom.query.filter_by(name="실시간 전체 채팅").first()
        
        if not global_chat:
            print("'실시간 전체 채팅' 채팅방을 찾을 수 없습니다.")
            return
        
        # 채팅방 정보 및 메시지 수 출력
        message_count = ChatMessage.query.filter_by(chat_room_id=global_chat.id).count()
        participant_count = ChatParticipant.query.filter_by(chat_room_id=global_chat.id).count()
        
        print(f"'실시간 전체 채팅' 채팅방 (ID: {global_chat.id})")
        print(f"메시지 수: {message_count}")
        print(f"참가자 수: {participant_count}")
        
        confirm = input("\n이 채팅방의 모든 메시지를 삭제하시겠습니까? (채팅방 자체는 유지됩니다) (y/n): ")
        if confirm.lower() != 'y':
            print("채팅방 메시지 삭제를 취소했습니다.")
            return
        
        # 채팅 메시지만 삭제 (채팅방 자체는 유지)
        try:
            ChatMessage.query.filter_by(chat_room_id=global_chat.id).delete()
            db.session.commit()
            print(f"'{global_chat.name}' 채팅방의 {message_count}개 메시지를 성공적으로 삭제했습니다.")
        except Exception as e:
            db.session.rollback()
            print(f"채팅 메시지 삭제 중 오류가 발생했습니다: {str(e)}")

def delete_group_chats():
    """그룹 채팅방을 삭제합니다."""
    with app.app_context():
        # 그룹 채팅방 찾기 (실시간 전체 채팅방 제외)
        group_chats = ChatRoom.query.filter(
            (ChatRoom.type == 'public') & 
            (ChatRoom.name != "실시간 전체 채팅")
        ).all()
        
        count = len(group_chats)
        if count == 0:
            print("삭제할 그룹 채팅방이 없습니다.")
            return
        
        # 채팅방 정보 출력
        print(f"총 {count}개의 그룹 채팅방을 찾았습니다:")
        for i, chat in enumerate(group_chats, 1):
            message_count = ChatMessage.query.filter_by(chat_room_id=chat.id).count()
            participant_count = ChatParticipant.query.filter_by(chat_room_id=chat.id).count()
            print(f"{i}. ID: {chat.id}, 이름: {chat.name or '(이름 없음)'}, 메시지: {message_count}개, 참가자: {participant_count}명")
        
        confirm = input("\n이 그룹 채팅방들을 모두 삭제하시겠습니까? (y/n): ")
        if confirm.lower() != 'y':
            print("그룹 채팅방 삭제를 취소했습니다.")
            return
        
        # 그룹 채팅방 삭제
        try:
            for chat in group_chats:
                db.session.delete(chat)
            
            db.session.commit()
            print(f"{count}개의 그룹 채팅방을 성공적으로 삭제했습니다.")
        except Exception as e:
            db.session.rollback()
            print(f"그룹 채팅방 삭제 중 오류가 발생했습니다: {str(e)}")

def delete_private_chats():
    """1대1 채팅방을 삭제합니다."""
    with app.app_context():
        # 1대1 채팅방 찾기
        private_chats = ChatRoom.query.filter_by(type='private').all()
        
        count = len(private_chats)
        if count == 0:
            print("삭제할 1대1 채팅방이 없습니다.")
            return
        
        # 채팅방 정보 출력
        print(f"총 {count}개의 1대1 채팅방을 찾았습니다:")
        for i, chat in enumerate(private_chats, 1):
            message_count = ChatMessage.query.filter_by(chat_room_id=chat.id).count()
            participants = ChatParticipant.query.filter_by(chat_room_id=chat.id).all()
            participant_names = ", ".join([p.user.username for p in participants]) if participants else "없음"
            print(f"{i}. ID: {chat.id}, 참가자: {participant_names}, 메시지: {message_count}개")
        
        confirm = input("\n이 1대1 채팅방들을 모두 삭제하시겠습니까? (y/n): ")
        if confirm.lower() != 'y':
            print("1대1 채팅방 삭제를 취소했습니다.")
            return
        
        # 1대1 채팅방 삭제
        try:
            for chat in private_chats:
                db.session.delete(chat)
            
            db.session.commit()
            print(f"{count}개의 1대1 채팅방을 성공적으로 삭제했습니다.")
        except Exception as e:
            db.session.rollback()
            print(f"1대1 채팅방 삭제 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    while True:
        print("\n==== 테스트 데이터 삭제 도구 ====")
        print("1. 테스트 상품 삭제")
        print("2. 전체 채팅방 메시지 삭제")
        print("3. 그룹 채팅방 삭제")
        print("4. 1대1 채팅방 삭제")
        print("0. 종료")
        
        choice = input("\n옵션을 선택하세요: ")
        
        if choice == '1':
            delete_test_products()
        elif choice == '2':
            delete_global_chat()
        elif choice == '3':
            delete_group_chats()
        elif choice == '4':
            delete_private_chats()
        elif choice == '0':
            break
        else:
            print("잘못된 옵션입니다. 다시 선택해주세요.")
    
    print("프로그램을 종료합니다.") 