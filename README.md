# 중고거래 플랫폼

PRD 문서 기반으로 구현된 중고거래 웹 애플리케이션입니다.

## 기능

- **회원 관리**: 회원가입, 로그인, 프로필 수정
- **상품 관리**: 상품 등록, 수정, 조회, 검색
- **내부 지갑**: 잔액 확인, 다른 사용자에게 송금, 상품 구매
- **신고 시스템**: 사용자 및 상품 신고, 자동 신고 처리
- **관리자 기능**: 사용자/상품/신고 관리, 통계 대시보드

## 기술 스택

- **Backend**: Flask, SQLAlchemy, JWT
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript (템플릿 기반)

## 시작하기

### 로컬 실행

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 데이터베이스 초기화
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 서버 실행
flask run
```

### Docker 실행

```bash
docker-compose up --build
```

## API 엔드포인트

애플리케이션은 웹 UI와 함께 REST API를 제공합니다:

- **인증**: `/api/register`, `/api/login`
- **상품**: `/api/products`, `/api/products/<id>`
- **지갑**: `/api/wallet`, `/api/wallet/transfers`, `/api/wallet/transfer`
- **신고**: `/api/report/user/<id>`, `/api/report/product/<id>`
- **관리자**: `/api/admin/users`, `/api/admin/users/<id>`

## 보안 기능

- 비밀번호 해싱
- JWT 기반 인증
- 세션 관리
- 입력 검증 및 이스케이핑
