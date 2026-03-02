"""
어드민 시스템 설정 관리
"""
import os

# Firebase 컬렉션 이름
COLLECTIONS = {
    "AI_TOOLS": "ai-tools",
    "USERS": "users",
    "RECIPES": "my_recipe",  # 사용자 개인 레시피
    "PUBLIC_RECIPES": "public_recipe_collection",  # 공개 레시피 (AI 레시피 관리에서 사용)
    "CATEGORIES": "categories",
    # Albatross: 인기 질문 (원본/번역)
    "POPULAR_QUESTIONS": "popular_questions",
    "POPULAR_QUESTION_TRANSLATIONS": "popular_question_translations",
    "TRANSLATIONS": "translations",  # UI 텍스트 번역 (정적 파일 기반)
    "TOOL_TRANSLATIONS": "tool_translations",  # AI 도구 콘텐츠 번역 (DB 기반)
    "APPLICATIONS": "applications",
    "PAID_SERVICES": "paid-services",
    "TOOL_REGISTRATIONS": "applications/tool-registrations",
    "PAID_SERVICE_REQUESTS": "applications/paid-service-requests",
    "BANNERS": "banners"  # 배너 관리
}

# 배너 위치 정의
BANNER_SPOTS = {
    "web_top": {
        "id": "web_top",
        "name": "웹 상단",
        "icon": "🖥️",
        "description": "웹사이트 페이지 최상단"
    },
    "web_middle": {
        "id": "web_middle",
        "name": "웹 중단",
        "icon": "🖥️",
        "description": "웹사이트 페이지 중단"
    },
    "web_bottom": {
        "id": "web_bottom",
        "name": "웹 하단",
        "icon": "🖥️",
        "description": "웹사이트 페이지 하단"
    },
    "mobile_top": {
        "id": "mobile_top",
        "name": "모바일 상단",
        "icon": "📱",
        "description": "모바일 페이지 최상단"
    },
    "mobile_middle": {
        "id": "mobile_middle",
        "name": "모바일 중단",
        "icon": "📱",
        "description": "모바일 페이지 중단"
    },
    "mobile_bottom": {
        "id": "mobile_bottom",
        "name": "모바일 하단",
        "icon": "📱",
        "description": "모바일 페이지 하단"
    }
}

# 배너 노출 페이지 (프론트 HTML 페이지별 배너 영역 관리)
# id: 프론트 라우트/파일명과 매칭용 (예: total_page → total_page.html)
BANNER_PAGES = {
    "all": {"id": "all", "name": "전체 페이지", "description": "모든 HTML 페이지에 노출"},
    "total_page": {"id": "total_page", "name": "메인/종합", "description": "total_page.html"},
    "ai_comb_list": {"id": "ai_comb_list", "name": "AI 콤보 목록", "description": "ai_comb_list.html"},
    "ai_comb_detail": {"id": "ai_comb_detail", "name": "AI 콤보 상세", "description": "ai_comb_detail.html"},
    "builder": {"id": "builder", "name": "빌더", "description": "builder.html"},
    "detail_sp": {"id": "detail_sp", "name": "상세(SP)", "description": "detail_sp.html"},
    "filter_search": {"id": "filter_search", "name": "필터/검색", "description": "filter_search.html"},
    "profile": {"id": "profile", "name": "프로필", "description": "profile.html"},
    "question_recommendation": {"id": "question_recommendation", "name": "질문 추천", "description": "question_recommendation.html"},
    "service_apply_add": {"id": "service_apply_add", "name": "서비스 신청 추가", "description": "service_apply_add.html"},
    "service_apply_basic": {"id": "service_apply_basic", "name": "서비스 신청 기본", "description": "service_apply_basic.html"},
    "service_apply_verified": {"id": "service_apply_verified", "name": "서비스 신청 검증", "description": "service_apply_verified.html"},
    "service_sales_page": {"id": "service_sales_page", "name": "서비스 판매", "description": "service_sales_page.html"},
}

# 배너 상태
BANNER_STATUS = {
    "live": "LIVE (Visible)",
    "off": "OFF (Hidden)",
    "scheduled": "SCHEDULED (Reserve)"
}

# 국가 목록 (타겟팅용)
COUNTRIES = {
    "KR": "Korea",
    "JP": "Japan",
    "CN": "China",
    "SG": "Singapore",
    "MY": "Malaysia",
    "VN": "Vietnam",
    "ID": "Indonesia",
    "TH": "Thailand",
    "US": "United States",
    "CA": "Canada",
    "GB": "United Kingdom",
    "AU": "Australia",
    "DE": "Germany",
    "FR": "France",
    "ES": "Spain",
    "IT": "Italy",
    "RU": "Russia",
    "BR": "Brazil",
    "MX": "Mexico",
    "IN": "India",
    "PH": "Philippines"
}

# 지원 언어 목록 (aicuratorhub.com 기준)
# A5: 프론트(translate.js supportedLanguages, constants.js SUPPORTED_LANGUAGES)와 키 목록 동일 유지
SUPPORTED_LANGUAGES = {
    "ko": {"name": "한국어", "native": "한국어"},
    "en": {"name": "English", "native": "English"},
    "ja": {"name": "日本語", "native": "日本語"},
    "zh": {"name": "中文", "native": "中文"},
    "ru": {"name": "Русский", "native": "Русский"},
    "es": {"name": "Español", "native": "Español"},
    "pt": {"name": "Português", "native": "Português"},
    "ar": {"name": "العربية", "native": "العربية"},
    "vi": {"name": "Tiếng Việt", "native": "Tiếng Việt"},
    "id": {"name": "Bahasa Indonesia", "native": "Bahasa Indonesia"},
    "fr": {"name": "Français", "native": "Français"},
    "hi": {"name": "हिन्दी", "native": "हिन्दी"},
    "ms": {"name": "Bahasa Melayu", "native": "Bahasa Melayu"},
    "it": {"name": "Italiano", "native": "Italiano"},
    "de": {"name": "Deutsch", "native": "Deutsch"},
    "tr": {"name": "Türkçe", "native": "Türkçe"}
}

# 필수 지원 언어 (오리진 언어 제외) - HTML mockup 기준
REQUIRED_LANGUAGES = ["ja", "zh", "ru", "es", "pt", "ar", "ms", "id"]

# 오리진 언어 (원본 언어)
ORIGIN_LANGUAGES = ["ko", "en"]

# 카테고리 정보
CATEGORIES = {
    "전체": {"id": "all", "icon": "🌐", "color": "#6366f1"},
    "텍스트 생성": {"id": "text-generation", "icon": "📝", "color": "#8b5cf6"},
    "이미지 생성": {"id": "image-generation", "icon": "🎨", "color": "#ec4899"},
    "음성/오디오": {"id": "audio", "icon": "🎵", "color": "#f59e0b"},
    "비디오 제작": {"id": "video", "icon": "🎬", "color": "#ef4444"},
    "코드 작성": {"id": "code", "icon": "💻", "color": "#10b981"},
    "데이터 분석": {"id": "data-analysis", "icon": "📊", "color": "#3b82f6"},
    "생산성": {"id": "productivity", "icon": "⚡", "color": "#f97316"},
    "마케팅": {"id": "marketing", "icon": "📢", "color": "#06b6d4"},
    "교육": {"id": "education", "icon": "🎓", "color": "#84cc16"},
    "디자인": {"id": "design", "icon": "✨", "color": "#a855f7"},
    "비즈니스": {"id": "business", "icon": "💼", "color": "#14b8a6"},
    "기타": {"id": "other", "icon": "🔮", "color": "#64748b"}
}

# 번역 타입
TRANSLATION_TYPES = {
    "menu": "메뉴",
    "tool_info": "도구 정보",
    "other": "기타"
}

# 환경 설정
ENV = os.getenv("ENV", "development")
DEBUG = ENV == "development"

# Firebase 설정
# serviceAccountKey.json 파일을 여러 위치에서 찾도록 설정
# admin_main.py에서 환경 변수를 설정하므로, 여기서는 fallback 경로만 계산
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 프로젝트 루트 (ai_curatorhub_admin)
_base_dir = os.path.dirname(_project_root)  # 상위 디렉토리 (bigbluewave_website)

# 우선순위: 1) 프로젝트 루트, 2) ai_curator_hub_db 폴더, 3) 상위 디렉토리
_default_key_paths = [
    os.path.join(_project_root, "serviceAccountKey.json"),  # 프로젝트 루트 (최우선)
    os.path.join(_base_dir, "ai_curator_hub_db", "serviceAccountKey.json"),
    os.path.join(_base_dir, "serviceAccountKey.json")
]

# 존재하는 첫 번째 경로를 사용
_default_key_path = None
for path in _default_key_paths:
    if os.path.exists(path):
        _default_key_path = path
        break
# 경로를 찾지 못한 경우 프로젝트 루트 경로를 기본값으로 사용
if _default_key_path is None:
    _default_key_path = _default_key_paths[0]

FIREBASE_SERVICE_ACCOUNT_KEY_PATH = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_KEY_PATH", 
    _default_key_path
)
FIREBASE_SERVICE_ACCOUNT_KEY_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_JSON")

# A6: UI 텍스트 ↔ 프론트 JSON 동기화용 경로 (프론트 public/lang 폴더)
# Streamlit Cloud 등 배포 환경에서 _base_dir 경로가 없을 수 있으므로 예외 시 빈 문자열로 폴백
try:
    _front_lang_default = os.path.join(_base_dir, "ai_site_20_vt", "public", "lang")
except Exception:
    _front_lang_default = ""
FRONT_LANG_JSON_DIR = os.getenv("FRONT_LANG_JSON_DIR", _front_lang_default)
