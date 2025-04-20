from app import create_app
from app.models import ChatRoom

app = create_app()

with app.app_context():
    global_chat = ChatRoom.query.filter_by(name="실시간 전체 채팅").first()
    if global_chat:
        print(f"글로벌 채팅방 ID: {global_chat.id}")
    else:
        print("글로벌 채팅방이 아직 생성되지 않았습니다.") 