# Aicuatorhub Admin 시스템

Aicuatorhub 웹사이트의 데이터를 관리하는 통합 어드민 시스템입니다.

## 🚀 시작하기

### 1. 필요한 패키지 설치

```bash
cd ai_curator_hub_admin
pip install -r requirements.txt
```

### 2. Firebase 인증 설정

`serviceAccountKey.json` 파일이 프로젝트 루트에 있는지 확인하세요.
또는 환경 변수를 설정하세요:

```bash
# Windows PowerShell
$env:FIREBASE_SERVICE_ACCOUNT_KEY_PATH="serviceAccountKey.json"

# Linux/Mac
export FIREBASE_SERVICE_ACCOUNT_KEY_PATH="serviceAccountKey.json"
```

### 3. 어드민 패널 실행

```bash
streamlit run admin_main.py
```

브라우저가 자동으로 열리며 어드민 패널이 표시됩니다.
기본 포트: `8502`

## 📁 프로젝트 구조

```
ai_curator_hub_admin/
├── admin_main.py              # 메인 진입점
├── admin/                     # 공통 모듈
│   ├── __init__.py
│   ├── config.py             # 설정 관리
│   ├── firebase.py            # Firebase 초기화
│   ├── menu.py                # 메뉴 시스템
│   ├── utils.py               # 유틸리티 함수
│   └── components.py          # 공통 UI 컴포넌트
├── pages/                     # Streamlit Multi-Page
│   ├── 1_📊_대시보드.py
│   ├── 2_🔧_AI_도구_관리.py
│   ├── 3_👥_사용자_관리.py
│   ├── 4_📝_AI_레시피_관리.py
│   ├── 5_🌐_다국어_관리.py
│   ├── 6_📦_카테고리_관리.py
│   ├── 7_📋_등록_신청_관리.py
│   ├── 8_💳_유료_서비스_관리.py
│   └── 9_⚙️_설정.py
├── .streamlit/
│   ├── config.toml            # Streamlit 설정
│   └── custom.css             # 커스텀 스타일
└── README.md
```

## 📋 주요 기능

### 현재 구현된 기능
- ✅ 기본 구조 및 메뉴 시스템
- ✅ Firebase 연결
- ✅ 대시보드 기본 통계 (준비 중)
- ✅ AI 도구 관리 페이지 (기본 구조)

### 개발 예정 기능
- 🔄 AI 도구 관리 (기존 단일 패널 기능 통합)
- 🔄 사용자 관리
- 🔄 다국어 관리
- 🔄 카테고리 관리
- 🔄 등록 신청 관리
- 🔄 레시피 관리
- 🔄 유료 서비스 관리

## 🔧 설정

### 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` | Firebase 서비스 계정 키 파일 경로 | `serviceAccountKey.json` |
| `FIREBASE_SERVICE_ACCOUNT_KEY_JSON` | Firebase 서비스 계정 키 JSON 문자열 | - |
| `ENV` | 환경 (development/production) | `development` |

### Streamlit 설정

`.streamlit/config.toml` 파일에서 포트, 테마 등을 설정할 수 있습니다.

## 📝 개발 가이드

### 새 페이지 추가하기

1. `pages/` 폴더에 새 파일 생성
2. 파일명 형식: `{순서}_{아이콘}_{이름}.py`
3. `admin/menu.py`의 `get_menu_items()`에 메뉴 항목 추가

### 공통 모듈 사용하기

```python
from admin.firebase import get_db
from admin.components import render_page_header
from admin.config import COLLECTIONS
from admin.utils import normalize_id, format_value
```

## 🚢 배포

### 로컬 배포
```bash
streamlit run admin_main.py
```

### 운영 환경 배포

**빠른 시작:** [`QUICK_DEPLOY.md`](QUICK_DEPLOY.md) 참고 (5분 배포)

**상세 가이드:** [`DEPLOYMENT.md`](DEPLOYMENT.md) 참고

#### 추천 배포 플랫폼
- **Streamlit Cloud** (가장 간단, 무료) ⭐
- **Railway** (유연함, $5/월 크레딧) ⭐⭐
- **Render** (무료 플랜 제공)
- **Fly.io** (엣지 배포)

#### Docker 배포
```bash
docker build -t aicuatorhub-admin .
docker run -p 8501:8501 \
  -e FIREBASE_SERVICE_ACCOUNT_KEY_JSON='{"type":"service_account",...}' \
  -e ENV=production \
  aicuatorhub-admin
```

#### 환경 변수 설정 (운영)
운영 환경에서는 **반드시** `FIREBASE_SERVICE_ACCOUNT_KEY_JSON` 환경 변수를 사용하세요.
파일로 저장하지 마세요!

## 📞 지원

문제가 발생하거나 질문이 있으시면 프로젝트 관리자에게 문의하세요.

## 📄 라이선스

© 2025 Aicuatorhub. All rights reserved.
