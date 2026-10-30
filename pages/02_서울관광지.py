import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. Page Configuration
st.set_page_config(
    page_title="서울 주요 관광지 1박 2일 코스 가이드",
    page_icon="🗺️",
    layout="wide"
)

# 2. 관광지 Top 10 데이터 준비
tourist_spots = [
    {"rank": 1, "name": "경복궁", "lat": 37.5796, "lon": 126.9770, "category": "역사/문화", "desc": "조선 왕조의 대표 궁궐"},
    {"rank": 2, "name": "N서울타워", "lat": 37.5512, "lon": 126.9882, "category": "전망대/랜드마크", "desc": "남산 정상에서 서울 전경을 한눈에 감상"},
    {"rank": 3, "name": "명동 쇼핑거리", "lat": 37.5629, "lon": 126.9858, "category": "쇼핑/길거리음식", "desc": "K-뷰티, 쇼핑, 길거리 음식의 중심지"},
    {"rank": 4, "name": "북촌 한옥마을", "lat": 37.5826, "lon": 126.9831, "category": "역사/문화", "desc": "전통 한옥이 잘 보존된 고풍스러운 거리"},
    {"rank": 5, "name": "홍대 거리", "lat": 37.5563, "lon": 126.9230, "category": "문화/버스킹", "desc": "젊음, 버스킹, 예술 문화의 거리"},
    {"rank": 6, "name": "인사동", "lat": 37.5716, "lon": 126.9860, "category": "전통/공예", "desc": "전통 찻집, 공예품, 갤러리가 모인 거리"},
    {"rank": 7, "name": "동대문디자인플라자(DDP)", "lat": 37.5665, "lon": 127.0092, "category": "건축/디자인", "desc": "미래지향적 복합문화공간"},
    {"rank": 8, "name": "롯데월드타워", "lat": 37.5126, "lon": 127.1025, "category": "전망대/쇼핑", "desc": "국내 최고층 초고층 전망대 및 쇼핑몰"},
    {"rank": 9, "name": "광장시장", "lat": 37.5701, "lon": 126.9997, "category": "전통시장/음식", "desc": "빈대떡, 육회, 마약김밥 등 K-푸드의 성지"},
    {"rank": 10, "name": "반포한강공원", "lat": 37.5097, "lon": 127.0001, "category": "자연/휴식", "desc": "달빛무지개분수와 피크닉 명소"}
]

df = pd.DataFrame(tourist_spots)

# 3. 헤더
st.title("🗺️ 서울 Top 10 관광지 1박 2일 완벽 코스")
st.caption("09:00 ~ 19:00 효율적 동선 반영 | 식당 및 숙소 링크 포함")

# 4. 지도 생성 (서울 중심)
m = folium.Map(location=[37.555, 126.985], zoom_start=12, tiles="OpenStreetMap")

for _, row in df.iterrows():
    popup_html = f"""
    <div style="font-family: sans-serif; width: 180px;">
        <h4 style="margin: 0; color: #1976D2;">#{row['rank']} {row['name']}</h4>
        <p style="font-size: 12px; color: #666; margin-top: 4px;">{row['desc']}</p>
    </div>
    """
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=folium.Popup(popup_html, max_width=220),
        tooltip=f"#{row['rank']} {row['name']}",
        icon=folium.Icon(color="red", icon="star", prefix="fa")
    ).add_to(m)

# 5. 지도 및 목록 상단 배치
col_map, col_info = st.columns([2, 1])

with col_map:
    st.subheader("📍 서울 관광지 위치 지도")
    st_folium(m, width="100%", height=480)

with col_info:
    st.subheader("📌 Top 10 관광지 요약")
    for _, row in df.iterrows():
        with st.expander(f"#{row['rank']} {row['name']}"):
            st.write(f"**카테고리:** {row['category']}")
            st.write(f"**설명:** {row['desc']}")

st.markdown("---")

# 6. 지도 아래 1박 2일 일정표 (시간대별 / 식당 / 숙소 포함)
st.header("🗓️ 1박 2일 통합 일정표 (09:00 ~ 19:00)")

# 마크다운 표
schedule_md = """
| 구분 | 시간 | 주요 동선 & 일정 | 아침 식당 | 점심 식당 | 저녁 식당 | 추천 숙소 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1일차** | **09:00 - 11:30** | #1 경복궁 & #4 북촌 한옥마을 | [무교동 북어국집](https://www.google.com/search?q=무교동북어국집) | - | - | - |
| **1일차** | **11:30 - 15:30** | #6 인사동 & #9 광장시장 | - | [토속촌 삼계탕](https://www.google.com/search?q=토속촌삼계탕) | - | - |
| **1일차** | **15:30 - 19:00** | #7 동대문디자인플라자(DDP) & #3 명동 | - | - | [진옥화할매원조닭한마리](https://www.google.com/search?q=진옥화할매원조닭한마리) | [노보텔 앰배서더 동대문](https://www.google.com/travel/search?q=노보텔+앰배서더+서울+동대문) |
| **2일차** | **09:00 - 12:00** | #2 N서울타워 & 남산 산책 | [명동교자 본점](https://www.google.com/search?q=명동교자본점) | - | - | - |
| **2일차** | **12:00 - 15:30** | #5 홍대 거리 문화 투어 | - | [연남토마 본점](https://www.google.com/search?q=연남토마+본점) | - | - |
| **2일차** | **15:30 - 19:00** | #8 롯데월드타워 & #10 반포한강공원 | - | - | [잠실 한강공원 치맥 / 반포 야시장](https://www.google.com/search?q=반포한강공원+맛집) | - |
"""

st.markdown(schedule_md, unsafe_allow_html=True)

st.markdown("### 🏨 숙소 상세 정보")
st.info("""
* **추천 호텔:** [노보텔 앰배서더 서울 동대문 (5성급)](https://www.google.com/travel/search?q=노보텔+앰배서더+서울+동대문)
* **선택 이유:** DDP, 광장시장, 명동 중심가와 가깝고 지하철역(동대문역사문화공원역) 직결 수준이라 1일차 저녁 이동 및 2일차 오전에 최적화된 위치입니다.
""")

st.markdown("---")
st.subheader("📊 전체 데이터 보기")
st.dataframe(df.set_index("rank"), use_container_width=True)
