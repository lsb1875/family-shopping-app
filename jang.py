import streamlit as st
import streamlit.components.v1 as components
import os
from google import genai
import streamlit.components.v1 as components

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
# 2. 홈 화면 아이콘 "강제" 주입 (가장 강력한 방법)
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🛒")

# 브라우저의 Head 태그를 직접 수정하여 아이콘 설정을 강제로 덮어씌웁니다.
components.html("""
<script>
    const head = window.parent.document.head;
    
    // 1. 기존 스트림릿 기본 앱 설정 삭제
    const oldManifest = head.querySelector('link[rel="manifest"]');
    if (oldManifest) oldManifest.remove();
    
    // 2. 새로운 아이콘 설정 주입
    const iconLink = window.parent.document.createElement('link');
    iconLink.rel = 'apple-touch-icon'; // 아이폰용
    iconLink.href = 'https://emojicdn.elk.sh/🛒?size=192';
    head.appendChild(iconLink);
    
    const favLink = window.parent.document.createElement('link');
    favLink.rel = 'icon'; // 안드로이드/PC용
    favLink.href = 'https://emojicdn.elk.sh/🛒?size=192';
    head.appendChild(favLink);
</script>
""", height=0)

# --- 이하 기존 스타일 및 리스트 코드 ---
st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; align-items: center !important; justify-content: flex-start !important; gap: 0px !important; }
    .item-container { background-color: #ffffff; border-radius: 12px; padding: 6px 10px; margin-bottom: 6px; border: 1px solid #eef0f2; }
    div[data-testid="column"]:nth-child(1) { flex: 0 1 auto !important; min-width: 0px !important; }
    div[data-testid="column"]:nth-child(2) { flex: 0 0 40px !important; min-width: 40px !important; padding-left: 5px !important; }
    .stCheckbox label p { font-size: 16px !important; font-weight: 500 !important; white-space: nowrap !important; }
    button[key*="del_"] { background: transparent !important; border: none !important; font-size: 18px !important; padding: 0px !important; color: #ff4b4b !important; }
    </style>
    """, unsafe_allow_html=True)

st.caption("v1.1.7 - 홈 화면 아이콘 강제 주입 시스템")
st.title("👨‍👩‍👦‍👦 우리집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# ➕ 물품 추가 섹션
with st.container(border=True):
    st.markdown("##### ➕ 물품 추가")
    who = st.selectbox("누가 필요하나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 살까요?", placeholder="재료 입력...")
    if st.button("장바구니에 담기", use_container_width=True, type="secondary"):
        if new_item:
            st.session_state['list'].append(f"{who}:{new_item}")
            save_data(st.session_state['list'])
            st.rerun()

st.divider()

# 🛒 장바구니 목록
st.subheader("🛒 사야할 것들")
selected_ingredients = []

if not st.session_state['list']:
    st.info("장바구니가 비어 있습니다.")
else:
    for i, full_item in enumerate(st.session_state['list']):
        user, name = full_item.split(":", 1) if ":" in full_item else ("기본", full_item)
        emoji = FAMILY_EMOJI.get(user, FAMILY_EMOJI["기본"])
        st.markdown('<div class="item-container">', unsafe_allow_html=True)
        c1, c2 = st.columns([0.85, 0.15])
        with c1:
            is_selected = st.checkbox(f"{emoji} {name}", key=f"check_{i}")
            if is_selected: selected_ingredients.append(name)
        with c2:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state['list'].pop(i)
                save_data(st.session_state['list'])
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("")
    if st.button("🧹 전체 목록 삭제", use_container_width=True):
        st.session_state['list'] = []; save_data([]); st.rerun()

st.divider()

# 👨‍🍳 AI 레시피 추천
if st.button("🍳 선택한 재료로 레시피 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.warning("재료를 체크한 후 눌러주세요!")
    else:
        with st.spinner('메뉴 추천 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 아들 둘을 둔 가족이 먹기 좋은 요리와 레시피를 한국어로 알려줘."
                response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                st.success("레시피 도착!"); st.markdown(response.text)
            except Exception as e:
                st.error(f"오류: {str(e)}")