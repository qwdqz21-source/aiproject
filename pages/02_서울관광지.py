import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. 스트림릿 페이지 기본 설정
st.set_page_config(
    page_title="외국인이 선호하는 서울 관광지 Top 10",
    page_icon="🗺️",
    layout="wide"
)

# 2. 서울 주요 관광지 Top 10 데이터 준비
tourist_spots = [
    {"rank": 1, "name": "경복궁 (Gyeongbokgung Palace)", "lat": 37.5796, "lon": 126.9770, "category": "역사/문화", "desc": "조선 왕조의 대표 궁궐이자 전통 한복 체험의 명소"},
    {"rank": 2, "name": "N서울타워 (N Seoul Tower)", "lat": 37.5512, "lon": 126.9882, "category": "전망대/랜드마크", "desc": "남산 정상에서 서울 시내 전경을 한눈에 조망할 수 있는 랜드마크"},
    {"rank": 3, "name": "명동 쇼핑거리 (Myeongdong)", "lat": 37.5629, "lon": 126.9858, "category": "쇼핑/길거리음식", "desc": "K-뷰티, 길거리 음식, 쇼핑의 중심지"},
    {"rank": 4, "name": "북촌한옥마을 (Bukchon Hanok Village)", "lat": 37.5826, "lon": 126.9831, "category": "역사/문화", "desc": "수백 년 된 전통 한옥이 보존되어 있는 거리"},
    {"rank": 5, "name": "홍대 거리 (Hongdae Street)", "lat": 37.5563, "lon": 126.9230, "category": "문화/버스킹", "desc": "젊음과 예술, 버스킹 공연, 밤문화의 중심지"},
    {"rank": 6, "name": "인사동 (Insadong)", "lat": 37.5716, "lon": 126.9860, "category": "전통/공예", "desc": "전통 차, 골동품, 한지 공예 등 한국 전통문화를 느끼는 거리"},
    {"rank": 7, "name": "동대문디자인플라자 (DDP)", "lat": 37.5665, "lon": 127.0092, "category": "건축/디자인", "desc": "미래지향적 건축물과 전시, 밤도깨비 야시장이 열리는 명소"},
    {"rank": 8, "name": "롯데월드 타워 (Lotte World Tower)", "lat": 37.5126, "lon": 127.1025, "category": "전망대/쇼핑", "desc": "한국 최고층 마천루이자 세계적인 규모의 전망대 및 쇼핑몰"},
    {"rank": 9, "name": "광장시장 (Gwangjang Market)", "lat": 37.5701, "lon": 126.9997, "category": "전통시장/음식", "desc": "빈대떡, 마약김밥 등 K-푸드를 맛볼 수 있는 대표 전통시장"},
    {"rank": 10, "name": "한강시민공원 반포지구 (Banpo Hangang Park)", "lat": 37.5097, "lon": 127.0001, "category": "자연/휴식", "desc": "무지개 분수 쇼와 야경, 피크닉과 치맥 문화를 즐기는 명소"}
]

df = pd.DataFrame(tourist_spots)

# 3. 헤더 및 소개글
st.title("🗺️ 외국인이 선호하는 서울 주요 관광지 Top 10")
st.caption("Folium 지도를 기반으로 제작된 스트림릿 웹 애플리케이션입니다.")

# 4. 사이드바 - 카테고리 필터
st.sidebar.header("🔍 검색 및 필터")
categories = ["전체"] + list(df["category"].unique())
selected_category = st.sidebar.selectbox("카테고리 선택", categories)

if selected_category != "전체":
    filtered_df = df[df["category"] == selected_category]
else:
    filtered_df = df

# 5. Folium 지도 객체 생성 (서울 시청 중심)
m = folium.Map(
    location=[37.5665, 126.9780], 
    zoom_start=11, 
    tiles="OpenStreetMap"
)

# 관광지 마커 추가
for _, row in filtered_df.iterrows():
    popup_html = f"""
    <div style="font-family: Arial; width: 220px;">
        <h4 style="margin-bottom: 5px; color: #1E88E5;">#{row['rank']} {row['name']}</h4>
        <p style="font-size: 12px; color: #555; margin-bottom: 5px;"><b>카테고리:</b> {row['category']}</p>
        <p style="font-size: 12px;">{row['desc']}</p>
    </div>
    """
    
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=f"#{row['rank']} {row['name']}",
        icon=folium.Icon(color="red", icon="star", prefix="fa")
    ).add_to(m)

# 6. 화면 레이아웃 분할 (지도 영역 / 목록 영역)
col_map, col_list = st.columns([2, 1])

with col_map:
    st.subheader("📍 관광지 위치 지도")
    # folium 지도를 streamlit에 표시
    st_folium(m, width="100%", height=520)

with col_list:
    st.subheader("📋 관광지 목록")
    for _, row in filtered_df.iterrows():
        with st.expander(f"#{row['rank']} {row['name']}"):
            st.write(f"**카테고리:** {row['category']}")
            st.write(f"**상세설명:** {row['desc']}")

# 7. 하단 전체 데이터 테이블
st.markdown("---")
st.subheader("📊 데이터 상세 보기")
st.dataframe(
    filtered_df[["rank", "name", "category", "desc"]].set_index("rank"),
    use_container_width=True
)
