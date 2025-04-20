from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

# 사용자 모델
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    username = db.Column(db.String(64), nullable=False)
    profile_image = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    bank_name = db.Column(db.String(50), nullable=True)
    account_number = db.Column(db.String(30), nullable=True)
    
    # 관계
    products = db.relationship('Product', backref='seller', lazy='dynamic')
    wallet = db.relationship('Wallet', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# 지갑 모델
class Wallet(db.Model):
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    balance = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    sent_transfers = db.relationship('Transfer', foreign_keys='Transfer.sender_id', backref='sender', lazy='dynamic')
    received_transfers = db.relationship('Transfer', foreign_keys='Transfer.receiver_id', backref='receiver', lazy='dynamic')
    
    def __repr__(self):
        return f'<Wallet {self.id} - User {self.user_id}>'

# 송금 모델
class Transfer(db.Model):
    __tablename__ = 'transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    status = db.Column(db.String(20), default='completed')  # completed, pending, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transfer {self.id} - {self.amount}>'

# 거래 내역 모델
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # CHARGE, PURCHASE, TRANSFER
    amount = db.Column(db.Integer, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_transactions')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_transactions')
    
    def __repr__(self):
        return f'<Transaction {self.id} - {self.type} - {self.amount}>'

# 상품 모델
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, sold, hidden
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    images = db.relationship('ProductImage', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    transfers = db.relationship('Transfer', backref='product', lazy='dynamic')
    
    def __repr__(self):
        return f'<Product {self.id} - {self.title}>'

# 상품 이미지 모델
class ProductImage(db.Model):
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductImage {self.id} - Product {self.product_id}>'

# 신고 모델
class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reported_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reported_reports')
    reported = db.relationship('User', foreign_keys=[reported_id], backref='received_reports')
    product = db.relationship('Product', backref='reports')
    
    def __repr__(self):
        return f'<Report {self.id}>'

# 검색 로그 모델
class SearchLog(db.Model):
    __tablename__ = 'search_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    query = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SearchLog {self.id} - {self.query}>'

# 메시지 모델
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # 관계
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')
    product = db.relationship('Product', backref='messages')
    
    def __repr__(self):
        return f'<Message {self.id} - From: {self.sender_id} To: {self.recipient_id}>'

# 채팅방 모델
class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)  # 전체 채팅방일 경우 이름 지정 가능
    type = db.Column(db.String(20), nullable=False)  # 'private' (1대1) 또는 'public' (전체)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계
    messages = db.relationship('ChatMessage', backref='chat_room', lazy='dynamic', cascade='all, delete-orphan')
    participants = db.relationship('ChatParticipant', backref='chat_room', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ChatRoom {self.id} - {self.type}>'

# 채팅 참가자 모델 (다대다 관계를 위한 중간 테이블)
class ChatParticipant(db.Model):
    __tablename__ = 'chat_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계
    user = db.relationship('User', backref='chat_participations')
    
    def __repr__(self):
        return f'<ChatParticipant - User: {self.user_id}, Room: {self.chat_room_id}>'

# 채팅 메시지 모델
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계
    sender = db.relationship('User', backref='chat_messages')
    
    def __repr__(self):
        return f'<ChatMessage {self.id} - From: {self.sender_id}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id)) 