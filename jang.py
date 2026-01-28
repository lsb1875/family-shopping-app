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
# 2. 앱 화면 및 스타일 구성 (가로 정렬 필살기)
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🍳")

st.markdown("""
    <style>
    /* 1. 리스트 아이템 전용 컨테이너: 무조건 가로로 나열 (flex-direction: row) */
    .row-container {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        padding: 5px 0px;
        border-bottom: 1px solid #f0f2f6;
    }

    /* 2. 각 요소별 간격 조정 */
    .checkbox-col { flex: 0 0 30px !important; }
    .text-col { flex: 1 1 auto !important; padding-left: 5px; font-size: 16px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .btn-col { flex: 0 0 40px !important; text-align: right; }

    /* 3. 체크박스 기본 여백 제거 */
    .stCheckbox { margin: 0px !important; padding: 0px !important; line-height: 1 !important; }
    
    /* 4. 리스트 내 삭제 버튼 전용 스타일 (쓰레기통 아이콘만) */
    .del-button button {
        background: transparent !important;
        border: none !important;
        padding: 0px !important;
        font-size: 20px !important;
        width: 35px !important;
        height: 35px !important;
    }

    /* 5. 레시피 추천 등 메인 버튼은 글자가 잘 보이게 유지 */
    .stButton > button {
        white-space: nowrap !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 버전 표시
st.caption("v1.0.9 - 리스트 가로 배치 고정 (Flex 모드)") 

st.title("👨‍👩‍👦‍👦 아들둘집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 섹션 (사용자 요청: 세 줄 배치 유지) ---
with st.expander("➕ 누가 무엇을 살까요?", expanded=True):
    who = st.selectbox("누구 사나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 사나요?", placeholder="재료 입력...")
    
    if st.button("장바구니에 추가", use_container_width=True, key="add_btn_main"):
        if new_item:
            st.session_state['list'].append(f"{who}:{new_item}")
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# --- 장바구니 목록 (강제 가로 한 줄 배치) ---
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

        # 표준 st.columns 대신 HTML 구조를 사용하여 강제로 가로 배치
        # 하지만 Streamlit 위젯(체크박스, 버튼)은 columns 안에 있어야 하므로
        # columns를 쓰되 CSS로 해당 컬럼들을 강제로 묶어버립니다.
        
        st.markdown('<div class="row-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
        
        with col1:
            is_selected = st.checkbox("", key=f"check_{i}", label_visibility="collapsed")
            if is_selected:
                selected_ingredients.append(name)
        with col2:
            st.markdown(f"<div class='text-col'>{emoji} {name}</div>", unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="del-button">', unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state['list'].pop(i)
                save_data(st.session_state['list'])
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    if st.button("🧹 전체 목록 삭제", use_container_width=True, key="clear_all"):
        st.session_state['list'] = []
        save_data([])
        st.rerun()

st.divider()

# --- AI 요리 추천 섹션 ---
st.subheader("👨‍🍳 제미나이 레시피")
if st.button("🍳 선택한 재료로 레시피 추천받기", type="primary", use_container_width=True, key="recipe_btn"):
    if not selected_ingredients:
        st.error("재료를 선택해주세요!")
    else:
        with st.spinner('레시피 찾는 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 알려줘."
                response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                st.success("추천 레시피 도착!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")