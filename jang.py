import streamlit as st
import os
from google import genai

# ==========================================
# 1. 설정 및 데이터 관리
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

DATA_FILE = "shopping_list.txt"

FAMILY_EMOJI = {
    "아빠": "👨",
    "엄마": "👩",
    "큰아들": "👦",
    "작은아들": "👶",
    "기본": "🛒"
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_data(items):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for item in items:
            f.write(item + "\n")

# ==========================================
# 2. 앱 화면 및 스타일 구성 (CSS 강화)
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🍳")

# 모바일에서 컬럼이 쌓이는 것을 방지하고 한 줄로 강제 고정하는 CSS
st.markdown("""
    <style>
    /* 리스트 줄(HorizontalBlock)의 세로 쌓기 방지 및 한 줄 고정 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 5px !important;
    }
    
    /* 각 컬럼의 최소 너비를 없애서 좁은 화면에서도 나란히 배치 */
    div[data-testid="column"] {
        min-width: 0px !important;
        flex: 1 1 auto !important;
    }

    /* 체크박스 크기와 여백 조정 */
    .stCheckbox { margin-bottom: 0px; }
    
    /* 삭제 버튼(쓰레기통) 크기 및 위치 조정 */
    .stButton button { 
        padding: 0px !important; 
        width: 35px !important; 
        height: 35px !important;
        border: none !important;
        background: transparent !important;
        font-size: 20px !important;
    }

    /* 텍스트 줄바꿈 방지 및 폰트 크기 */
    .item-text {
        font-size: 16px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("👨‍👩‍👦‍👦 우리 집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 섹션 (요청하신 세 줄 배치 유지) ---
with st.expander("➕ 누가 무엇을 살까요?", expanded=True):
    who = st.selectbox("누가 사나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 사나요?", placeholder="예: 우유, 사과, 과자...")
    
    if st.button("장바구니에 추가", use_container_width=True, type="secondary"):
        if new_item:
            st.session_state['list'].append(f"{who}:{new_item}")
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# --- 장바구니 목록 (초밀착 가로 한 줄 고정) ---
st.subheader("🛒 사야 할 목록")
selected_ingredients = []

if not st.session_state['list']:
    st.info("장바구니가 비어 있습니다.")
else:
    # 목록 영역을 컨테이너로 감싸서 관리
    list_container = st.container()
    with list_container:
        for i, full_item in enumerate(st.session_state['list']):
            if ":" in full_item:
                user, name = full_item.split(":", 1)
                emoji = FAMILY_EMOJI.get(user, FAMILY_EMOJI["기본"])
            else:
                name = full_item
                emoji = FAMILY_EMOJI["기본"]

            # 컬럼 비율을 모바일에 최적화 (체크박스 15%, 이름 70%, 삭제버튼 15%)
            cols = st.columns([0.15, 0.7, 0.15])
            
            with cols[0]:
                is_selected = st.checkbox("", key=f"check_{i}", label_visibility="collapsed")
                if is_selected:
                    selected_ingredients.append(name)
            
            with cols[1]:
                # 텍스트와 이모지를 한 줄에 표시
                st.markdown(f"<div class='item-text'>{emoji} {name}</div>", unsafe_allow_html=True)
            
            with cols[2]:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state['list'].pop(i)
                    save_data(st.session_state['list'])
                    st.rerun()

    # --- 목록 관리 버튼 ---
    st.write("")
    if st.button("🧹 전체 목록 삭제", use_container_width=True):
        st.session_state['list'] = []
        save_data([])
        st.rerun()

st.divider()

# --- AI 요리 추천 섹션 ---
st.subheader("👨‍🍳 제미나이 레시피")
if st.button("🍳 선택한 재료로 레시피 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.error("재료를 선택해주세요!")
    else:
        with st.spinner('아들들이 좋아할 메뉴 추천 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 자세히 알려줘."
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                st.success("추천 레시피 도착!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")