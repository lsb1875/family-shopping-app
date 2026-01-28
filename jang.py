import streamlit as st
import os
from google import genai

# 1. 설정 및 데이터 관리
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)
DATA_FILE = "shopping_list.txt"

FAMILY_EMOJI = {"아빠": "👨", "엄마": "👩", "큰아들": "👦", "작은아들": "👶", "기본": "🛒"}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_data(items):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for item in items:
            f.write(item + "\n")

# 2. 앱 화면 및 스타일 구성 (초강력 밀착 레이아웃)
st.set_page_config(page_title="우리집 장바구니", page_icon="🍳")

st.markdown("""
    <style>
    /* 리스트 줄 가로 배치 및 요소 사이의 물리적 거리를 0으로 고정 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 0px !important;
    }
    
    /* 체크박스 컬럼: 너비를 20px로 강제 고정 */
    div[data-testid="column"]:nth-child(1) {
        flex: 0 0 20px !important;
        min-width: 20px !important;
    }
    
    /* 이름 컬럼: 음수 마진(-20px)을 주어 체크박스 바로 옆으로 강제 이동 */
    div[data-testid="column"]:nth-child(2) {
        flex: 1 1 auto !important;
        margin-left: -20px !important;
        padding-left: 0px !important;
    }
    
    /* 삭제 버튼 컬럼 */
    div[data-testid="column"]:nth-child(3) {
        flex: 0 0 40px !important;
        text-align: right !important;
    }

    /* 체크박스 위젯 자체의 불필요한 영역 삭제 */
    .stCheckbox { margin-bottom: 0px !important; }
    .stCheckbox label { padding: 0 !important; margin: 0 !important; min-height: 0px !important; }
    div[data-testid="stMarkdownContainer"] { display: none; }
    
    /* 삭제 버튼 투명 스타일 */
    button[key*="del_"] { background: transparent !important; border: none !important; padding: 0 !important; font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

# 버전 정보 표시 (이게 바뀌어야 업데이트된 것입니다)
st.caption("v1.1.2 - 초강력 밀착 업데이트 완료")

st.title("👨‍👩‍👦‍👦 아들둘집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# 물품 추가 (세 줄 배치)
with st.container(border=True):
    st.markdown("##### ➕ 물품 추가")
    who = st.selectbox("누구?", ["아빠", "엄마", "큰아들", "작은아들"], label_visibility="collapsed")
    new_item = st.text_input("무엇을?", placeholder="재료 입력...", label_visibility="collapsed")
    if st.button("추가하기", use_container_width=True):
        if new_item:
            st.session_state['list'].append(f"{who}:{new_item}")
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# 장바구니 목록 (초밀착 가로 정렬)
st.subheader("🛒 목록")
selected_ingredients = []

for i, full_item in enumerate(st.session_state['list']):
    user, name = full_item.split(":", 1) if ":" in full_item else ("기본", full_item)
    emoji = FAMILY_EMOJI.get(user, FAMILY_EMOJI["기본"])

    c1, c2, c3 = st.columns([0.05, 0.85, 0.1])
    with c1:
        is_selected = st.checkbox("", key=f"check_{i}", label_visibility="collapsed")
        if is_selected: selected_ingredients.append(name)
    with c2:
        st.markdown(f"<div style='font-size:16px;'>{emoji} <b>{name}</b></div>", unsafe_allow_html=True)
    with c3:
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state['list'].pop(i)
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# AI 요리 추천
if st.button("🍳 요리 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.warning("재료를 선택해 주세요!")
    else:
        with st.spinner('생각 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 알려줘."
                response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류: {str(e)}")