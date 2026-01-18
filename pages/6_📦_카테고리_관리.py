"""
카테고리 관리 페이지
"""
import streamlit as st
import sys
import os
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.firebase import get_db
from admin.components import render_page_header
from admin.config import COLLECTIONS, CATEGORIES
from admin.categories import (
    get_all_categories, get_category_statistics, get_tools_by_category, update_category
)
from admin.utils import format_value

# 페이지 설정
st.set_page_config(
    page_title="카테고리 관리 - Aicuatorhub Admin",
    page_icon="📦",
    layout="wide"
)

# Firebase 연결
db = get_db()
if db is None:
    st.error("⚠️ Firebase 연결에 실패했습니다.")
    st.stop()

# 세션 상태 초기화
if 'selected_category_id' not in st.session_state:
    st.session_state.selected_category_id = None
if 'selected_category_data' not in st.session_state:
    st.session_state.selected_category_data = None
if 'is_edit_mode' not in st.session_state:
    st.session_state.is_edit_mode = False

# 페이지 헤더
render_page_header("📦 카테고리 관리", "카테고리를 조회하고 관리할 수 있습니다.")

# 서브 메뉴
submenu = st.radio(
    "메뉴",
    ["카테고리 목록", "카테고리 통계", "카테고리 편집"],
    key="category_submenu",
    horizontal=True
)

st.markdown("---")

# 카테고리 목록
if submenu == "카테고리 목록":
    st.markdown("### 📋 카테고리 목록")
    
    categories = get_all_categories()
    stats = get_category_statistics()
    
    if categories:
        # 카테고리 카드 형태로 표시
        cols = st.columns(3)
        
        for idx, category in enumerate(categories):
            with cols[idx % 3]:
                with st.container():
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, {category['color']}15, {category['color']}05);
                        border: 2px solid {category['color']};
                        border-radius: 12px;
                        padding: 1.5rem;
                        margin-bottom: 1rem;
                        text-align: center;
                    ">
                        <div style="font-size: 3rem; margin-bottom: 0.5rem;">{category['icon']}</div>
                        <h3 style="color: {category['color']}; margin: 0.5rem 0;">{category['name']}</h3>
                        <p style="color: #64748b; font-size: 0.9rem; margin: 0.5rem 0;">
                            ID: {category['id']}
                        </p>
                        <div style="
                            background: {category['color']};
                            color: white;
                            padding: 0.5rem 1rem;
                            border-radius: 20px;
                            font-weight: bold;
                            margin-top: 1rem;
                        ">
                            {category['toolCount']}개 도구
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"상세보기", key=f"view_{category['id']}", use_container_width=True):
                        st.session_state.selected_category_id = category['id']
                        st.session_state.selected_category_data = category
                        st.session_state.current_submenu = "카테고리 편집"
                        st.rerun()
        
        # 테이블 형태로도 표시
        st.markdown("---")
        st.markdown("### 📊 카테고리 테이블")
        
        table_data = []
        for category in categories:
            table_data.append({
                "순서": category['order'],
                "아이콘": category['icon'],
                "카테고리명": category['name'],
                "ID": category['id'],
                "색상": category['color'],
                "도구 수": category['toolCount'],
                "_id": category['id']
            })
        
        df = pd.DataFrame(table_data)
        
        # AgGrid 설정
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection('single')
        gb.configure_default_column(
            resizable=True,
            sortable=True,
            filterable=True,
            editable=False
        )
        
        gb.configure_column("순서", width=80)
        gb.configure_column("아이콘", width=80)
        gb.configure_column("카테고리명", width=200)
        gb.configure_column("ID", width=200)
        gb.configure_column("색상", width=120)
        gb.configure_column("도구 수", width=100)
        gb.configure_column("_id", hide=True)
        
        grid_options = gb.build()
        
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            height=400,
            width='100%',
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            key="category_grid",
            theme='streamlit'
        )
        
        # 선택 이벤트 처리
        selected_rows = grid_response.get('selected_rows', [])
        
        if isinstance(selected_rows, pd.DataFrame):
            selected_rows = selected_rows.to_dict('records')
        elif selected_rows is None:
            selected_rows = []
        
        if len(selected_rows) > 0:
            try:
                selected_row = selected_rows[0]
                clicked_category_id = str(selected_row.get('_id', '')).strip()
                
                if clicked_category_id and st.session_state.selected_category_id != clicked_category_id:
                    st.session_state.selected_category_id = clicked_category_id
                    category_data = next((c for c in categories if c['id'] == clicked_category_id), None)
                    if category_data:
                        st.session_state.selected_category_data = category_data
                    st.rerun()
            except Exception as e:
                if st.session_state.get('debug_mode', False):
                    st.error(f"데이터 매칭 오류: {e}")
    else:
        st.warning("카테고리 데이터가 없습니다.")

# 카테고리 통계
elif submenu == "카테고리 통계":
    st.markdown("### 📊 카테고리별 통계")
    
    stats = get_category_statistics()
    categories = get_all_categories()
    
    # 전체 통계
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        total_tools = stats.get("all", 0)
        st.metric("전체 도구 수", f"{total_tools:,}개")
    
    with col_stat2:
        active_categories = sum(1 for cat in categories if cat['toolCount'] > 0)
        st.metric("활성 카테고리", f"{active_categories}개")
    
    with col_stat3:
        avg_tools = sum(cat['toolCount'] for cat in categories) / len(categories) if categories else 0
        st.metric("카테고리당 평균 도구", f"{avg_tools:.1f}개")
    
    st.markdown("---")
    
    # 카테고리별 도구 수 차트
    if categories:
        st.markdown("#### 카테고리별 도구 수")
        
        chart_data = []
        for category in sorted(categories, key=lambda x: x['toolCount'], reverse=True):
            chart_data.append({
                "카테고리": category['name'],
                "도구 수": category['toolCount']
            })
        
        chart_df = pd.DataFrame(chart_data)
        
        # 막대 그래프
        st.bar_chart(chart_df.set_index("카테고리"))
        
        # 상세 테이블
        st.markdown("#### 상세 통계")
        st.dataframe(chart_df, use_container_width=True)
        
        # 카테고리별 도구 목록 보기
        st.markdown("---")
        st.markdown("#### 카테고리별 도구 목록")
        
        selected_category_for_tools = st.selectbox(
            "카테고리 선택",
            ["전체"] + [cat['name'] for cat in categories],
            key="category_tools_select"
        )
        
        if selected_category_for_tools != "전체":
            category_id = next((cat['id'] for cat in categories if cat['name'] == selected_category_for_tools), None)
            if category_id:
                tools = get_tools_by_category(category_id)
                
                if tools:
                    st.info(f"**{selected_category_for_tools}** 카테고리에 속한 도구: {len(tools)}개")
                    
                    tools_data = []
                    for tool in tools[:20]:  # 최대 20개만 표시
                        tools_data.append({
                            "ID": tool.get("id", "-"),
                            "이름": tool.get("name", "-"),
                            "회사": tool.get("company", "-"),
                            "상태": tool.get("status", "-")
                        })
                    
                    if tools_data:
                        tools_df = pd.DataFrame(tools_data)
                        st.dataframe(tools_df, use_container_width=True)
                    
                    if len(tools) > 20:
                        st.caption(f"총 {len(tools)}개 중 20개만 표시됩니다.")
                else:
                    st.info(f"**{selected_category_for_tools}** 카테고리에 속한 도구가 없습니다.")

# 카테고리 편집
elif submenu == "카테고리 편집":
    st.markdown("### ✏️ 카테고리 편집")
    
    categories = get_all_categories()
    
    if not categories:
        st.warning("카테고리 데이터가 없습니다.")
    else:
        # 카테고리 선택
        category_names = [cat['name'] for cat in categories]
        selected_category_name = st.selectbox(
            "편집할 카테고리 선택",
            category_names,
            index=category_names.index(st.session_state.selected_category_data['name']) if st.session_state.selected_category_data and st.session_state.selected_category_data.get('name') in category_names else 0,
            key="edit_category_select"
        )
        
        selected_category = next((c for c in categories if c['name'] == selected_category_name), None)
        
        if selected_category:
            st.session_state.selected_category_data = selected_category
            st.session_state.selected_category_id = selected_category['id']
            
            st.markdown("---")
            st.markdown(f"#### {selected_category['icon']} {selected_category['name']} 편집")
            
            with st.form("edit_category_form"):
                col_edit1, col_edit2 = st.columns(2)
                
                with col_edit1:
                    category_name_kr = st.text_input(
                        "카테고리명 (한글) *",
                        value=selected_category.get('nameKr', selected_category['name']),
                        key="edit_name_kr"
                    )
                    category_name_en = st.text_input(
                        "카테고리명 (영문)",
                        value=selected_category.get('nameEn', selected_category['name']),
                        key="edit_name_en"
                    )
                    category_icon = st.text_input(
                        "아이콘 (이모지)",
                        value=selected_category.get('icon', ''),
                        key="edit_icon",
                        help="예: 📝, 🎨, 💻 등"
                    )
                
                with col_edit2:
                    category_color = st.color_picker(
                        "색상",
                        value=selected_category.get('color', '#6366f1'),
                        key="edit_color"
                    )
                    category_order = st.number_input(
                        "순서",
                        min_value=0,
                        value=selected_category.get('order', 0),
                        key="edit_order",
                        help="숫자가 작을수록 앞에 표시됩니다."
                    )
                    st.info(f"**현재 도구 수**: {selected_category['toolCount']}개")
                
                col_save1, col_save2 = st.columns([1, 1])
                with col_save1:
                    submitted = st.form_submit_button("💾 저장", use_container_width=True, type="primary")
                with col_save2:
                    cancel = st.form_submit_button("❌ 취소", use_container_width=True)
                
                if submitted:
                    if not category_name_kr:
                        st.error("카테고리명 (한글)은 필수입니다.")
                    else:
                        update_data = {
                            "nameKr": category_name_kr,
                            "nameEn": category_name_en if category_name_en else category_name_kr,
                            "icon": category_icon if category_icon else selected_category['icon'],
                            "color": category_color,
                            "order": category_order
                        }
                        
                        if update_category(selected_category['id'], update_data):
                            st.success("✅ 카테고리 정보가 업데이트되었습니다!")
                            get_category_statistics.clear()
                            st.rerun()

# 사이드바 통계
with st.sidebar:
    st.markdown("### 📊 빠른 통계")
    
    try:
        stats = get_category_statistics()
        total_tools = stats.get("all", 0)
        st.metric("전체 도구 수", f"{total_tools:,}개")
        
        categories = get_all_categories()
        active_categories = sum(1 for cat in categories if cat['toolCount'] > 0)
        st.metric("활성 카테고리", f"{active_categories}개")
        
        # 상위 3개 카테고리
        if categories:
            st.markdown("#### 상위 카테고리")
            sorted_cats = sorted(categories, key=lambda x: x['toolCount'], reverse=True)[:3]
            for cat in sorted_cats:
                st.write(f"{cat['icon']} **{cat['name']}**: {cat['toolCount']}개")
    except Exception as e:
        st.error(f"통계 조회 실패: {str(e)}")
    
    # 캐시 초기화
    if st.button("🔄 캐시 초기화", use_container_width=True):
        get_category_statistics.clear()
        get_all_categories.clear()
        st.success("캐시가 초기화되었습니다!")
        st.rerun()
