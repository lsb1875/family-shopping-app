import streamlit as st
import os
from google import genai

# ==========================================
# 1. 설정 및 데이터 관리
# ==========================================
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
# 2. 앱 화면 구성
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🍳")
st.title("👨‍👩‍👦‍👦 우리집 장보기 리스트")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 섹션 (가로 배치) ---
with st.expander("➕ 필요한 물품을 입력하세요", expanded=True):
    # 모바일에서도 한 줄에 잘 보이도록 간격 조정
    col_who, col_what, col_btn = st.columns([1, 1.5, 0.8])
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

# --- 장바구니 목록 (한 줄 정렬) ---
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
        cols = st.columns([0.15, 0.65, 0.2])
        
        is_selected = cols[0].checkbox(f"sel_{i}", key=f"check_{i}", label_visibility="collapsed")
        if is_selected:
            selected_ingredients.append(name)
        
        # 이름 클릭 시 체크박스와 상관없이 볼 수 있도록 강조
        cols[1].markdown(f"{emoji} {name}")
        
        if cols[2].button("🗑️", key=f"del_{i}"):
            st.session_state['list'].pop(i)
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# --- AI 요리 추천 ---
if st.button("👨‍🍳 제미나이의 레시피 제안", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.error("재료를 선택해주세요!")
    else:
        with st.spinner('아들들이 좋아할 레시피 찾는 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 알려줘."
                response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                st.success("레시피가 도착했습니다!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")