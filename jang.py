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
# 2. 앱 화면 및 스타일 구성 (CSS 정밀 타격)
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🍳")

st.markdown("""
    <style>
    /* 1. 입력 칸(expander 내부)은 세로로 나오게 기본값 유지 */
    
    /* 2. 장바구니 리스트 영역만 강제로 한 줄 배치 */
    div.list-item-container > div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important; /* 줄바꿈 절대 금지 */
        align-items: center !important;
        gap: 0px !important;
    }
    
    /* 3. 컬럼 비율 강제 고정 (모바일 무시) */
    div.list-item-container div[data-testid="column"]:nth-of-type(1) {
        flex: 0 0 40px !important; /* 체크박스 공간 */
        min-width: 40px !important;
    }
    div.list-item-container div[data-testid="column"]:nth-of-type(2) {
        flex: 1 1 auto !important; /* 이름 공간 (나머지 전부) */
        padding-left: 0px !important;
    }
    div.list-item-container div[data-testid="column"]:nth-of-type(3) {
        flex: 0 0 50px !important; /* 삭제 버튼 공간 */
        min-width: 50px !important;
    }

    /* 4. 리스트 내 삭제 버튼(🗑️)만 투명하게 배경 제거 */
    div.list-item-container button {
        background: transparent !important;
        border: none !important;
        padding: 0px !important;
        font-size: 20px !important;
        color: inherit !important;
    }

    /* 5. 텍스트와 체크박스 밀착 */
    .stCheckbox { margin-right: -10px !important; }
    .item-text { font-size: 16px; white-space: nowrap; margin-top: 3px; }
    </style>
    """, unsafe_allow_html=True)

# 버전 표시
st.caption("v1.0.8 - 목록 강제 한 줄 고정 적용") 

st.title("👨‍👩‍👦‍👦 아들둘집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 섹션 (사용자 요청: 세 줄 배치) ---
with st.expander("➕ 누가 무엇을 살까요?", expanded=True):
    # 컬럼 없이 나열하면 자동으로 세 줄이 됩니다.
    who = st.selectbox("누구 사나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 사나요?", placeholder="재료 입력...")
    
    if st.button("장바구니에 추가", use_container_width=True, key="main_add_btn"):
        if new_item:
            st.session_state['list'].append(f"{who}:{new_item}")
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# --- 장바구니 목록 (초밀착 한 줄 정렬) ---
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

        # CSS가 이 div 안의 컬럼만 잡아내도록 클래스 부여
        st.markdown(f'<div class="list-item-container">', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([0.1, 0.8, 0.1])
        
        with c1:
            is_selected = st.checkbox("", key=f"check_{i}", label_visibility="collapsed")
            if is_selected:
                selected_ingredients.append(name)
        with c2:
            st.markdown(f"<div class='item-text'>{emoji} {name}</div>", unsafe_allow_html=True)
        with c3:
            # 삭제 버튼 (아이콘만 표시)
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state['list'].pop(i)
                save_data(st.session_state['list'])
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    if st.button("🧹 전체 목록 삭제", use_container_width=True, key="clear_all"):
        st.session_state['list'] = []
        save_data([])
        st.rerun()

st.divider()

# --- AI 요리 추천 섹션 ---
st.subheader("👨‍🍳 제미나이 레시피")
# 이제 이 버튼의 글자가 정상적으로 보입니다.
if st.button("🍳 선택한 재료로 레시피 추천받기", type="primary", use_container_width=True, key="recipe_btn"):
    if not selected_ingredients:
        st.error("재료를 선택해주세요!")
    else:
        with st.spinner('아들들이 좋아할 레시피 찾는 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 알려줘."
                response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                st.success("추천 레시피 도착!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")