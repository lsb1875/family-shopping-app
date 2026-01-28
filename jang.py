import streamlit as st
import os
from google import genai

# ==========================================
# 1. 설정 및 데이터 관리
# ==========================================
# Streamlit Secrets에서 API 키를 가져옵니다.
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

DATA_FILE = "shopping_list.txt"

# 아들 둘 가족 구성원 이모지 설정
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

# 리스트 아이템만 한 줄에 밀착되도록 하는 CSS
st.markdown("""
    <style>
    /* 리스트 영역의 컬럼들이 모바일에서도 가로로 유지되게 함 */
    [data-testid="column"] {
        flex-direction: row !important;
        align-items: center !important;
    }
    .stCheckbox { margin-bottom: 0px; }
    .item-text { font-size: 16px; margin-top: 5px; white-space: nowrap; }
    /* 삭제 버튼 스타일 */
    .stButton button { padding: 2px 5px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("👨‍👩‍👦‍👦 우리집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 섹션 (요청하신 세 줄 배치) ---
with st.expander("➕ 누가 무엇을 살까요?", expanded=True):
    # 각 요소를 세로로 나열하여 입력을 편하게 만듭니다.
    who = st.selectbox("누가 사나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 사나요?", placeholder="예: 우유, 사과, 과자...")
    
    if st.button("장바구니에 추가", use_container_width=True, type="secondary"):
        if new_item:
            st.session_state['list'].append(f"{who}:{new_item}")
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# --- 장바구니 목록 (한 줄 정렬 유지) ---
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

        # [체크박스 | 이름 | 삭제] 비율 조정
        cols = st.columns([0.15, 0.7, 0.15])
        
        with cols[0]:
            is_selected = st.checkbox("", key=f"check_{i}", label_visibility="collapsed")
            if is_selected:
                selected_ingredients.append(name)
        
        with cols[1]:
            st.markdown(f"<div class='item-text'>{emoji} {name}</div>", unsafe_allow_html=True)
        
        with cols[2]:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state['list'].pop(i)
                save_data(st.session_state['list'])
                st.rerun()

    # 목록 관리 버튼
    st.write("")
    if st.button("🧹 전체 목록 삭제", use_container_width=True):
        st.session_state['list'] = []
        save_data([])
        st.rerun()

st.divider()

# --- AI 요리 추천 섹션 (화면 하단 배치) ---
st.subheader("👨‍🍳 제미나이 레시피")
if st.button("🍳 선택한 재료로 레시피 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.error("재료를 선택해주세요!")
    else:
        with st.spinner('아들들이 좋아할 메뉴 추천 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 알려줘."
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                st.success("추천 레시피가 도착했습니다!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")