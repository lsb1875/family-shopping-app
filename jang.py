import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from google import genai
import streamlit.components.v1 as components

# ==========================================
# 1. 설정 및 데이터 관리
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)
DATA_FILE = "shopping_list.txt"

# --- 이메일 설정 (아빠 Gmail 정보) ---
SENDER_EMAIL = "lsb1875@gmail.com"  # 아빠 Gmail 주소로 수정
RECEIVER_EMAIL = "lsb1875@gmail.com" # 알림 받을 아빠 이메일 주소
GMAIL_PW = st.secrets.get("GMAIL_APP_PASSWORD", "")

FAMILY_EMOJI = {"아빠": "👨", "엄마": "👩", "큰아들": "👦", "작은아들": "👶", "기본": "🛒"}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for item in data:
            f.write(item + "\n")

# 📧 이메일 발송 함수
def send_email_notification(who, item):
    if not GMAIL_PW:
        return 

    subject = f"🛒 [장바구니] {who}님이 '{item}'을 추가했습니다!"
    body = f"누가: {who}\n물품: {item}\n시간: {datetime.now().strftime('%m/%d %H:%M')}\n\n아빠! 장보실 때 잊지 말고 챙겨주세요! 👦👶"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, GMAIL_PW)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    except Exception as e:
        st.error(f"메일 발송 오류: {e}")

# ==========================================
# 2. UI 스타일 및 아이콘 강제 설정
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🛒")

# 홈 화면 아이콘 강제 주입
components.html(f"""
    <script>
        const head = window.parent.document.head;
        const icon_url = "https://emojicdn.elk.sh/🛒?size=192";
        const oldAppleIcon = head.querySelector('link[rel="apple-touch-icon"]');
        if (oldAppleIcon) oldAppleIcon.remove();
        const newAppleIcon = window.parent.document.createElement('link');
        newAppleIcon.rel = 'apple-touch-icon';
        newAppleIcon.href = icon_url;
        head.appendChild(newAppleIcon);
    </script>
    """, height=0)

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

st.caption("우리집 장보기 v1.2.0 ")
st.title("👨‍👩‍👦‍👦 우리집 장보기")

if 'list' not in st.session_state:
    st.session_state['list'] = load_data()

# --- 3. 물품 추가 섹션 ---
with st.container(border=True):
    st.markdown("##### ➕ 물품 추가")
    who = st.selectbox("누가 필요나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 살까요?", placeholder="재료 입력...")
    
    if st.button("장바구니에 담기", use_container_width=True, type="secondary"):
        if new_item:
            st.session_state['list'].append(f"{who}:{new_item}")
            save_data(st.session_state['list'])
            
            # 이메일 발송 로직 추가
            send_email_notification(who, new_item)
            st.toast(f"✅ {new_item} 추가! 아빠에게 메일을 보냈어요.", icon="📧")
            st.rerun()

st.divider()

# --- 4. 장바구니 목록 ---
st.subheader("🛒장보기 리스트")
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

# --- 5. AI 요리 추천 ---
st.subheader("👨‍🍳 제미나이 추천")
if st.button("🍳 레시피 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.warning("재료를 체크한 후 눌러주세요!")
    else:
        with st.spinner(' 메뉴 추천 가져오는 중...'):
            try:
                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"{ingredients_str}를 주재료로 하여 한국의 지금 계절, 날씨를 확인해서 날씨와계절에 어울리고 먹기 좋은 요리와 레시피를 한국어로 알려줘."
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                st.success("추천 레시피 도착!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류: {str(e)}")