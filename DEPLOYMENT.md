# 🚀 Aicuatorhub Admin 배포 가이드

이 문서는 Aicuatorhub Admin 시스템을 운영 환경에 배포하는 방법을 설명합니다.

## 📋 배포 전 준비사항

### 1. Firebase 서비스 계정 키 준비

운영 환경에서는 **절대 파일로 저장하지 마세요**. 환경 변수로 관리해야 합니다.

```bash
# serviceAccountKey.json 파일의 내용을 JSON 문자열로 변환
# Windows PowerShell
$keyContent = Get-Content serviceAccountKey.json -Raw
$keyContent | Out-File -Encoding utf8 key.txt

# Linux/Mac
cat serviceAccountKey.json | jq -c .
```

### 2. GitHub 저장소 준비

- 코드를 GitHub에 푸시
- `serviceAccountKey.json`은 `.gitignore`에 포함되어 있어야 함 (이미 설정됨)

---

## 🌐 배포 옵션

### 옵션 1: Streamlit Cloud (추천 ⭐)

**장점:**
- 무료 플랜 제공
- GitHub 연동 자동화
- 설정이 매우 간단
- 자동 HTTPS 지원

**단계:**

1. **Streamlit Cloud 가입**
   - https://share.streamlit.io 접속
   - GitHub 계정으로 로그인

2. **앱 배포**
   - "New app" 클릭
   - Repository: `your-username/your-repo` 선택
   - Branch: `main` (또는 `master`)
   - Main file path: `admin_main.py`

3. **환경 변수 설정**
   - Settings → Secrets 탭
   - 다음 형식으로 추가:

   ```toml
   FIREBASE_SERVICE_ACCOUNT_KEY_JSON = """
   {
     "type": "service_account",
     "project_id": "...",
     "private_key_id": "...",
     "private_key": "...",
     ...
   }
   """
   ```

4. **배포 완료**
   - 자동으로 배포 시작
   - URL: `https://your-app-name.streamlit.app`

---

### 옵션 2: Railway (추천 ⭐⭐)

**장점:**
- 무료 크레딧 제공 ($5/월)
- Docker 지원
- GitHub 자동 배포
- 환경 변수 관리 편리

**단계:**

1. **Railway 가입**
   - https://railway.app 접속
   - GitHub 계정으로 로그인

2. **프로젝트 생성**
   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - 저장소 선택

3. **환경 변수 설정**
   - Settings → Variables 탭
   - 다음 변수 추가:
     ```
     FIREBASE_SERVICE_ACCOUNT_KEY_JSON = {전체 JSON 문자열}
     ENV = production
     ```

4. **배포 설정**
   - Railway가 자동으로 Dockerfile 감지
   - 또는 Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run admin_main.py --server.port=$PORT`

5. **도메인 설정 (선택)**
   - Settings → Domains
   - 커스텀 도메인 추가 가능

---

### 옵션 3: Render

**장점:**
- 무료 플랜 제공 (제한적)
- GitHub 연동
- 쉬운 설정

**단계:**

1. **Render 가입**
   - https://render.com 접속
   - GitHub 계정으로 로그인

2. **Web Service 생성**
   - "New +" → "Web Service"
   - GitHub 저장소 연결
   - 설정:
     - Name: `aicuatorhub-admin`
     - Environment: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `streamlit run admin_main.py --server.port=$PORT --server.address=0.0.0.0`

3. **환경 변수 설정**
   - Environment 탭
   - `FIREBASE_SERVICE_ACCOUNT_KEY_JSON` 추가 (전체 JSON 문자열)
   - `ENV=production` 추가

---

### 옵션 4: Fly.io

**장점:**
- 무료 플랜 제공
- 전 세계 엣지 배포
- 빠른 속도

**단계:**

1. **Fly.io CLI 설치**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   
   # Mac/Linux
   curl -L https://fly.io/install.sh | sh
   ```

2. **로그인 및 앱 생성**
   ```bash
   fly auth login
   fly launch
   ```

3. **환경 변수 설정**
   ```bash
   fly secrets set FIREBASE_SERVICE_ACCOUNT_KEY_JSON="$(cat serviceAccountKey.json | jq -c .)"
   fly secrets set ENV=production
   ```

4. **배포**
   ```bash
   fly deploy
   ```

---

### 옵션 5: 자체 서버 (AWS, GCP, Azure 등)

**Docker 사용 시:**

```bash
# 이미지 빌드
docker build -t aicuatorhub-admin .

# 실행 (환경 변수 포함)
docker run -d \
  -p 8501:8501 \
  -e FIREBASE_SERVICE_ACCOUNT_KEY_JSON='{"type":"service_account",...}' \
  -e ENV=production \
  --name aicuatorhub-admin \
  aicuatorhub-admin
```

**직접 실행 시:**

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export FIREBASE_SERVICE_ACCOUNT_KEY_JSON='{"type":"service_account",...}'
export ENV=production

# 실행
streamlit run admin_main.py --server.port=8501
```

---

## 🔒 보안 체크리스트

- [ ] `serviceAccountKey.json`이 `.gitignore`에 포함되어 있는지 확인
- [ ] GitHub에 키 파일이 커밋되지 않았는지 확인
- [ ] 운영 환경에서는 환경 변수만 사용
- [ ] HTTPS 사용 (대부분의 플랫폼에서 자동 제공)
- [ ] 접근 제한 설정 (필요 시)

---

## 🔧 환경 변수 참조

| 변수명 | 설명 | 필수 | 예시 |
|--------|------|------|------|
| `FIREBASE_SERVICE_ACCOUNT_KEY_JSON` | Firebase 키 전체 JSON 문자열 | ✅ | `{"type":"service_account",...}` |
| `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` | 파일 경로 (로컬 개발용) | ❌ | `serviceAccountKey.json` |
| `ENV` | 환경 설정 | ❌ | `production` |

---

## 🐛 문제 해결

### Firebase 연결 실패
- 환경 변수가 올바르게 설정되었는지 확인
- JSON 문자열이 올바른 형식인지 확인 (이스케이프 문자 주의)
- Firebase 프로젝트 권한 확인

### 포트 오류
- 플랫폼에서 제공하는 `$PORT` 환경 변수 사용
- Streamlit은 기본적으로 8501 포트 사용

### 의존성 오류
- `requirements.txt`에 모든 패키지가 포함되어 있는지 확인
- Python 버전 호환성 확인 (3.9+ 권장)

---

## 📞 지원

문제가 발생하면:
1. 로그 확인 (각 플랫폼의 로그 탭)
2. 로컬에서 테스트 (`ENV=production`으로)
3. 프로젝트 관리자에게 문의

---

## 📝 업데이트 배포

대부분의 플랫폼은 GitHub에 푸시하면 자동으로 재배포됩니다.

수동 재배포가 필요한 경우:
- Streamlit Cloud: "Reboot app" 버튼
- Railway: "Redeploy" 버튼
- Render: "Manual Deploy" 버튼
