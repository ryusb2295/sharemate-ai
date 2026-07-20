import streamlit as st
import pandas as pd
from PIL import Image
from datetime import date
import os
import json
import base64
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
import streamlit.components.v1 as components

from database import (
    init_db,
    get_chores,
    add_chore,
    update_chore_status,
    delete_chore,
    get_shopping_items,
    add_shopping_item,
    update_shopping_status,
    delete_shopping_item,
    get_settlements,
    add_settlement,
    update_settlement_status,
    delete_settlement,
    get_houses_by_user,
    get_house_by_invite_code,
    create_house,
    join_house,
    count_house_members,
    get_house_members,
    get_house_by_id
)

# -----------------------------
# OpenAI 설정
# -----------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# -----------------------------
# Streamlit 기본 설정
# -----------------------------
st.set_page_config(
    page_title="RoomSync",
    page_icon="🏠",
    layout="wide"
)

# -----------------------------
# DB 초기화
# -----------------------------
init_db()

# -----------------------------
# 커스텀 스타일 (앱 내 Light/Dark 토글 대응)
# -----------------------------
current_theme = st.context.theme.type

if current_theme == "dark":
    theme_vars = """
    :root {
        --rs-bg: #241620;
        --rs-sidebar-bg: #3A2233;
        --rs-primary: #FF8FA3;
        --rs-primary-dark: #FFB3C1;
        --rs-text: #FCEAF0;
        --rs-card-bg: #2E1B29;
        --rs-yellow-bg: #4A3B1E;
        --rs-yellow-border: #FFD23F;
        --rs-yellow-text: #FFD23F;
    }
    """
else:
    theme_vars = """
    :root {
        --rs-bg: #FFF6F2;
        --rs-sidebar-bg: #FFD9E3;
        --rs-primary: #FF6F91;
        --rs-primary-dark: #E85577;
        --rs-text: #3A2E39;
        --rs-card-bg: #FFFFFF;
        --rs-yellow-bg: #FFE8A3;
        --rs-yellow-border: #FFD23F;
        --rs-yellow-text: #7A5A00;
    }
    """

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Poppins:wght@400;500;600&display=swap');

{theme_vars}

html, body, [class*="css"] {{
    font-family: 'Poppins', sans-serif;
    color: var(--rs-text);
}}

.stApp {{
    background: var(--rs-bg);
}}

h1, h2, h3 {{
    font-family: 'Fredoka', sans-serif !important;
    color: var(--rs-primary) !important;
    font-weight: 600 !important;
}}

h1 {{
    letter-spacing: -0.5px;
}}

section[data-testid="stSidebar"] {{
    background: var(--rs-sidebar-bg);
    border-right: 3px solid var(--rs-primary);
}}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    color: var(--rs-text) !important;
}}

section[data-testid="stSidebar"] code {{
    background: var(--rs-yellow-border);
    color: #3A2E39;
    padding: 2px 8px;
    border-radius: 8px;
    font-weight: 600;
}}

.stButton > button {{
    border-radius: 999px;
    border: 2px solid var(--rs-primary);
    background: var(--rs-bg);
    color: var(--rs-primary);
    font-family: 'Fredoka', sans-serif;
    font-weight: 500;
    padding: 0.5rem 1.2rem;
    transition: all 0.15s ease;
}}

.stButton > button:hover {{
    background: var(--rs-primary);
    color: #FFFFFF;
    border-color: var(--rs-primary);
    transform: translateY(-1px);
}}

.stButton > button[kind="primary"] {{
    background: var(--rs-primary);
    color: #FFFFFF;
    border: 2px solid var(--rs-primary);
    box-shadow: 0 3px 0 var(--rs-primary-dark);
}}

.stButton > button[kind="primary"]:hover {{
    background: var(--rs-primary-dark);
}}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 18px !important;
    border: 2px solid var(--rs-sidebar-bg) !important;
    background: var(--rs-card-bg);
    box-shadow: 0 4px 12px rgba(255, 111, 145, 0.08);
}}

hr {{
    border-top: 2px dashed var(--rs-sidebar-bg);
}}

div[data-testid="stMetric"] {{
    background: var(--rs-card-bg);
    border: 2px solid var(--rs-sidebar-bg);
    border-radius: 16px;
    padding: 12px 16px;
}}

div[data-testid="stMetricValue"] {{
    color: var(--rs-primary);
    font-family: 'Fredoka', sans-serif;
}}

div[data-testid="stDataFrame"] {{
    border-radius: 12px;
    overflow: hidden;
    border: 2px solid var(--rs-sidebar-bg);
}}

.sidebar-info-card {{
    background: var(--rs-card-bg);
    border: 2px solid var(--rs-primary);
    border-radius: 14px;
    padding: 10px 14px;
    margin-bottom: 10px;
}}

.sidebar-info-card .info-label {{
    font-family: 'Fredoka', sans-serif;
    font-size: 11px;
    font-weight: 600;
    color: var(--rs-primary);
    letter-spacing: 1px;
    margin-bottom: 2px;
}}

.sidebar-info-card .info-value {{
    font-family: 'Poppins', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: var(--rs-text);
}}

.invite-card {{
    background: var(--rs-yellow-bg);
    border-color: var(--rs-yellow-border);
}}

.invite-code-value {{
    letter-spacing: 2px;
    color: var(--rs-yellow-text);
}}

section[data-testid="stSidebar"] div[data-testid="stRadio"] label {{
    font-family: 'Fredoka', sans-serif;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] > label {{
    padding: 12px 14px;
    margin-bottom: 4px;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 600;
    width: 100%;
    transition: background 0.15s ease, transform 0.1s ease;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
    background: color-mix(in srgb, var(--rs-primary) 20%, transparent);
    transform: translateX(2px);
}}

section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {{
    transform: scale(1.25);
}}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 예비용 Mockup 영수증 데이터 (OpenAI Vision API 호출 전 테스트용)
# -----------------------------
def get_mock_receipt_data():
    return {
        "store_name": "이마트 동대구점",
        "items": [
            {"name": "서울우유 1L", "price": 3.20},
            {"name": "플레인 요거트 400g", "price": 4.50},
            {"name": "신라면 5입", "price": 4.80}
        ],
        "total": 12.50
    }

# -----------------------------
# Session State
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

if "current_house" not in st.session_state:
    st.session_state["current_house"] = None

if "current_house_id" not in st.session_state:
    st.session_state["current_house_id"] = None

if "menu" not in st.session_state:          
    st.session_state["menu"] = "Dashboard"  

# -----------------------------
# 로그인 페이지
# -----------------------------
def show_login_page():
    st.title("🏠 RoomSync")
    st.write("OpenAI Vision 기반 쉐어하우스 공동생활 관리 플랫폼")

    st.divider()

    st.subheader("로그인")

    email = st.text_input("이메일", placeholder="example@email.com")
    password = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        email = email.strip()
        password = password.strip()

        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if email == "" or password == "":
            st.error("이메일과 비밀번호를 입력해주세요.")

        elif not re.match(email_pattern, email):
            st.error("이메일 형식에 맞게 입력해주세요. 예: example@email.com")

        elif len(password) < 4:
            st.error("비밀번호는 최소 4자 이상 입력해주세요.")

        else:
            user_name = email.split("@")[0]

            st.session_state["logged_in"] = True
            st.session_state["current_user"] = user_name
            st.rerun()

    st.caption("현재는 MVP 테스트용 로그인입니다.")


# -----------------------------
# 하우스 선택 페이지
# -----------------------------
def show_house_select_page():
    st.title("🏠 내 쉐어하우스")
    st.write(f"{st.session_state['current_user']}님, 참여할 쉐어하우스를 선택하세요.")

    user_name = st.session_state["current_user"]
    houses = get_houses_by_user(user_name)

    st.divider()

    st.subheader("참여 중인 하우스")

    if len(houses) == 0:
        st.info("참여 중인 하우스가 없습니다.")
    else:
        for house in houses:
            member_count = count_house_members(house["id"])

            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 2, 2])

                with col1:
                    st.write(f"### {house['name']}")
                    st.write(f"지역: {house['location']}")
                    st.write(f"초대코드: `{house['invite_code']}`")

                with col2:
                    st.metric("멤버", f"{member_count}명")

                with col3:
                    if st.button("입장하기", key=f"enter_{house['id']}"):
                        st.session_state["current_house"] = house["name"]
                        st.session_state["current_house_id"] = house["id"]
                        st.rerun()

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("새 하우스 만들기")

        new_house_name = st.text_input("하우스 이름", placeholder="예: Brisbane Share House")
        new_house_location = st.text_input("지역", placeholder="예: Sydney")

        if st.button("하우스 만들기"):
            if new_house_name.strip() == "":
                st.error("하우스 이름을 입력해주세요.")

            elif len(new_house_name.strip()) < 3:
                st.error("하우스 이름은 3자 이상 입력해주세요.")

            else:
                invite_code = new_house_name.upper().replace(" ", "")[:5] + "123"

                try:
                    create_house(
                        name=new_house_name,
                        location=new_house_location if new_house_location else "Unknown",
                        invite_code=invite_code,
                        created_by=user_name
                    )

                    st.success(f"{new_house_name} 하우스가 생성되었습니다.")
                    st.rerun()

                except Exception:
                    st.error("이미 존재하는 초대코드입니다. 하우스 이름을 조금 다르게 입력해주세요.")

    with right:
        st.subheader("초대코드로 참여하기")

        invite_code_input = st.text_input("초대코드 입력", placeholder="예: SUNNY123")

        if st.button("초대코드로 참여"):
            invite_code_input = invite_code_input.strip().upper()

            if invite_code_input == "":
                st.error("초대코드를 입력해주세요.")
            else:
                matched_house = get_house_by_invite_code(invite_code_input)

                if matched_house:
                    joined = join_house(matched_house["id"], user_name)

                    if joined:
                        st.success(f"{matched_house['name']}에 참여했습니다.")
                    else:
                        st.info("이미 참여 중인 하우스입니다.")

                    st.rerun()
                else:
                    st.error("일치하는 초대코드가 없습니다.")

    st.divider()

    if st.button("로그아웃"):
        st.session_state["logged_in"] = False
        st.session_state["current_user"] = None
        st.session_state["current_house"] = None
        st.session_state["current_house_id"] = None
        st.rerun()


# -----------------------------
# 로그인 / 하우스 진입 처리
# -----------------------------
if not st.session_state["logged_in"]:
    show_login_page()
    st.stop()

if st.session_state["current_house"] is None:
    show_house_select_page()
    st.stop()


# -----------------------------
# 하우스 멤버 불러오기
# -----------------------------
house_members = get_house_members(st.session_state["current_house_id"])
roommates = [member["user_name"] for member in house_members]

if len(roommates) == 0:
    roommates = [st.session_state["current_user"]]



def extract_json_from_text(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group(0))

    raise ValueError("Gemini 응답에서 JSON을 찾을 수 없습니다.")


# -----------------------------
# 영수증 AI 분석 함수
# -----------------------------
def analyze_receipt_with_gemini(uploaded_file):
    if client is None:
        raise ValueError(".env 파일에 GEMINI_API_KEY가 없습니다.")

    # Streamlit 업로드 파일을 PIL Image 객체로 변환
    image = Image.open(uploaded_file)

    prompt = """
You are an OCR assistant for receipts.

Analyze the uploaded receipt image and extract:
- store name
- purchased items
- item prices
- total amount

Rules:
1. Return ONLY valid JSON.
2. Do not include markdown code blocks like ```json.
3. Do not include explanations.
4. If a discount appears, include it as an item with a negative price.
5. Use numbers only for price and total.
6. If the store name is unclear, use "Unknown Store".
7. The sum of items should be close to the total if possible.

Format:
{
  "store_name": "",
  "items": [
    {
      "name": "",
      "price": 0.00
    }
  ],
  "total": 0.00
}
"""

    
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=[image, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json", 
            temperature=0.0
        )
    )

    result_text = response.text
    return extract_json_from_text(result_text)


# -----------------------------
# Sidebar
# -----------------------------
current_house_info = get_house_by_id(st.session_state["current_house_id"])  


st.sidebar.title("🏠 RoomSync")

st.sidebar.markdown(f"""
<div class="sidebar-info-card">
    <div class="info-label">HOUSE</div>
    <div class="info-value">{st.session_state['current_house']}</div>
</div>
<div class="sidebar-info-card">
    <div class="info-label">USER</div>
    <div class="info-value">{st.session_state['current_user']}</div>
</div>
""", unsafe_allow_html=True)

if current_house_info:
    st.sidebar.markdown(f"""
    <div class="sidebar-info-card invite-card">
        <div class="info-label">INVITE CODE</div>
        <div class="info-value invite-code-value">{current_house_info['invite_code']}</div>
    </div>
    """, unsafe_allow_html=True)

if st.sidebar.button("하우스 변경"):
    st.session_state["current_house"] = None
    st.session_state["current_house_id"] = None

    if "receipt_data" in st.session_state:
        del st.session_state["receipt_data"]

    st.rerun()

if st.sidebar.button("로그아웃"):
    st.session_state["logged_in"] = False
    st.session_state["current_user"] = None
    st.session_state["current_house"] = None
    st.session_state["current_house_id"] = None

    if "receipt_data" in st.session_state:
        del st.session_state["receipt_data"]

    st.rerun()

menu_items = ["Dashboard", "Receipt Split", "Settlements", "Chores", "Shopping List"]

sidebar_menu = st.sidebar.radio(
    "메뉴",
    menu_items,
    index=menu_items.index(st.session_state["menu"])
)

if sidebar_menu != st.session_state["menu"]:
    st.session_state["menu"] = sidebar_menu
    st.rerun()


# -----------------------------
# Top Navigation
# -----------------------------
nav_cols = st.columns(len(menu_items))

for col, item in zip(nav_cols, menu_items):
    with col:
        is_selected = st.session_state["menu"] == item
        if st.button(
            item,
            key=f"nav_{item}",
            use_container_width=True,
            type="primary" if is_selected else "secondary"
        ):
            st.session_state["menu"] = item
            st.rerun()

menu = st.session_state["menu"]

st.divider()

# -----------------------------
# Dashboard
# -----------------------------
if menu == "Dashboard":
    st.title(f"🏠 {st.session_state['current_house']} Dashboard")
    st.write("OpenAI Vision 기반 쉐어하우스 공동생활 관리 플랫폼")

    house_id = st.session_state["current_house_id"]

    chores = get_chores(house_id)
    shopping_items = get_shopping_items(house_id)
    settlements = get_settlements(house_id)

    pending_settlement_total = sum(
        item["amount"] for item in settlements
        if item["status"] == "대기"
    )

    pending_chores = len([
        item for item in chores
        if item["status"] == "진행 전"
    ])

    need_buy_items = len([
        item for item in shopping_items
        if item["status"] == "구매 필요"
    ])

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        member_count = count_house_members(house_id)
        st.metric("하우스 멤버", f"{member_count}명")

    with col2:
        st.metric("정산 대기", f"${pending_settlement_total:.2f}")

    with col3:
        st.metric("남은 Chore", f"{pending_chores}개")

    with col4:
        st.metric("구매 필요 물품", f"{need_buy_items}개")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("이번 주 Chore")

        if chores:
            chore_df = pd.DataFrame(chores)
            chore_df = chore_df.rename(columns={
                "title": "할 일",
                "assigned_to": "담당자",
                "due_date": "날짜",
                "status": "상태"
            })

            st.dataframe(
                chore_df[["할 일", "담당자", "날짜", "상태"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("등록된 Chore가 없습니다.")

    with right:
        st.subheader("공동 장바구니")

        if shopping_items:
            shopping_df = pd.DataFrame(shopping_items)
            shopping_df = shopping_df.rename(columns={
                "item_name": "물품",
                "added_by": "추가한 사람",
                "status": "상태"
            })

            st.dataframe(
                shopping_df[["물품", "추가한 사람", "상태"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("등록된 장바구니 항목이 없습니다.")

    st.divider()

    st.subheader("최근 정산 내역")

    if settlements:
        settlement_df = pd.DataFrame(settlements)
        settlement_df = settlement_df.rename(columns={
            "content": "내용",
            "debtor": "돈 내야 하는 사람",
            "creditor": "돈 받을 사람",
            "amount": "금액",
            "status": "상태"
        })

        settlement_df["금액"] = settlement_df["금액"].apply(lambda x: f"${x:.2f}")

        st.dataframe(
            settlement_df[["내용", "돈 내야 하는 사람", "돈 받을 사람", "금액", "상태"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("정산 내역이 없습니다.")


# -----------------------------
# Receipt Split
# -----------------------------
elif menu == "Receipt Split":
    st.title("🧾 Receipt Split")
    st.write("영수증 이미지를 업로드하면 AI가 품목과 금액을 추출하고 1/N 정산을 생성합니다.")

    house_id = st.session_state["current_house_id"]

    # 💡 [신규 연동 1] 현재 하우스의 '구매 필요' 장바구니 항목 불러오기
    all_shopping_items = get_shopping_items(house_id)
    needed_shopping_items = [item for item in all_shopping_items if item["status"] == "구매 필요"]

    if needed_shopping_items:
        with st.expander("🛒 현재 구매 필요한 장바구니 목록 (정산 생성 시 자동 구매 완료 처리됩니다)", expanded=True):
            items_str = ", ".join([f"**{item['item_name']}** ({item['added_by']})" for item in needed_shopping_items])
            st.markdown(f"💡 **살 것들:** {items_str}")

    st.divider()

    st.subheader("1. 영수증 이미지 업로드")

    uploaded_file = st.file_uploader(
        "영수증 이미지를 업로드하세요",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)

        st.image(
            image,
            caption="업로드한 영수증",
            use_container_width=True
        )

        if st.button("AI로 영수증 분석하기"):
                    try:
                        if "receipt_data" in st.session_state:
                            del st.session_state["receipt_data"]

                        with st.spinner("Gemini Vision으로 영수증을 분석하는 중입니다..."):
                            st.session_state["receipt_data"] = analyze_receipt_with_gemini(uploaded_file)

                        st.success("AI 분석 완료!")

                    except Exception as e:
                        st.error(f"API 호출 오류: {e}")
                        st.warning("테스트용 Mock 분석 결과로 대체합니다.")

                        st.session_state["receipt_data"] = get_mock_receipt_data()

    else:
        st.info("JPG, JPEG, PNG 형식의 영수증 이미지를 선택해주세요.")

    if "receipt_data" in st.session_state:
        receipt_data = st.session_state["receipt_data"]

        st.divider()
        st.subheader("2. AI 분석 결과")

        store_name = receipt_data.get("store_name", "Unknown Store")
        items = receipt_data.get("items", [])
        total = float(receipt_data.get("total", 0.0))

        st.write(f"매장명: {store_name}")
        st.write(f"영수증 총액: ${total:.2f}")

        df = pd.DataFrame(items)

        if df.empty:
            st.error("분석된 품목이 없습니다. 다른 영수증 이미지를 업로드해보세요.")
            st.stop()

        if "name" not in df.columns:
            df["name"] = "Unknown Item"

        if "price" not in df.columns:
            df["price"] = 0.0

        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
        df["is_shared"] = True

        edited_df = st.data_editor(
            df,
            column_config={
                "name": "품목명",
                "price": st.column_config.NumberColumn("금액", format="$%.2f"),
                "is_shared": st.column_config.CheckboxColumn("공용 여부")
            },
            use_container_width=True,
            hide_index=True,
            key="receipt_items_editor"
        )

        shared_total = edited_df[edited_df["is_shared"] == True]["price"].sum()

        st.metric("공용 품목 합계", f"${shared_total:.2f}")

        st.divider()
        st.subheader("3. 1/N 정산")

        payer = st.selectbox("결제한 사람", roommates)

        selected_members = st.multiselect(
            "정산 대상 선택",
            roommates,
            default=roommates
        )

        if len(selected_members) > 0:
            share_amount_preview = shared_total / len(selected_members)

            st.info(
                f"공용 품목 합계 ${shared_total:.2f} ÷ "
                f"정산 대상 {len(selected_members)}명 = "
                f"1인 부담금 ${share_amount_preview:.2f}"
            )

        if st.button("정산 생성하기"):
            if len(selected_members) == 0:
                st.error("정산 대상이 최소 1명 이상 필요합니다.")
            else:
                share_amount = shared_total / len(selected_members)

                settlement_rows = []

                for member in selected_members:
                    if member != payer:
                        settlement_rows.append({
                            "content": f"{store_name} 영수증",
                            "debtor": member,
                            "creditor": payer,
                            "amount": round(share_amount, 2),
                            "status": "대기"
                        })

                if settlement_rows:
                    for row in settlement_rows:
                        add_settlement(
                            row["content"],
                            row["debtor"],
                            row["creditor"],
                            row["amount"],
                            st.session_state["current_house_id"]
                        )

                    # 💡 [신규 연동 2] 영수증 품목 중 장바구니에 있던 물품 자동 '구매 완료' 처리
                    receipt_item_names = [str(name).lower().strip() for name in edited_df["name"].tolist()]
                    auto_completed_items = []

                    for s_item in needed_shopping_items:
                        s_name = s_item["item_name"].lower().strip()
                        # 영수증 품목 이름에 장바구니 키워드가 포함되어 있으면 연동 처리
                        if any(s_name in r_name or r_name in s_name for r_name in receipt_item_names):
                            update_shopping_status(s_item["id"], "구매 완료")
                            auto_completed_items.append(s_item["item_name"])

                    settlement_df = pd.DataFrame(settlement_rows)
                    settlement_df = settlement_df.rename(columns={
                        "content": "내용",
                        "debtor": "돈 내야 하는 사람",
                        "creditor": "돈 받을 사람",
                        "amount": "금액",
                        "status": "상태"
                    })

                    st.subheader("정산 결과")
                    st.dataframe(
                        settlement_df[["내용", "돈 내야 하는 사람", "돈 받을 사람", "금액", "상태"]],
                        use_container_width=True,
                        hide_index=True
                    )

                    st.success("정산 생성 완료. DB와 Dashboard에 반영되었습니다.")

                    if auto_completed_items:
                        st.info(f"🛒 장바구니 연동: **{', '.join(auto_completed_items)}** 항목이 자동으로 '구매 완료' 처리되었습니다!")

                else:
                    st.info("결제자만 정산 대상에 포함되어 있어 받을 금액이 없습니다.")

# -----------------------------
# Settlements
# -----------------------------
elif menu == "Settlements":
    st.title("💸 Settlements")
    st.write("룸메이트 간 정산 내역을 확인하고 결제 완료 처리합니다.")

    st.divider()

    settlements = get_settlements(st.session_state["current_house_id"])

    if len(settlements) == 0:
        st.info("정산 내역이 없습니다.")
    else:
        pending_total = sum(
            item["amount"] for item in settlements
            if item["status"] == "대기"
        )

        paid_total = sum(
            item["amount"] for item in settlements
            if item["status"] == "완료"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("전체 정산 건수", f"{len(settlements)}건")

        with col2:
            st.metric("정산 대기 금액", f"${pending_total:.2f}")

        with col3:
            st.metric("완료 금액", f"${paid_total:.2f}")

        st.divider()

        st.subheader("정산 내역")

        for settlement in settlements:
            with st.container(border=True):
                col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 2])

                with col1:
                    st.write(f"{settlement['content']}")

                with col2:
                    st.write(f"내야 할 사람: {settlement['debtor']}")

                with col3:
                    st.write(f"받을 사람: {settlement['creditor']}")

                with col4:
                    st.write(f"${settlement['amount']:.2f}")
                    st.write(f"상태: {settlement['status']}")

                with col5:
                    if settlement["status"] == "대기":
                        if st.button("결제 완료", key=f"paid_settlement_{settlement['id']}"):
                            update_settlement_status(settlement["id"], "완료")
                            st.rerun()
                    else:
                        if st.button("대기로 변경", key=f"pending_settlement_{settlement['id']}"):
                            update_settlement_status(settlement["id"], "대기")
                            st.rerun()

                with col6:
                    if st.button("삭제", key=f"delete_settlement_{settlement['id']}"):
                        delete_settlement(settlement["id"])
                        st.rerun()


# -----------------------------
# Chores
# -----------------------------
elif menu == "Chores":
    st.title("🧹 Chores")
    st.write("쉐어하우스 청소 당번을 관리합니다.")

    st.divider()

    st.subheader("할 일 추가")

    col1, col2, col3 = st.columns(3)

    with col1:
        chore_title = st.text_input("할 일 이름", placeholder="예: 화장실 청소")

    with col2:
        assigned_to = st.selectbox("담당자", roommates)

    with col3:
        due_date = st.date_input("마감일", value=date.today())

    if st.button("할 일 추가하기"):
        if chore_title.strip() == "":
            st.error("할 일 이름을 입력해주세요.")
        else:
            add_chore(
                chore_title,
                assigned_to,
                str(due_date),
                st.session_state["current_house_id"]
            )
            st.success(f"{assigned_to} 담당으로 '{chore_title}' 할 일이 추가되었습니다.")
            st.rerun()

    st.divider()

    st.subheader("이번 주 Chore")

    chores = get_chores(st.session_state["current_house_id"])

    if len(chores) == 0:
        st.info("등록된 할 일이 없습니다.")
    else:
        for chore in chores:
            with st.container(border=True):
                col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 2])

                with col1:
                    st.write(f"{chore['title']}")

                with col2:
                    st.write(chore["assigned_to"])

                with col3:
                    st.write(chore["due_date"])

                with col4:
                    st.write(chore["status"])

                with col5:
                    if chore["status"] == "진행 전":
                        if st.button("완료", key=f"complete_chore_{chore['id']}"):
                            update_chore_status(chore["id"], "완료")
                            st.rerun()
                    else:
                        if st.button("되돌리기", key=f"undo_chore_{chore['id']}"):
                            update_chore_status(chore["id"], "진행 전")
                            st.rerun()

                with col6:
                    if st.button("삭제", key=f"delete_chore_{chore['id']}"):
                        delete_chore(chore["id"])
                        st.rerun()


# -----------------------------
# Shopping List
# -----------------------------
elif menu == "Shopping List":
    st.title("🛒 Shopping List")
    st.write("공용 생필품 장바구니를 관리합니다.")

    st.divider()

    st.subheader("물품 추가")

    col1, col2 = st.columns(2)

    with col1:
        item_name = st.text_input("물품명", placeholder="예: 우유, 휴지, 세제")

    with col2:
        added_by = st.selectbox("추가한 사람", roommates)

    if st.button("장바구니에 추가"):
        if item_name.strip() == "":
            st.error("물품명을 입력해주세요.")
        else:
            add_shopping_item(
                item_name,
                added_by,
                st.session_state["current_house_id"]
            )
            st.success(f"'{item_name}' 항목이 공동 장바구니에 추가되었습니다.")
            st.rerun()

    st.divider()

    st.subheader("공동 장바구니")

    shopping_items = get_shopping_items(st.session_state["current_house_id"])

    if len(shopping_items) == 0:
        st.info("등록된 장바구니 항목이 없습니다.")
    else:
        for item in shopping_items:
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])

                with col1:
                    st.write(f"{item['item_name']}")

                with col2:
                    st.write(item["added_by"])

                with col3:
                    st.write(item["status"])

                with col4:
                    if item["status"] == "구매 필요":
                        if st.button("구매 완료", key=f"buy_item_{item['id']}"):
                            update_shopping_status(item["id"], "구매 완료")
                            st.rerun()
                    else:
                        if st.button("다시 필요", key=f"need_item_{item['id']}"):
                            update_shopping_status(item["id"], "구매 필요")
                            st.rerun()

                with col5:
                    if st.button("삭제", key=f"delete_item_{item['id']}"):
                        delete_shopping_item(item["id"])
                        st.rerun()