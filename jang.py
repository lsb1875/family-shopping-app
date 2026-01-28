import streamlit as st
import os
from google import genai

# ==========================================
# 1. 설정 및 데이터 관리
# ==========================================

# Streamlit Secrets에서 API 키를 안전하게 가져옵니다.
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

DATA_FILE = "shopping_list.txt"

# 아들 둘 가족 구성원에 맞춘 이모지 설정
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

# CSS를 사용하여 모바일에서 요소들이 한 줄에 바짝 붙도록 강제 조정합니다.
st.markdown("""
    <style>
    /* 체크박스 여백 제거 */
    .stCheckbox { margin-bottom: -15px; }
    /* 삭제 버튼 크기 및 여백 조정 */
    .stButton button { padding: 2px 5px; margin-top: -5px; height: auto; }
    /* 컬럼 내부 요소들을 세로 중앙 정렬 */
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    /* 텍스트 줄바꿈 방지 및 여백 조정 */
    .item-text { white-space: nowrap; margin-top: 5px; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

st.title("👨‍👩‍👦‍👦 우리집 장보기 리스트")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 섹션 ---
with st.expander("➕ 필요한 물품을 입력하세요", expanded=True):
    col_who, col_what, col_btn = st.columns([1, 1.8, 0.8])
    with col_who:
        who = st.selectbox("누구?", ["아빠", "엄마", "큰아들", "작은아들"], label_visibility="collapsed")
    with col_what:
        new_item = st.text_input("재료명", placeholder="재료 입력", label_visibility="collapsed")
    with col_btn:
        if st.button("추가", use_container_width=True):
            if new_item:
                st.session_state['list'].append(f"{who}:{new_item}")
                save_data(st.session_state['list'])
                st.rerun()

st.divider()

# --- 장바구니 목록 (초밀착 가로 정렬) ---
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

        # [체크박스(0.1) | 이름(0.75) | 삭제(0.15)] 비율로 아주 좁게 배치
        cols = st.columns([0.12, 0.73, 0.15])
        
        with cols[0]:
            is_selected = st.checkbox("", key=f"check_{i}", label_visibility="collapsed")
            if is_selected:
                selected_ingredients.append(name)
        
        with cols[1]:
            # HTML을 사용하여 텍스트 위치를 미세 조정
            st.markdown(f"<div class='item-text'>{emoji} {name}</div>", unsafe_allow_html=True)
        
        with cols[2]:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state['list'].pop(i)
                save_data(st.session_state['list'])
                st.rerun()

st.divider()

# --- AI 요리 추천 섹션 ---
if st.button("👨‍🍳 제미나이의 레시피 제안", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.error("재료를 선택해주세요!")
    else:
        with st.spinner('아들들이 좋아할 레시피 찾는 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 알려줘."
                
                # 모델명을 안정적인 'gemini-1.5-flash'로 유지했습니다.
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                
                st.success("레시피가 도착했습니다!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")