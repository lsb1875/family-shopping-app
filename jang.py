import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from google import genai
import streamlit.components.v1 as components

# ==========================================
# 1. 설정 및 구글 시트 연결 (데이터 보존)
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# [연동] 구글 시트 API 연결 (Service Account 방식)
conn = st.connection("gsheets", type=GSheetsConnection)

SENDER_EMAIL = "lsb1875@gmail.com"  
RECEIVER_EMAIL = "lsb1875@gmail.com" 
GMAIL_PW = st.secrets.get("GMAIL_APP_PASSWORD", st.secrets.get("우리집장보기", ""))

FAMILY_EMOJI = {"아빠": "👨", "엄마": "👩", "큰아들": "👦", "작은아들": "👶", "기본": "🛒"}

# 데이터 불러오기 (구글 시트)
def load_data():
    try:
        df = conn.read(ttl="5s")
        if df is not None and not df.empty:
            return df['items'].dropna().tolist()
        return []
    except:
        return []

# 데이터 저장 (구글 시트)
def save_data(data_list):
    try:
        df = pd.DataFrame({"items": data_list})
        conn.update(data=df)
        st.cache_data.clear() # 즉시 반영을 위한 캐시 삭제
    except Exception as e:
        st.error(f"저장 실패: {e}")

def send_email_notification(who, item):
    if not GMAIL_PW: return 
    subject = f"🛒 [장바구니] {who}님이 '{item}'을 추가했습니다!"
    body = f"누가: {who}\n물품: {item}\n시간: {datetime.now().strftime('%m/%d %H:%M')}\n\n아빠! 장보실 때 잊지 말고 챙겨주세요! 👦👶"
    msg = MIMEText(body); msg['Subject'] = subject; msg['From'] = SENDER_EMAIL; msg['To'] = RECEIVER_EMAIL
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, GMAIL_PW)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    except: pass

# ==========================================
# 2. UI 스타일 및 모바일 최적화 레이아웃
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🛒")

# 홈 화면 아이콘 설정
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
    /* 한 줄 레이아웃 고정 */
    [data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; align-items: center !important; gap: 5px !important; }
    .item-container { background-color: #ffffff; border-radius: 12px; padding: 4px 8px; margin-bottom: 6px; border: 1px solid #eef0f2; }
    /* 체크박스 영역 넓게, 삭제 버튼 영역 좁게 */
    [data-testid="column"]:nth-child(1) { flex: 9 !important; min-width: 0px !important; }
    [data-testid="column"]:nth-child(2) { flex: 1 !important; min-width: 35px !important; text-align: right !important; }
    .stCheckbox label p { font-size: 16px !important; font-weight: 500 !important; }
    button[key*="del_"] { background: transparent !important; border: none !important; padding: 0px !important; font-size: 18px !important; color: #ff4b4b !important; }
    </style>
    """, unsafe_allow_html=True)

st.caption("우리집 장보기 v1.4.0 (GS-API)")
st.title("👨‍👩‍👦‍👦 우리집 장바구니")

# 데이터 로드
shopping_list = load_data()

# --- 3. 물품 추가 ---
with st.container(border=True):
    st.markdown("##### ➕ 물품 추가")
    who = st.selectbox("누가 필요나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 살까요?", placeholder="재료 입력...", key="input_new_item")
    if st.button("장바구니에 담기", use_container_width=True, key="add_btn"):
        if new_item:
            shopping_list.append(f"{who}:{new_item}")
            save_data(shopping_list)
            send_email_notification(who, new_item)
            st.toast(f"✅ {new_item} 저장 완료!")
            st.rerun()

st.divider()

# --- 4. 장바구니 목록 (초밀착 한 줄 레이아웃) ---
st.subheader("🛒장보기 리스트")
selected_ingredients = []

if not shopping_list:
    st.info("장바구니가 비어 있습니다.")
else:
    for i, full_item in enumerate(shopping_list):
        user, name = full_item.split(":", 1) if ":" in full_item else ("기본", full_item)
        emoji = FAMILY_EMOJI.get(user, "🛒")
        
        st.markdown('<div class="item-container">', unsafe_allow_html=True)
        c1, c2 = st.columns([0.88, 0.12])
        with c1:
            is_selected = st.checkbox(f"{emoji} {name}", key=f"check_{i}")
            if is_selected: selected_ingredients.append(name)
        with c2:
            if st.button("🗑️", key=f"del_{i}"):
                shopping_list.pop(i)
                save_data(shopping_list)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    
    # --- 삭제 확인 로직 (모바일 최적화 위아래 배치) ---
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False

    if not st.session_state.confirm_delete:
        if st.button("🧹 전체 목록 삭제", use_container_width=True, key="clear_all_btn"):
            st.session_state.confirm_delete = True
            st.rerun()
    else:
        with st.container(border=True):
            st.warning("⚠️ 모든 목록을 지울까요?")
            if st.button("🔥 네, 전체 삭제합니다", use_container_width=True, type="primary", key="confirm_yes"):
                save_data([]) # 시트 비우기
                st.session_state.confirm_delete = False
                st.rerun()
            if st.button("❌ 아니오, 취소합니다", use_container_width=True, key="confirm_no"):
                st.session_state.confirm_delete = False
                st.rerun()

st.divider()

# --- 5. AI 요리 추천 (계절/날씨 인식) ---
st.subheader("👨‍🍳 제미나이 추천 요리")
if st.button("🍳 레시피 추천 받기", type="primary", use_container_width=True, key="recipe_btn"):
    if not selected_ingredients:
        st.warning("재료를 체크한 후 눌러주세요!")
    else:
        with st.spinner('메뉴 추천 중...'):
            try:
                now = datetime.now()
                month = now.month
                today_str = now.strftime("%Y년 %m월 %d일")
                
                if 3 <= month <= 5: season = "봄"
                elif 6 <= month <= 8: season = "여름"
                elif 9 <= month <= 11: season = "가을"
                else: season = "겨울"

                ingredients_str = ", ".join(selected_ingredients)
                prompt = f"오늘은 {today_str}이고 한국은 {season}이야. 재료({ingredients_str})로 계절과 날씨에 맞는 레시피 추천해줘."
                
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                st.success(f"오늘({today_str}, {season}) 추천 레시피!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류: {str(e)}")