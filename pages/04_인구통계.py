import os
import re
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 1. 페이지 설정
st.set_page_config(page_title="인구 현황 복합 그래프 분석", layout="wide")
st.title("📊 행정구/성별/연도별 인구수 분석")


# 2. 데이터 불러오기 및 전처리 (상위 폴더의 population.csv 경로 지정)
@st.cache_data
def load_data():
  current_dir = os.path.dirname(os.path.abspath(__file__))
  file_path = os.path.join(current_dir, "..", "population.csv")

  try:
    df = pd.read_csv(file_path, encoding="cp949")
  except Exception:
    try:
      df = pd.read_csv("population.csv", encoding="cp949")
    except Exception:
      df = pd.read_csv("population.csv", encoding="utf-8-sig")

  # 지역명 정제 ('서울특별시 종로구 (1111000000)' -> '서울특별시 종로구')
  df["지역명"] = df["행정구역"].apply(
      lambda x: x.split("(")[0].strip() if isinstance(x, str) else str(x)
  )

  # 쉼표(,) 제거 및 숫자형 변환
  num_cols = [c for c in df.columns if c not in ["행정구역", "지역명"]]
  for col in num_cols:
    df[col] = df[col].astype(str).str.replace(",", "").str.strip()
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

  return df


try:
  df = load_data()
except Exception as e:
  st.error(
      "`population.csv` 파일을 불러오지 못했습니다. 상위 폴더에 파일이"
      f" 있는지 확인해주세요. (오류: {e})"
  )
  st.stop()

# 3. 검색 조건 선택 (사이드바)
st.sidebar.header("⚙️ 검색 조건 선택")

# (1) 행정구 선택
region_list = df["지역명"].unique().tolist()
selected_region = st.sidebar.selectbox("행정구 선택", region_list)

# (2) 성별 선택
gender_options = ["전체(총인구)", "남성", "여성"]
selected_gender = st.sidebar.selectbox("성별 선택", gender_options)

# (3) 연도 선택 (컬럼명에서 4자리 연도 파싱)
years = sorted(list(set(re.findall(r"(\d{4})년", " ".join(df.columns)))))
selected_year = st.sidebar.selectbox("연도 선택", years, index=len(years) - 1)

# 4. 선택 조건별 데이터 추출
age_bins = [
    "0~9세",
    "10~19세",
    "20~29세",
    "30~39세",
    "40~49세",
    "50~59세",
    "60~69세",
    "70~79세",
    "80~89세",
    "90~99세",
    "100세 이상",
]

if selected_gender == "전체(총인구)":
  gender_prefix = f"{selected_year}년_거주자_"
elif selected_gender == "남성":
  gender_prefix = f"{selected_year}년_남_거주자_"
else:
  gender_prefix = f"{selected_year}년_여_거주자_"

row_data = df[df["지역명"] == selected_region]

age_pop_values = []
for age in age_bins:
  col_name = f"{gender_prefix}{age}"
  if col_name in row_data.columns:
    age_pop_values.append(row_data[col_name].values[0])
  else:
    age_pop_values.append(0)

plot_df = pd.DataFrame({"나이(연령대)": age_bins, "인구수": age_pop_values})

# 5. Plotly 복합 그래프 생성 (막대 + 꺾은선)
fig = go.Figure()

# (1) 막대그래프 추가
fig.add_trace(
    go.Bar(
        x=plot_df["나이(연령대)"],
        y=plot_df["인구수"],
        name="인구수 (막대)",
        marker=dict(
            color="rgba(255, 182, 193, 0.6)",  # 은은한 라이트 핑크 (투명도 적용)
            line=dict(color="#FF69B4", width=1.5),
        ),
    )
)

# (2) 꺾은선그래프 추가
fig.add_trace(
    go.Scatter(
        x=plot_df["나이(연령대)"],
        y=plot_df["인구수"],
        mode="lines+markers",
        name="인구수 (꺾은선)",
        line=dict(color="#FF1493", width=4),  # 딥 핫핑크
        marker=dict(size=9, color="#C71585"),
    )
)

fig.update_layout(
    title=f"<b>{selected_region} - {selected_gender} 인구 분포 ({selected_year}년)</b>",
    xaxis=dict(
        title="나이 (10살 단위 연령대)",
        showgrid=True,
        gridcolor="lightgray",
        dtick=1,
    ),
    yaxis=dict(
        title="인구수 (명)",
        showgrid=True,
        gridcolor="lightgray",
        dtick=100000,  # 10만 단위 눈금
        tickformat=",",
    ),
    plot_bgcolor="white",
    hovermode="x unified",
)

# 6. 결과 출력
st.plotly_chart(fig, use_container_width=True)

with st.expander("📊 상세 데이터 보기"):
  st.dataframe(plot_df.T)
