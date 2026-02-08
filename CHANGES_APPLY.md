# 변경 사항 반영 방법

## 1. Git으로 저장소에 반영하기

로컬에서 변경한 내용을 Git에 커밋하고 원격(예: GitHub)에 푸시하려면:

```powershell
# 프로젝트 폴더로 이동
cd c:\bigbluewave_website\ai_curatorhub_admin

# 변경된 파일 확인
git status

# 변경·추가된 파일 스테이징
git add "pages/2_🔧_AI_도구_관리.py"
git add "pages/5_🌐_다국어_관리.py"
git add CODE_REVIEW_IMPROVEMENTS.md
# 또는 한 번에:
# git add .

# 커밋 (메시지로 변경 내용 요약)
git commit -m "fix: 도구 상세 선택 시 하단 정보 갱신, 다국어 검색 UI/검색 로직 수정, 코드 검토 문서 추가"

# 원격 저장소에 푸시 (기본 브랜치가 main인 경우)
git push origin main
```

- **다른 브랜치**를 쓰는 경우: `git push origin <브랜치이름>`
- **첫 푸시**이거나 upstream이 없으면: `git push -u origin main`

---

## 2. 로컬에서 실행해 보기

배포 전에 로컬에서 동작 확인:

```powershell
cd c:\bigbluewave_website\ai_curatorhub_admin
streamlit run admin_main.py
```

브라우저에서 열리면:

1. **AI 도구 관리** → 도구 조회 → 그리드에서 **다른 제품을 연속으로 클릭**해도 하단 상세 정보가 바뀌는지 확인
2. **다국어 관리** → UI 텍스트 번역 탭에서 **검색 버튼**이 탭 안에 보이는지, **한국어/영어 메뉴 이름**으로 검색되는지 확인

---

## 3. 이미 배포 중인 경우 (Streamlit Cloud / Railway 등)

코드를 **Git에 푸시**하면 대부분 자동으로 다시 배포됩니다.

1. 위 **1번**대로 `git add` → `git commit` → `git push origin main` 실행
2. Streamlit Cloud / Railway 대시보드에서 **배포 로그** 확인
3. 배포가 끝나면 해당 URL에서 위 2번 항목처럼 동작 확인

수동 배포나 캐시 초기화가 필요하면 각 서비스 문서를 참고하면 됩니다.

---

## 변경된 파일 요약

| 파일 | 내용 |
|------|------|
| `pages/2_🔧_AI_도구_관리.py` | 도구 상세 영역 위젯에 동적 key 적용 → 다른 제품 클릭 시 하단 정보 갱신 |
| `pages/5_🌐_다국어_관리.py` | 검색 UI를 탭 내부로 이동, 한국어/영어 검색 수정, 세션·key 정리 |
| `CODE_REVIEW_IMPROVEMENTS.md` | 전체 코드 검토 및 개선 항목 정리 (신규) |
