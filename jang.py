import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from google import genai

# ==========================================
# 1. 설정 및 연결
# ==========================================
# [수정] 연결 방식을 더 명시적으로 설정합니다.
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # 최신 데이터를 읽어옵니다.
        df = conn.read(ttl=0)
        return df['items'].dropna().tolist() if df is not None else []
    except Exception as e:
        st.error(f"데이터 읽기 실패: {e}")
        return []

def save_data(data_list):
    try:
        df = pd.DataFrame({"items": data_list})
        # [핵심] 이 부분에서 '편집자' 권한이 없으면 에러가 납니다.
        conn.update(data=df)
        st.cache_data.clear()
        return True
    except Exception as e:
        # 어떤 구체적인 권한 문제인지 화면에 표시합니다.
        st.error(f"⚠️ 저장 실패! (공유 설정 확인 필요): {e}")
        return False

# ... (중략: 기존 UI 및 추가 로직 동일) ...

# ➕ 물품 추가 버튼 로직
if st.button("장바구니에 담기", use_container_width=True):
    if new_item:
        current_list = load_data() # 현재 시트 상태 확인
        current_list.append(f"{who}:{new_item}")
        if save_data(current_list):
            st.toast("✅ 구글 시트에 안전하게 저장되었습니다!")
            st.rerun()# ==========================================
# 2. UI 및 로직
# ==========================================
st.set_page_config(page_title="우리집 장바구니", page_icon="🛒")

# (기존 CSS 및 아이콘 JS 코드는 동일하게 유지)
st.markdown("""<style>div[data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; align-items: center !important; gap: 0px !important; } .item-container { background-color: #ffffff; border-radius: 12px; padding: 6px 10px; margin-bottom: 6px; border: 1px solid #eef0f2; } .stCheckbox label p { font-size: 16px !important; font-weight: 500 !important; } button[key*="del_"] { background: transparent !important; border: none !important; font-size: 18px !important; color: #ff4b4b !important; }</style>""", unsafe_allow_html=True)

st.title("👨‍👩‍👦‍👦 무적의 장바구니")
st.caption("v1.3.3 - 오류 진단 모드")

# 데이터 로드
shopping_list = load_data()

with st.container(border=True):
    st.markdown("##### ➕ 물품 추가")
    who = st.selectbox("누가 필요나요?", ["아빠", "엄마", "큰아들", "작은아들"])
    new_item = st.text_input("무엇을 살까요?", placeholder="재료 입력...")
    
    if st.button("장바구니에 담기", use_container_width=True):
        if new_item:
            # 1. 새로운 리스트 만들기
            temp_list = shopping_list.copy()
            temp_list.append(f"{who}:{new_item}")
            
            # 2. 저장 시도 및 성공 시에만 화면 갱신
            if save_data(temp_list):
                st.toast(f"✅ {new_item} 저장 완료!")
                st.rerun()

st.divider()

# (목록 표시 및 삭제 기능 동일)
if not shopping_list:
    st.info("장바구니가 비어 있습니다. (구글 시트 확인 중...)")
else:
    for i, full_item in enumerate(shopping_list):
        user, name = full_item.split(":", 1) if ":" in full_item else ("기본", full_item)
        emoji = FAMILY_EMOJI.get(user, "🛒")
        st.markdown('<div class="item-container">', unsafe_allow_html=True)
        c1, c2 = st.columns([0.85, 0.15])
        with c1:
            st.checkbox(f"{emoji} {name}", key=f"check_{i}")
        with c2:
            if st.button("🗑️", key=f"del_{i}"):
                shopping_list.pop(i)
                if save_data(shopping_list): st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.write("")
if st.button("🧹 전체 비우기", use_container_width=True):
    if save_data([]): st.rerun()

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