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
# 2. 앱 화면 및 스타일 구성 (모바일 가로 배치 종결판)
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🍳")

# [v1.1.0] 모바일 가로 정렬 강제 고정 및 깔끔한 UI를 위한 CSS
st.markdown("""
    <style>
    /* 1. 모바일에서 모든 가로 블록(st.columns)의 줄바꿈을 원천 차단 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 0px !important;
    }
    
    /* 2. 각 컬럼의 너비를 강제로 고정하여 겹침 방지 */
    div[data-testid="column"]:nth-child(1) {
        flex: 0 0 35px !important;
        min-width: 35px !important;
    }
    div[data-testid="column"]:nth-child(2) {
        flex: 1 1 auto !important;
        padding-left: 5px !important;
    }
    div[data-testid="column"]:nth-child(3) {
        flex: 0 0 45px !important;
        min-width: 45px !important;
        text-align: right !important;
    }

    /* 3. 체크박스 라벨 공간 삭제 및 여백 최소화 */
    .stCheckbox { margin-bottom: 0px !important; }
    .stCheckbox label { padding: 0 !important; }
    
    /* 4. 리스트 아이템 디자인 (카드 느낌) */
    .shopping-item {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 8px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #f0f2f6;
    }

    /* 5. 삭제 버튼(쓰레기통) 투명 스타일 - 다른 버튼에 영향 안 미치도록 */
    button[key*="del_"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        font-size: 20px !important;
        color: #ff4b4b !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 버전 정보 표시
st.caption("v1.1.0 - 모바일 가로 정렬 종결 버전")

st.title("👨‍👩‍👦‍👦 아들둘집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 섹션 (입력창 3줄 배치) ---
with st.container(border=True):
    st.markdown("##### ➕ 물품 추가")
    who = st.selectbox("누가 사나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 사나요?", placeholder="재료명을 입력하세요...")
    
    if st.button("장바구니에 담기", use_container_width=True, type="secondary"):
        if new_item:
            st.session_state['list'].append(f"{who}:{new_item}")
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# --- 장바구니 목록 (카드형 가로 한 줄 정렬) ---
st.subheader("🛒 사야 할 목록")
selected_ingredients = []

if not st.session_state['list']:
    st.info("장바구니가 비어 있습니다. 물품을 추가해 보세요!")
else:
    for i, full_item in enumerate(st.session_state['list']):
        if ":" in full_item:
            user, name = full_item.split(":", 1)
            emoji = FAMILY_EMOJI.get(user, FAMILY_EMOJI["기본"])
        else:
            name = full_item
            emoji = FAMILY_EMOJI["기본"]

        # 전체 행을 카드 스타일로 감쌈
        st.markdown('<div class="shopping-item">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([0.1, 0.8, 0.1])
        
        with c1:
            is_selected = st.checkbox("", key=f"check_{i}", label_visibility="collapsed")
            if is_selected:
                selected_ingredients.append(name)
        with c2:
            st.markdown(f"<div style='margin-top:4px; font-size:16px;'>{emoji} <b>{name}</b></div>", unsafe_allow_html=True)
        with c3:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state['list'].pop(i)
                save_data(st.session_state['list'])
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    if st.button("🧹 전체 목록 삭제", use_container_width=True):
        st.session_state['list'] = []
        save_data([])
        st.rerun()

st.divider()

# --- AI 요리 추천 섹션 ---
st.subheader("👨‍🍳 제미나이 추천 레시피")
if st.button("🍳 선택한 재료로 레시피 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.warning("목록에서 재료를 선택(체크)한 후 버튼을 눌러주세요!")
    else:
        with st.spinner('아들들이 좋아할 메뉴를 고민 중입니다...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 자세히 알려줘."
                response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                st.success("짜잔! 추천 레시피입니다.")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류가 발생했어요: {str(e)}")