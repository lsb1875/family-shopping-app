import streamlit as st
import os
from google import genai

# ==========================================
# 1. 설정 및 데이터 관리
# ==========================================
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

# ==========================================
# 2. 앱 화면 및 스타일 구성 (안전한 밀착 레이아웃)
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🍳")

# 다른 곳은 건드리지 않고, '리스트 영역'만 콕 집어서 수정하는 안전한 CSS
st.markdown("""
    <style>
    /* 리스트 아이템을 감싸는 박스 스타일 */
    .item-box {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 5px 0px;
        border-bottom: 1px solid #eee;
    }
    
    /* 체크박스와 이름을 담는 왼쪽 그룹 */
    .left-group {
        display: flex;
        align-items: center;
        gap: 2px; /* 체크박스와 이름 사이의 간격을 직접 조절 (매우 좁게) */
    }

    /* 스트림릿 기본 컬럼의 자동 줄바꿈 방지 */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    
    /* 삭제 버튼(쓰레기통) 스타일만 별도 지정 */
    button[key*="del_"] {
        border: none !important;
        background: transparent !important;
        padding: 0px !important;
        font-size: 18px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.caption("v1.1.3 - 화면 복구 및 리스트 밀착")
st.title("👨‍👩‍👦‍👦 아들둘집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 1. 물품 추가 (세 줄 배치) ---
with st.container(border=True):
    st.markdown("##### ➕ 물품 추가")
    who = st.selectbox("누가 사나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 사나요?", placeholder="재료 입력...")
    if st.button("장바구니에 담기", use_container_width=True, type="secondary"):
        if new_item:
            st.session_state['list'].append(f"{who}:{new_item}")
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# --- 2. 장바구니 목록 (가로 한 줄 정렬) ---
st.subheader("🛒 목록")
selected_ingredients = []

if not st.session_state['list']:
    st.info("장바구니가 비어 있습니다.")
else:
    for i, full_item in enumerate(st.session_state['list']):
        user, name = full_item.split(":", 1) if ":" in full_item else ("기본", full_item)
        emoji = FAMILY_EMOJI.get(user, FAMILY_EMOJI["기본"])

        # [체크박스 | 이름 | 삭제] 3단 컬럼
        # 비율을 0.15 / 0.7 / 0.15 정도로 주어 이름 영역을 확보
        c1, c2, c3 = st.columns([0.15, 0.7, 0.15])
        
        with c1:
            # 체크박스
            is_selected = st.checkbox("", key=f"check_{i}", label_visibility="collapsed")
            if is_selected:
                selected_ingredients.append(name)
        
        with c2:
            # 이름을 체크박스 쪽으로 바짝 붙여서 출력 (음수 마진 사용)
            st.markdown(f"<div style='margin-left: -15px; font-size: 16px; margin-top: 3px;'>{emoji} {name}</div>", unsafe_allow_html=True)
        
        with c3:
            # 삭제 버튼 (쓰레기통)
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state['list'].pop(i)
                save_data(st.session_state['list'])
                st.rerun()

    st.write("")
    if st.button("🧹 전체 목록 삭제", use_container_width=True):
        st.session_state['list'] = []
        save_data([])
        st.rerun()

st.divider()

# --- 3. AI 요리 추천 ---
st.subheader("👨‍🍳 제미나이 추천")
if st.button("🍳 레시피 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.warning("재료를 선택(체크)해 주세요!")
    else:
        with st.spinner('생각 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 알려줘."
                response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                st.success("추천 레시피!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류: {str(e)}")