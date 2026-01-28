import streamlit as st
import os
from google import genai  # 최신 라이브러리로 변경

# ==========================================
# 1. 설정 및 데이터 관리
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]
# 최신 클라이언트 설정 방식
client = genai.Client(api_key=API_KEY)

DATA_FILE = "shopping_list.txt"

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
st.set_page_config(page_title="스마트 장바구니", page_icon="🍳")
st.title("👨‍👩‍👧‍👦 우리 가족 장보기 리스트")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 물품 추가 ---
with st.expander("➕ 필요한 물품을 입력하세요!", expanded=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        new_item = st.text_input("재료 입력", label_visibility="collapsed")
    with col2:
        if st.button("추가", use_container_width=True):
            if new_item:
                st.session_state['list'].append(new_item)
                save_data(st.session_state['list'])
                st.rerun()

st.divider()

# --- 장바구니 목록 ---
st.subheader("🛒 사야 할 목록")
selected_ingredients = []

if not st.session_state['list']:
    st.info("장바구니가 비어 있습니다.")
else:
    for i, item in enumerate(st.session_state['list']):
        cols = st.columns([0.5, 3, 1])
        # 해결책: 체크박스에 이름을 주고 숨김 처리(label_visibility="collapsed")
        is_selected = cols[0].checkbox(f"select_{item}", key=f"check_{i}", label_visibility="collapsed")
        if is_selected:
            selected_ingredients.append(item)
        
        cols[1].write(item)
        
        if cols[2].button("삭제", key=f"del_{i}"):
            st.session_state['list'].pop(i)
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# --- AI 요리 추천 ---
st.subheader("👨‍🍳 제미나이의 레시피 제안")
if st.button("선택한 재료로 레시피 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.error("재료를 최소 하나 이상 선택해야 합니다!")
    else:
        with st.spinner('레시피를 생성 중입니다...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 한 요리 2~3개와 레시피를 한국어로 알려줘.".encode('utf-8').decode('utf-8')
                
                # 최신 API 호출 방식
                response = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                
                st.success("추천 레시피가 도착했습니다!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류 발생: {e}")