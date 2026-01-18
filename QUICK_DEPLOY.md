# 🚀 빠른 배포 가이드

## 가장 빠른 방법: Streamlit Cloud (5분)

1. **GitHub에 코드 푸시**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Streamlit Cloud 접속**
   - https://share.streamlit.io
   - GitHub로 로그인

3. **앱 생성**
   - "New app" 클릭
   - Repository 선택
   - Main file: `admin_main.py`

4. **Secrets 설정**
   - Settings → Secrets
   - `serviceAccountKey.json` 파일 내용을 복사하여 다음 형식으로 붙여넣기:
   
   ```toml
   FIREBASE_SERVICE_ACCOUNT_KEY_JSON = """
   {여기에 JSON 내용 전체 붙여넣기}
   """
   ```

5. **완료!** 
   - 자동으로 배포 시작
   - URL: `https://your-app-name.streamlit.app`

---

## Railway 배포 (10분)

1. **Railway 가입**
   - https://railway.app
   - GitHub 연동

2. **프로젝트 생성**
   - "New Project" → "Deploy from GitHub repo"
   - 저장소 선택

3. **환경 변수 설정**
   - Settings → Variables
   - `FIREBASE_SERVICE_ACCOUNT_KEY_JSON` 추가
   - 값: `serviceAccountKey.json` 파일의 전체 내용 (JSON 문자열)

4. **배포 완료**
   - 자동으로 배포 시작
   - 커스텀 도메인 설정 가능

---

## Firebase 키 변환 방법

### Windows PowerShell
```powershell
# JSON 파일 내용을 한 줄로 변환
$content = Get-Content serviceAccountKey.json -Raw
$content -replace "`n", "" -replace "`r", "" -replace " ", ""
```

### Linux/Mac
```bash
# jq 사용 (설치 필요: brew install jq)
cat serviceAccountKey.json | jq -c .

# 또는 Python 사용
python -c "import json; print(json.dumps(json.load(open('serviceAccountKey.json'))))"
```

---

## ⚠️ 중요 사항

1. **절대 GitHub에 `serviceAccountKey.json`을 커밋하지 마세요!**
   - 이미 `.gitignore`에 포함되어 있습니다
   - 확인: `git status`로 파일이 나타나지 않아야 함

2. **환경 변수 형식**
   - JSON 전체를 문자열로 넣어야 합니다
   - 따옴표 이스케이프 주의

3. **테스트**
   - 배포 후 Firebase 연결이 정상인지 확인
   - 로그에서 오류 메시지 확인

---

자세한 내용은 `DEPLOYMENT.md` 참고
