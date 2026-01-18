# 빠른 시작 가이드

## 1. 실행 방법

```bash
# ai_curator_hub_admin 폴더로 이동
cd ai_curator_hub_admin

# 패키지 설치 (필요한 경우)
pip install -r requirements.txt

# 어드민 실행
streamlit run admin_main.py
```

## 2. 접속

브라우저에서 자동으로 열리거나, 수동으로 접속:
- URL: http://localhost:8502

## 3. Firebase 설정

### 방법 1: 상위 폴더의 serviceAccountKey.json 사용 (기본)
- 상위 폴더(`ai_curator_hub_db/`)에 `serviceAccountKey.json` 파일이 있으면 자동으로 사용됩니다.

### 방법 2: 환경 변수 설정
```bash
# Windows PowerShell
$env:FIREBASE_SERVICE_ACCOUNT_KEY_PATH="C:\path\to\serviceAccountKey.json"

# Linux/Mac
export FIREBASE_SERVICE_ACCOUNT_KEY_PATH="/path/to/serviceAccountKey.json"
```

### 방법 3: JSON 문자열로 설정 (운영 환경)
```bash
# Windows PowerShell
$env:FIREBASE_SERVICE_ACCOUNT_KEY_JSON='{"type":"service_account",...}'

# Linux/Mac
export FIREBASE_SERVICE_ACCOUNT_KEY_JSON='{"type":"service_account",...}'
```

## 4. 메뉴 구조

Streamlit의 Multi-Page 기능을 사용하므로, `pages/` 폴더의 파일들이 자동으로 사이드바 메뉴에 표시됩니다.

현재 사용 가능한 페이지:
- 📊 대시보드
- 🔧 AI 도구 관리
- 👥 사용자 관리
- 📝 AI 레시피 관리
- 🌐 다국어 관리
- 📦 카테고리 관리
- 📋 등록 신청 관리
- 💳 유료 서비스 관리
- ⚙️ 설정

## 5. 문제 해결

### Firebase 연결 실패
- `serviceAccountKey.json` 파일이 올바른 위치에 있는지 확인
- 파일 권한 확인
- 환경 변수 설정 확인

### 모듈을 찾을 수 없음
- `ai_curator_hub_admin` 폴더에서 실행하는지 확인
- Python 경로 확인

### 포트 충돌
- `.streamlit/config.toml`에서 포트 변경 (기본: 8502)
