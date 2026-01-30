import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from google import genai
import streamlit.components.v1 as components

# ==========================================
# 1. 설정 및 구글 시트 연결
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# 구글 시트 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 이메일 설정
SENDER_EMAIL = "lsb1875@gmail.com"  
RECEIVER_EMAIL = "lsb1875@gmail.com" 
GMAIL_PW = st.secrets.get("GMAIL_APP_PASSWORD", "") 

FAMILY_EMOJI = {"아빠": "👨", "엄마": "👩", "큰아들": "👦", "작은아들": "👶", "기본": "🛒"}

# 데이터 불러오기 함수 (구글 시트에서)
def load_data():
    try:
        df = conn.read(ttl="10s") # 10초마다 새로고침 가능
        return df['items'].dropna().tolist()
    except:
        return []

# 데이터 저장 함수 (구글 시트 업데이트)
def save_data(data_list):
    df = pd.DataFrame({"items": data_list})
    conn.update(data=df)

def send_email_notification(who, item):
    if not GMAIL_PW: return 
    subject = f"🛒 [장바구니] {who}님이 '{item}'을 추가했습니다!"
    body = f"누가: {who}\n물품: {item}\n시간: {datetime.now().strftime('%m/%d %H:%M')}\n\n아빠! 장보실 때 잊지 말고 챙겨주세요!"
    msg = MIMEText(body); msg['Subject'] = subject; msg['From'] = SENDER_EMAIL; msg['To'] = RECEIVER_EMAIL
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, GMAIL_PW)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    except: pass

# ==========================================
# 2. UI 스타일 및 로직 (기존과 동일하되 데이터 저장만 변경)
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🛒")

# (아이콘 설정 JS 코드는 이전과 동일하게 유지)
components.html(f"""<script>const head = window.parent.document.head; const icon_url = "https://emojicdn.elk.sh/🛒?size=192"; const oldAppleIcon = head.querySelector('link[rel="apple-touch-icon"]'); if (oldAppleIcon) oldAppleIcon.remove(); const newAppleIcon = window.parent.document.createElement('link'); newAppleIcon.rel = 'apple-touch-icon'; newAppleIcon.href = icon_url; head.appendChild(newAppleIcon);</script>""", height=0)

st.markdown("""<style>div[data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; align-items: center !important; justify-content: flex-start !important; gap: 0px !important; } .item-container { background-color: #ffffff; border-radius: 12px; padding: 6px 10px; margin-bottom: 6px; border: 1px solid #eef0f2; } div[data-testid="column"]:nth-child(1) { flex: 0 1 auto !important; } div[data-testid="column"]:nth-child(2) { flex: 0 0 40px !important; padding-left: 5px !important; } .stCheckbox label p { font-size: 16px !important; font-weight: 500 !important; } button[key*="del_"] { background: transparent !important; border: none !important; font-size: 18px !important; color: #ff4b4b !important; }</style>""", unsafe_allow_html=True)

st.title("👨‍👩‍👦‍👦 무적의 장바구니")
st.caption("v1.3.0 - 구글 시트 연동 (데이터 보존 버전)")

# 목록 불러오기
shopping_list = load_data()

# ➕ 물품 추가
with st.container(border=True):
    who = st.selectbox("누가 필요나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 살까요?", placeholder="재료 입력...")
    if st.button("장바구니에 담기", use_container_width=True):
        if new_item:
            shopping_list.append(f"{who}:{new_item}")
            save_data(shopping_list)
            send_email_notification(who, new_item)
            st.toast(f"✅ {new_item} 저장 완료!")
            st.rerun()

st.divider()

# 🛒 목록 표시
selected_ingredients = []
if not shopping_list:
    st.info("장바구니가 비어 있습니다.")
else:
    for i, full_item in enumerate(shopping_list):
        user, name = full_item.split(":", 1) if ":" in full_item else ("기본", full_item)
        emoji = FAMILY_EMOJI.get(user, "🛒")
        st.markdown('<div class="item-container">', unsafe_allow_html=True)
        c1, c2 = st.columns([0.85, 0.15])
        with c1:
            if st.checkbox(f"{emoji} {name}", key=f"check_{i}"):
                selected_ingredients.append(name)
        with c2:
            if st.button("🗑️", key=f"del_{i}"):
                shopping_list.pop(i)
                save_data(shopping_list)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 🧹 전체 삭제 (확인 절차 포함)
if st.button("🧹 전체 비우기"):
    save_data([]) # 빈 데이터로 시트 업데이트
    st.rerun()

# --- 5. AI 요리 추천 ---
st.subheader("👨‍🍳 제미나이 추천")
if st.button("🍳 레시피 추천받기", type="primary", use_container_width=True):
    if not selected_ingredients:
        st.warning("재료를 체크한 후 눌러주세요!")
    else:
        with st.spinner('메뉴 추천 중...'):
            try:
                # 1. 오늘 날짜와 월 정보를 가져옵니다.
                now = datetime.now()
                month = now.month
                today_str = now.strftime("%Y년 %m월 %d일")
                
                # 2. 월별로 계절 텍스트를 정해줍니다.
                if 3 <= month <= 5:
                    season = "봄"
                    weather_desc = "봄에 어울리는 상큼한 요리"
                elif 6 <= month <= 8:
                    season = "여름"
                    weather_desc = "여름에 어울리는 요리"
                elif 9 <= month <= 11:
                    season = "가을"
                    weather_desc = "가을과 어울리는 든든한 요리"
                else:
                    season = "겨울"
                    weather_desc = "추운 겨울에 먹으면 좋을 요리"

                ingredients_str = ", ".join(selected_ingredients)
                
                # 3. AI에게 날짜와 판단된 계절 정보를 함께 전달합니다.
                prompt = f"""
                오늘 날짜는 {today_str}입니다. 한국은 지금 {season}입니다.
                {weather_desc}가 필요한 시기입니다.

                선택된 재료들({ingredients_str})을 주재료로 하여,
                {season} 날씨에 가족들이 
                가장 맛있게 먹을 수 있는 요리와 레시피를 한국어로 알려줘.
                """
                
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                st.success(f"오늘({today_str}, {season})에 딱 맞는 레시피 도착!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류: {str(e)}")