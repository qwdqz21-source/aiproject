import os
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="월별 기온 분석", page_icon="🌡️", layout="wide"
)

# 한글 폰트 깨짐 방지
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.unicode_minus"] = False


# 데이터 로드 함수 (캐싱 적용)
@st.cache_data
def load_data():
  # pages 폴더의 상위 폴더에 있는 temperature.csv 경로 지정
  current_dir = os.path.dirname(os.path.abspath(__file__))
  file_path = os.path.join(current_dir, "..", "temperature.csv")

  df = pd.read_csv(file_path, encoding="cp949")
  # '일시' 컬럼을 datetime 형식으로 변환 후 연도와 월 추출
  df["연월"] = pd.to_datetime(df["일시"], format="%b-%y")
  df["연도"] = df["연월"].dt.year
  df["월"] = df["연월"].dt.month
  return df


# 데이터 불러오기
try:
  df = load_data()
except Exception as e:
  st.error(
      f"데이터 파일을 불러오는 중 오류가 발생했습니다. 상위 폴더에 'temperature.csv' 파일이"
      f" 있는지 확인하세요. 에러: {e}"
  )
  st.stop()

# 스트림릿 화면 구성
st.title("🌡️ 연도별 월별 기온 분석기")
st.write(
    "원하는 **월(Month)**을 선택하면, 해당 월의 연도별 최고기온 및 최저기온"
    " 변화를 시각화합니다."
)

# 월 선택 셀렉트박스 (1월 ~ 12월)
month_dict = {
    "1월": 1,
    "2월": 2,
    "3월": 3,
    "4월": 4,
    "5월": 5,
    "6월": 6,
    "7월": 7,
    "8월": 8,
    "9월": 9,
    "10월": 10,
    "11월": 11,
    "12월": 12,
}

selected_month_name = st.selectbox(
    "조회할 월을 선택하세요:", list(month_dict.keys())
)
selected_month_num = month_dict[selected_month_name]

# 선택한 월에 해당하는 데이터 필터링
filtered_df = df[df["월"] == selected_month_num].sort_values("연도")

# 그래프 그리기
st.subheader(f"📊 {selected_month_name} 기온 분석 그래프")

fig, ax = plt.subplots(figsize=(10, 5))

# 최고기온 (핫핑크), 최저기온 (하늘색) 그래프 선 연결 및 마커 표시
ax.plot(
    filtered_df["연도"],
    filtered_df["최고기온(℃)"],
    color="hotpink",
    marker="o",
    linewidth=2,
    label="최고기온",
)
ax.plot(
    filtered_df["연도"],
    filtered_df["최저기온(℃)"],
    color="skyblue",
    marker="s",
    linewidth=2,
    label="최저기온",
)

# 그래프 제목 및 축 이름 설정
ax.set_title("월별 기온분석", fontsize=16, fontweight="bold", pad=15)
ax.set_xlabel("연도", fontsize=12)
ax.set_ylabel("온도 (℃)", fontsize=12)

# 범례 표시 및 그리드 추가
ax.legend(loc="upper left", fontsize=11)
ax.grid(True, linestyle="--", alpha=0.6)

# Streamlit에 Matplotlib 그래프 출력
st.pyplot(fig)

# 하단에 데이터 테이블 제공
with st.expander(f"📁 {selected_month_name} 원본 데이터 상세 보기"):
  st.dataframe(
      filtered_df[["연도", "최고기온(℃)", "최저기온(℃)", "평균기온(℃)"]].reset_index(
          drop=True
      )
  )
