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
# 2. 앱 화면 및 스타일 구성 (초밀착 정밀 조정)
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🍳")

st.markdown("""
    <style>
    /* 1. 리스트 줄 가로 배치 고정 및 여백 완전 제거 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 0px !important; 
    }
    
    /* 2. 각 컬럼별 초밀착 너비 설정 */
    /* 체크박스 컬럼: 공간을 25px로 더 줄임 */
    div[data-testid="column"]:nth-child(1) {
        flex: 0 0 25px !important; 
        min-width: 25px !important;
        padding: 0px !important;
    }
    /* 이름 컬럼: 체크박스 바로 옆에서 시작 */
    div[data-testid="column"]:nth-child(2) {
        flex: 1 1 auto !important;
        padding-left: 0px !important;
        margin-left: 0px !important;
    }
    /* 삭제 버튼 컬럼: 오른쪽 끝 정렬 */
    div[data-testid="column"]:nth-child(3) {
        flex: 0 0 45px !important;
        min-width: 45px !important;
        justify-content: flex-end !important;
        padding: 0px !important;
    }

    /* 3. 체크박스 내부 여백 및 라벨 공간 제거 */
    .stCheckbox { 
        margin-bottom: 0px; 
        width: 25px !important;
    }
    .stCheckbox > label {
        padding: 0px !important;
        margin: 0px !important;
        min-height: 0px !important;
    }
    
    /* 4. 삭제 버튼 스타일 */
    .stButton button { 
        padding: 0px !important; 
        width: 30px !important; 
        height: 30px !important;
        border: none !important;
        background: transparent !important;
        font-size: 18px !important;
    }

    /* 5. 이름 텍스트 위치 보정 */
    .item-text {
        font-size: 16px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-top: 2px;
        padding-left: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("👨‍👩‍👦‍👦 아들둘집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 섹션 (세 줄 배치) ---
with st.expander("➕ 누가 무엇을 살까요?", expanded=True):
    who = st.selectbox("누구 사나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 사나요?", placeholder="예: 우유, 사과, 과자...")
    
    if st.button("장바구니에 추가", use_container_width=True, type="secondary"):
        if new_item:
            st.session_state['list'].append(f"{who}:{new_item}")
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# --- 장바구니 목록 (초밀착 정렬) ---
st.subheader("🛒 사야 할 목록")
selected_ingredients = []

if not st.session_state['list']:
    st.info("장바구니가 비어 있습니다.")
else:
    for i, full_item in enumerate(st.session_state['list']):
        if ":" in full_item:
            user, name = full_item.split(":", 1)
            emoji = FAMILY_EMOJI.get(user, FAMILY_EMOJI["기본"])
        else:
            name = full_item
            emoji = FAMILY_EMOJI["기본"]

        # 컬럼 생성 (CSS에서 flex 너비가 우선 적용됨)
        cols = st.columns([0.1, 0.8, 0.1])
        
        with cols[0]:
            is_selected = st.checkbox("", key=f"check_{i}", label_visibility="collapsed")
            if is_selected:
                selected_ingredients.append(name)
        
        with cols[1]:
            # div 태그로 감싸서 추가적인 여백을 완전히 제거
            st.markdown(f"<div class='item-text'>{emoji} {name}</div>", unsafe_allow_html=True)
        
        with cols[2]:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state['list'].pop(i)
                save_data(st.session_state['list'])
                st.rerun()

    # --- 전체 초기화 버튼 ---
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
        with st.spinner('맛있는 레시피를 생각하고 있어요...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 자세히 알려줘."
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                st.success("추천 레시피 도착!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")