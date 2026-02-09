# 어드민 멀티렝 다국어 관리 페이지 – 고려사항 및 작업 목록

## 0. 배경

지금까지 계획(TOOL_CONTENT_MULTILINGUAL_IMPROVEMENT.md)은 **프론트** 언어별 적용(DBManager 병합, 언어 변경 시 재조회)에 대한 항목별 작업(§5.4)만 상세히 적었고, **어드민 멀티렝 다국어 관리 페이지**는 정책·개선 제안 수준만 있었다. 이 문서는 **어드민 측이 프론트 계획에서 어떻게 고려되는지**와 **어드민에서 진행해야 할 작업**을 항목별로 나열한 것이다.

- 전체 정책: MULTILINGUAL_POLICY_FULLSTACK.md §4(Admin 개선안), §7(권장 적용 순서).  
- 상세 문서는 `ai_site_20_vt/docs/` 참고.

---

## 1. 프론트 계획이 어드민에 기대하는 것

- **데이터 형식**: 프론트 DBManager 병합 유틸은 `tool_translations` 문서를 다음 형태로 기대한다.
  - 문서 ID: `{toolId}_{lang}` (예: `tldv_ja`).
  - 필드: `toolId`, `lang`, `fields` (객체).
  - `fields` 내부: `shortDescription`, `description`, `intro`, `pros`, `cons` (각각 `{ text: 문자열 또는 배열, status?: 문자열 }` 등). 이름까지 다국어로 쓰려면 `fields.name` 추가.
- **저장 주체**: 위 형식으로 데이터를 **쓰는** 것은 어드민(또는 배치 스크립트)이다. 프론트는 **읽기·병합**만 한다.
- **언어 코드**: `lang` 값(예: `ja`, `zh`, `en`)은 Admin `admin/config.SUPPORTED_LANGUAGES`와 동일한 코드를 써야 프론트 `getCurrentLanguage()`와 맞춰진다.

---

## 2. 어드민 다국어 관리 페이지 현재 상태 (요약)

| 구분 | 현재 동작 | 비고 |
|------|-----------|------|
| **탭1: UI 텍스트 번역** | `translations` 컬렉션 조회/검색/상세 편집 (ko, en, ja, zh 등) | 프론트는 `public/lang/*.json` 사용. 동기화 경로는 별도 결정 필요. |
| **탭2: AI 도구 콘텐츠 번역** | `tool_translations` 조회/검색/상세 편집. `create_tool_translation` 함수 있음 | **이미 있는** 번역 문서만 편집 가능. "도구 선택 → ai-tools 한국어 불러오기 → 대상 언어로 새 문서 생성" 플로우는 화면에 없을 수 있음. |

즉, **"한국어(ai-tools)를 불러와 다른 언어로 저장"**하는 한 번에 끝나는 플로우가 어드민 페이지에 있으면, 운영이 쉬워진다.

---

## 3. 어드민 측 항목별 작업 목록

| 항목 | 작업 | 파일·위치 | 상세 |
|------|------|-----------|------|
| **A1. 저장 형식이 프론트와 일치하는지 확인** | 어드민에서 `tool_translations` 저장 시 사용하는 필드명·구조가 프론트 병합 규칙과 같은지 점검 | `admin/translations.py` (create_tool_translation, update_tool_translation), `pages/5_🌐_다국어_관리.py` | 프론트는 `fields.shortDescription`, `fields.description`, `fields.intro`, `fields.pros`, `fields.cons` (및 선택 `fields.name`)를 읽음. 어드민 저장 시 동일 키로 저장해야 함. 각 필드가 `{ text: 문자열 또는 배열, status?: ... }` 형태인지 확인. |
| **A2. "한국어에서 다국어 생성" 플로우 추가 (권장)** | 도구 선택 → ai-tools에서 해당 도구 한국어 필드 로드 → 대상 언어 선택 → 번역 입력(또는 자동 번역) → tool_translations에 저장 | `pages/5_🌐_다국어_관리.py` (탭2), `admin/tools.py`(ai-tools 조회) | "AI 도구 콘텐츠 번역" 탭에 예: [도구 선택] 드롭다운/검색 → [대상 언어] 선택 → [한국어 원본 보기] (ai-tools에서 name, description, pros, cons 등 표시) → [번역 입력] 또는 [자동 번역] → [저장] 시 `create_tool_translation(tool_id, lang, data)` 호출. |
| **A3. 새 번역 문서 생성 UI** | 아직 `tool_translations`에 없는 (toolId, lang) 조합에 대해 "새 번역 추가" 버튼/폼 제공 | `pages/5_🌐_다국어_관리.py` | 현재는 기존 문서만 목록에 나오면 편집 가능. "도구 ID + 언어"를 선택해 새 문서를 만드는 진입점이 있으면, 번역이 없는 도구·언어도 채울 수 있음. (A2와 연계 가능.) |
| **A4. fields.name 지원 (선택)** | 도구 이름까지 다국어로 쓸 경우 `tool_translations.fields`에 `name` 필드 저장 가능하게 함 | `pages/5_🌐_다국어_관리.py` 상세 편집 폼, `admin/translations.py` | 프론트 병합 유틸은 `fields.name?.text`가 있으면 도구 이름을 그걸로 덮어씀. 어드민 편집 폼에 "도구 이름(번역)" 입력란을 추가하고, 저장 시 `fields.name = { text: "...", status: "..." }` 형태로 넣으면 됨. |
| **A5. 언어 코드 일치** | 어드민에서 쓰는 언어 코드(ja, zh, en 등)가 `admin/config.SUPPORTED_LANGUAGES` 및 프론트와 동일한지 유지 | `admin/config.py`, 다국어 관리 탭의 언어 목록 | 적용: `admin/config.py`에 프론트와 동일 유지 주석 추가. 프론트 `constants.js` SUPPORTED_LANGUAGES에 `ms` 추가하여 admin·translate.js·ip-geolocation과 동일하게 정렬. |
| **A6. UI 텍스트 번역과 프론트 JSON (선택)** | 탭1(UI 텍스트)에서 편집한 내용을 프론트 `public/lang/*.json`과 동기화할지 결정 후, 필요 시 내보내기/가져오기 기능 | `pages/5_🌐_다국어_관리.py`, 스크립트 또는 빌드 단계 | 적용: 탭1에 "UI 텍스트 ↔ 프론트 JSON 동기화" 섹션 추가(내보내기/가져오기 버튼). `admin/config.py` FRONT_LANG_JSON_DIR, `admin/ui_translation_sync.py` export/import 함수. CLI: `python scripts/ui_translation_sync_cli.py export|import`. |

---

## 4. 정리

- **프론트 계획(방안 A)**이 동작하려면, **어드민에서 `tool_translations`에 프론트가 기대하는 형식으로 데이터가 들어가야** 한다. 따라서 **A1(저장 형식 일치)**은 필수에 가깝고, **A2/A3(한국어→다국어 생성·새 문서 추가)**는 운영 편의를 위해 권장한다.
- **A4(fields.name)**는 "도구 이름까지 다국어"를 할 때만, **A5(언어 코드)**는 설정 일관성, **A6(UI 텍스트↔JSON)**는 별도 정책 결정 후 진행하면 된다.
