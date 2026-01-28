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
# 2. 앱 화면 및 스타일 구성 (초강력 간격 제거)
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🍳")

st.markdown("""
    <style>
    /* 1. 컬럼 사이의 기본 간격(1rem)을 완전히 제거 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
    }
    
    /* 2. 체크박스 컬럼 너비를 최소화 (30px) */
    div[data-testid="column"]:nth-of-type(1) {
        flex: 0 0 30px !important;
        min-width: 30px !important;
    }
    
    /* 3. 이름 컬럼을 체크박스 바로 옆에 배치 */
    div[data-testid="column"]:nth-of-type(2) {
        flex: 1 1 auto !important;
        margin-left: -5px !important; /* 음수 마진으로 더 바짝 붙임 */
    }
    
    /* 4. 삭제 버튼 컬럼 */
    div[data-testid="column"]:nth-of-type(3) {
        flex: 0 0 40px !important;
        min-width: 40px !important;
        text-align: right !important;
    }

    /* 5. 체크박스 자체의 여백 제거 */
    .stCheckbox { margin: 0px !important; padding: 0px !important; }
    .stCheckbox div[data-testid="stMarkdownContainer"] { display: none; } /* 라벨 공간 삭제 */
    
    /* 6. 삭제 버튼 스타일 */
    .stButton button { 
        background: transparent !important;
        border: none !important;
        padding: 0px !important;
        font-size: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 적용 여부 확인용 (화면 상단에 작은 글씨가 보이면 업데이트 성공)
st.caption("v1.0.5 - 초밀착 모드 적용됨") 

st.title("👨‍👩‍👦‍👦 우리집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 섹션 (세 줄 배치) ---
with st.expander("➕ 누가 무엇을 살까요?", expanded=True):
    who = st.selectbox("누가 사나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 사나요?", placeholder="예: 우유, 사과...")
    
    if st.button("장바구니에 추가", use_container_width=True):
        if new_item:
            st.session_state['list'].append(f"{who}:{new_item}")
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# --- 장바구니 목록 ---
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

        # 초밀착 컬럼 배치
        c1, c2, c3 = st.columns([0.1, 0.8, 0.1])
        
        with c1:
            is_selected = st.checkbox("", key=f"check_{i}", label_visibility="collapsed")
            if is_selected:
                selected_ingredients.append(name)
        with c2:
            st.markdown(f"<div style='font-size:16px; margin-top:3px;'>{emoji} {name}</div>", unsafe_allow_html=True)
        with c3:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state['list'].pop(i)
                save_data(st.session_state['list'])
                st.rerun()

    st.write("")
    if st.button("🧹 전체 목록 삭제", use_container_width=True):
        st.session_state['list'] = []
        save_data([])
        st.rerun()

st.divider()

# --- AI 요리 추천 ---
if st.button("🍳 레시피 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.error("재료를 선택해주세요!")
    else:
        with st.spinner('생각 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 알려줘."
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                st.success("추천 레시피 도착!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")