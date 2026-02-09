# 다국어(멀티렝) 전체 스택 점검 보고서

**점검일**: 2025-02-10  
**범위**: Front(ai_site_20_vt) · Admin(ai_curatorhub_admin) · DB(Firestore: ai-tools, tool_translations, translations)  
**목적**: 다국어 관련 코드 수정 완료 후, 프론트·어드민·DB가 유기적으로 연결되었는지 점검 및 보고.

---

## 1. 종합 평가

| 구분 | 평가 | 비고 |
|------|------|------|
| **데이터 형식 일치** | ✅ 양호 | tool_translations 필드명·구조(Admin 저장 ↔ Front 병합) 일치 |
| **언어 코드 일치** | ✅ 양호 | Admin config · Front translate.js · constants.js 동일(ko, en, ja, zh, ru, es, pt, ar, vi, id, fr, hi, ms) |
| **도구 다국어 흐름** | ✅ 양호 | Admin 저장 → Firestore tool_translations → Front 조회·병합 → 화면 표시 |
| **언어 변경 시 재조회** | ⚠️ 대부분 적용 | 상세/필터/전체/인기 도구는 재조회·재렌더 적용. BuilderSection·QuestionRecommendation은 미적용(알려진 갭) |
| **UI 텍스트 동기화** | ✅ 적용됨 | A6: translations ↔ public/lang/*.json 내보내기/가져오기·CLI 구현 |

**결론**: 다국어 관련 코드는 전반적으로 **유기적으로 잘 연결**되어 있음. 알려진 갭 2건(특정 컴포넌트 언어 변경 시 도구 데이터 재조회 미적용)은 선택 개선 사항으로 두면 됨.

---

## 2. 데이터 형식·정책 일치

### 2.1 tool_translations (도구 콘텐츠 번역)

| 항목 | Admin (저장) | Front (읽기·병합) | 일치 |
|------|--------------|-------------------|------|
| 컬렉션명 | `COLLECTIONS["TOOL_TRANSLATIONS"]` = `tool_translations` | `'tool_translations'` (하드코딩) | ✅ |
| 문서 ID | `{toolId}_{lang}` | `getToolTranslation(toolId, lang)` → `doc(..., translationId)` 동일 | ✅ |
| 필드 | `toolId`, `lang`, `fields` | `translation.fields`, `translation.toolId` 사용 | ✅ |
| fields 키 | shortDescription, description, intro, pros, cons, name(선택) | mergeToolWithTranslation에서 동일 키 참조 | ✅ |
| 필드 값 형태 | `{ "text": str \| list, "status": str }` | _getTranslationFieldValue(fieldData) → fieldData.text (및 .items 호환) | ✅ |

- **Admin**: `ensure_tool_translation_fields_shape()`로 저장 전 정규화. `create_tool_translation`, `update_tool_translation`에서 적용.
- **Front**: `mergeToolWithTranslation(tool, translation)`에서 `fields.name`, `shortDescription`, `description`, `intro`, `pros`, `cons`만 사용. Admin이 저장하는 구조와 동일.

### 2.2 언어 코드

- **Admin**: `admin/config.py` `SUPPORTED_LANGUAGES` (ko, en, ja, zh, ru, es, pt, ar, vi, id, fr, hi, ms). A5에서 프론트와 동일 유지 주석·constants.js에 `ms` 추가 반영.
- **Front**: `translate.js` `supportedLanguages`, `constants.js` `SUPPORTED_LANGUAGES`, `ip-geolocation.js` 동일 13개 코드.
- **도구 번역 적용 언어**: Front `_getCurrentLanguageForMerge()`는 `ko`이면 `null` 반환(번역 조회 생략). 그 외 언어는 동일 코드로 조회.

---

## 3. Front (ai_site_20_vt) 점검

### 3.1 DBManager · 도구 조회·병합

| API | 번역 병합 적용 | 비고 |
|-----|----------------|------|
| getToolById | ✅ | currentLang → getToolTranslation → mergeToolWithTranslation |
| getToolDetailsWithSummary | ✅ | 동일 |
| loadPopularAITools | ✅ | _applyTranslationsToToolList(result) |
| searchToolsByQuery | ✅ | _applyTranslationsToToolList(sortedTools) |
| loadAllTools | ✅ | _applyTranslationsToToolList(sortedTools) |

- `_getCurrentLanguageForMerge()`: `window.translationManager?.getCurrentLanguage()`, 없거나 `ko`면 `null` → 번역 조회 생략.
- `getToolTranslation(toolId, lang)`: `tool_translations/{toolId}_{lang}` 단건 조회.
- `getTranslationsByLanguage(lang)`: `where('lang', '==', lang)`로 목록 조회 후 `_applyTranslationsToToolList`에서 toolId별 맵 구성·병합.

### 3.2 언어 변경 시 재조회·재렌더

| 컴포넌트 | translationComplete 시 동작 | 도구 데이터 재조회 |
|----------|----------------------------|---------------------|
| DetailPageSection | getToolDetailsWithSummary(toolId) → displayToolDetails | ✅ |
| FilterSearchSection | searchToolsByQuery / loadAITools → applyFilters | ✅ |
| TotalPageSection | loadAllTools(1000) → render + translateDynamicElements | ✅ |
| App (인기 도구) | loadPopularTools() → 인기 도구 갱신 | ✅ |
| BuilderSection | translateElement / translatePage만 | ❌ (재조회 없음) |
| QuestionRecommendation | translateElement / translatePage / translateDynamicElements만 | ❌ (재조회 없음) |

- BuilderSection: `loadAllTools(100)`로 한 번 로드 후, 언어 변경 시 도구 목록 재요청 없음. 선택 시 개선 가능.
- QuestionRecommendation: 마스터 플랜에서 “구조 복잡으로 언어 변경 시 재조회/재렌더는 이번에 미적용”으로 명시된 갭.

---

## 4. Admin (ai_curatorhub_admin) 점검

### 4.1 구현 완료 항목 (A1～A6)

| 항목 | 내용 | 파일·위치 |
|------|------|------------|
| A1 | tool_translations 저장 형식 프론트와 일치 (fields.text/status, ensure_tool_translation_fields_shape) | admin/translations.py |
| A2 | 한국어→다국어 생성 플로우 (도구 ID·대상 언어·원본 불러오기·번역 입력·저장) | pages/5_🌐_다국어_관리.py 탭2 |
| A3 | 새 번역 문서 추가 (도구+언어 선택 → 빈 문서 생성) | 동일 탭2 |
| A4 | fields.name 지원 (A2 폼·상세 편집·그리드 name 컬럼) | 동일 페이지·translations |
| A5 | 언어 코드 일치 (config 주석, constants.js에 ms 추가) | admin/config.py, 프론트 constants.js |
| A6 | UI 텍스트 ↔ 프론트 JSON (내보내기/가져오기·CLI) | admin/config.py FRONT_LANG_JSON_DIR, admin/ui_translation_sync.py, 탭1, scripts/ui_translation_sync_cli.py |

### 4.2 Firestore 사용

- **ai-tools**: 한국어 원본. Admin `get_tool_by_id`, `get_all_tools`로 조회. A2에서 “한국어 원본 불러오기”에 사용.
- **tool_translations**: 문서 ID `{toolId}_{lang}`, 필드 toolId, lang, fields. Admin에서 생성/수정, Front에서 조회·병합만.
- **translations**: UI 텍스트 키별 다국어. Admin 탭1에서 조회/편집. A6에서 public/lang/*.json과 동기화.

### 4.3 UI 텍스트 동기화 (A6)

- **Export**: translations 컬렉션 → lang별 `{ "키": "값" }` → `public/lang/{lang}.json` 저장. 모든 문서 키를 모아 lang별 동일 키 집합 유지.
- **Import**: `public/lang/{lang}.json` 읽어 (키, 값)별로 기존 문서는 해당 lang 필드만 update, 없으면 create.
- **경로**: `FRONT_LANG_JSON_DIR` (기본: `../ai_site_20_vt/public/lang`). 환경 변수로 변경 가능.

---

## 5. DB (Firestore) 관점

- **ai-tools**: 스키마 변경 없음. 한국어 원본만 유지.
- **tool_translations**: 별도 컬렉션. 문서 ID·필드 규칙은 위 §2.1과 같음. Front는 읽기 전용.
- **translations**: UI 텍스트. 문서 ID = 키, 필드 = ko, en, ja, zh, … (SUPPORTED_LANGUAGES 키와 동일). Front는 public/lang/*.json 사용, Admin에서 편집 후 내보내기로 반영 가능.

---

## 6. 갭·권장 사항

| 구분 | 내용 | 우선순위 |
|------|------|----------|
| 알려진 갭 | **BuilderSection**: 언어 변경 시 `loadAllTools` 재호출 후 재렌더 없음. 도구 이름/설명이 이전 언어로 남을 수 있음. | 낮음 |
| 알려진 갭 | **QuestionRecommendation**: 언어 변경 시 도구 데이터 재조회/재렌더 미적용(의도된 생략). | 낮음 |
| 운영 | 어드민에서 도구 번역 추가·수정 후, 프론트는 별도 배포 없이 현재 언어로 즉시 반영(재조회 시 병합). | - |
| 운영 | UI 텍스트는 어드민 탭1 편집 후 “내보내기”로 public/lang/*.json 갱신 후 프론트 배포 필요. 또는 CLI `python scripts/ui_translation_sync_cli.py export`를 빌드 단계에 포함 가능. | - |

---

## 7. 참조 문서

- `ai_site_20_vt/docs/MULTILINGUAL_IMPLEMENTATION_MASTER_PLAN.md`
- `ai_site_20_vt/docs/MULTILINGUAL_POLICY_FULLSTACK.md`
- `ai_curatorhub_admin/ADMIN_MULTILINGUAL_WORK_ITEMS.md`
- `ai_site_20_vt/docs/TOOL_CONTENT_MULTILINGUAL_IMPROVEMENT.md`
