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
# 2. 앱 화면 및 스타일 구성 (새로운 안정형 UI)
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🍳")

# 리스트 아이템을 위한 최소한의 안전한 CSS
st.markdown("""
    <style>
    /* 리스트 항목을 감싸는 카드 스타일 */
    .item-container {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 5px 10px;
        margin-bottom: 8px;
        border: 1px solid #eee;
    }
    
    /* 모바일 가로 유지 (2열 구조는 매우 안정적입니다) */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 10px !important;
    }
    
    /* 체크박스 글자(이름) 크기 조절 */
    .stCheckbox label p {
        font-size: 16px !important;
        font-weight: 500 !important;
        margin-top: 2px !important;
    }

    /* 삭제 버튼(쓰레기통) 스타일 - 다른 버튼에 영향 없음 */
    button[key*="del_"] {
        background: transparent !important;
        border: none !important;
        font-size: 18px !important;
        padding: 0px !important;
        color: #ff4b4b !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.caption("v1.1.4 - 체크박스 일체형 안정화 버전")
st.title("👨‍👩‍👦‍👦 아들둘집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 1. 물품 추가 (세 줄 배치 유지) ---
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

# --- 2. 장바구니 목록 (안정적인 가로 2단 정렬) ---
st.subheader("🛒 목록")
selected_ingredients = []

if not st.session_state['list']:
    st.info("장바구니가 비어 있습니다.")
else:
    for i, full_item in enumerate(st.session_state['list']):
        user, name = full_item.split(":", 1) if ":" in full_item else ("기본", full_item)
        emoji = FAMILY_EMOJI.get(user, FAMILY_EMOJI["기본"])

        # 카드형 컨테이너 안에 [체크박스(이름포함) | 삭제버튼] 배치
        st.markdown('<div class="item-container">', unsafe_allow_html=True)
        c1, c2 = st.columns([0.85, 0.15])
        
        with c1:
            # 이름 자체를 체크박스의 라벨로 사용 (가장 밀착된 방식)
            is_selected = st.checkbox(f"{emoji} {name}", key=f"check_{i}")
            if is_selected:
                selected_ingredients.append(name)
        
        with c2:
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

# --- 3. AI 요리 추천 ---
st.subheader("👨‍🍳 제미나이 추천")
if st.button("🍳 선택한 재료로 레시피 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.warning("목록에서 재료를 체크한 후 눌러주세요!")
    else:
        with st.spinner('아들들이 좋아할 메뉴 추천 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 알려줘."
                response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                st.success("추천 레시피 도착!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류: {str(e)}")