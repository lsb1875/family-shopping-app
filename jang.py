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
# 2. 앱 화면 및 스타일 구성
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🍳")

# 강제 가로 배치 및 버튼/체크박스 간격 최소화를 위한 마법의 CSS
st.markdown("""
    <style>
    /* 모바일에서 컬럼이 아래로 쌓이는 것을 방지 */
    [data-testid="column"] {
        flex-direction: row !important;
        align-items: center !important;
        min-width: 0px !important;
    }
    /* 체크박스 여백 극소화 */
    .stCheckbox { margin-bottom: 0px; }
    /* 삭제 버튼을 작고 깔끔하게 */
    .stButton button { 
        padding: 0px 5px !important; 
        height: 30px !important; 
        width: 35px !important;
        border: none !important;
        background: transparent !important;
        font-size: 18px !important;
    }
    /* 텍스트 줄바꿈 방지 */
    .item-row { display: flex; align-items: center; gap: 5px; font-size: 16px; white-space: nowrap; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

st.title("👨‍👩‍👦‍👦 우리집 장보기 리스트")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 섹션 ---
with st.expander("➕ 누가 무엇을 추가할까요?", expanded=True):
    c1, c2, c3 = st.columns([1, 1.5, 0.8])
    with c1:
        who = st.selectbox("누구", ["아빠", "엄마", "큰아들", "작은아들"], label_visibility="collapsed")
    with c2:
        new_item = st.text_input("물품명", placeholder="재료 입력", label_visibility="collapsed")
    with c3:
        if st.button("추가", use_container_width=True, key="add_btn"):
            if new_item:
                st.session_state['list'].append(f"{who}:{new_item}")
                save_data(st.session_state['list'])
                st.rerun()

st.divider()

# --- 장바구니 목록 (강제 가로 정렬) ---
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

        # 좁은 폭을 주어 한 줄에 밀어넣기
        cols = st.columns([0.15, 0.7, 0.15])
        
        with cols[0]:
            is_selected = st.checkbox("", key=f"check_{i}", label_visibility="collapsed")
            if is_selected:
                selected_ingredients.append(name)
        
        with cols[1]:
            st.markdown(f"<div class='item-row'>{emoji} {name}</div>", unsafe_allow_html=True)
        
        with cols[2]:
            # 삭제 버튼을 쓰레기통 이모지로 표시
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state['list'].pop(i)
                save_data(st.session_state['list'])
                st.rerun()

    # --- 모두 초기화 버튼 ---
    st.write("") # 간격 띄우기
    if st.button("🧹 목록 모두 초기화", use_container_width=True):
        st.session_state['list'] = []
        save_data([])
        st.rerun()

st.divider()

# --- AI 요리 추천 섹션 ---
if st.button("👨‍🍳 제미나이 레시피 추천", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.error("재료를 선택해주세요!")
    else:
        with st.spinner('아들들이 좋아할 메뉴 추천 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 자세히 알려줘."
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                st.success("추천 레시피가 도착했습니다!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")