import streamlit as st
import os
from google import genai

# ==========================================
# 1. 설정 및 데이터 관리
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

DATA_FILE = "shopping_list.txt"

# 가족 이모지 설정
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

# 모바일 가로 정렬 강제 고정 및 여백 제거를 위한 CSS
st.markdown("""
    <style>
    /* 1. 모바일에서 컬럼이 세로로 쌓이는 것을 강제로 방지 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    div[data-testid="column"] {
        min-width: 0px !important;
        flex-grow: 1 !important;
    }
    
    /* 2. 요소 간 간격 좁히기 */
    .stCheckbox { margin-bottom: 0px; }
    .stButton button { 
        padding: 2px 5px !important; 
        height: auto !important; 
        font-size: 16px !important;
        border: 1px solid #ddd !important;
    }
    
    /* 3. 텍스트가 줄바꿈되지 않고 한 줄에 보이게 설정 */
    .item-text {
        font-size: 15px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("👨‍👩‍👦‍👦 우리집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 섹션 (강제 가로 배치) ---
with st.container():
    c1, c2, c3 = st.columns([1, 1.8, 0.8])
    with c1:
        who = st.selectbox("누구", ["아빠", "엄마", "큰아들", "작은아들"], label_visibility="collapsed")
    with c2:
        new_item = st.text_input("물품명", placeholder="재료 입력", label_visibility="collapsed")
    with c3:
        if st.button("추가", use_container_width=True):
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

        # [체크박스 | 이름 | 삭제]를 가로로 꽉 차게 배치
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

    # --- 목록 관리 버튼 ---
    st.write("")
    if st.button("🧹 전체 목록 삭제", use_container_width=True):
        st.session_state['list'] = []
        save_data([])
        st.rerun()

st.divider()

# --- AI 요리 추천 섹션 ---
st.subheader("👨‍🍳 제미나이 레시피")
if st.button("🍳 선택한 재료로 요리 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.error("재료를 선택해주세요!")
    else:
        with st.spinner('레시피를 생각하고 있어요...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 자세히 알려줘."
                
                # 안정적인 gemini-2.5-flash 모델 사용
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=prompt
                )
                
                st.success("맛있는 추천이 도착했습니다!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")