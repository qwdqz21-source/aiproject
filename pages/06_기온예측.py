import os
from matplotlib import font_manager, rc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
import streamlit as st

# [한글 폰트 설정]
try:
  if os.name == "posix":  # Linux (Streamlit Cloud 환경)
    font_list = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
    nanum_font = [
        f
        for f in font_list
        if any(name in f for name in ["Nanum", "nanum", "Malgun"])
    ]
    if nanum_font:
      font_path = nanum_font[0]
      font_name = font_manager.FontProperties(fname=font_path).get_name()
      rc("font", family=font_name)
    else:
      plt.rcParams["font.family"] = "sans-serif"
  else:  # Windows
    rc("font", family="Malgun Gothic")
except Exception:
  pass

plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지

# 스트림릿 페이지 설정
st.set_page_config(
    page_title="다양한 회귀 알고리즘 기온 예측 비교", layout="wide"
)

st.title("🌡️ 회귀 알고리즘별 월별 평균기온 예측 비교 대시보드")
st.markdown(
    "사용자가 선택한 **회귀 알고리즘**에 따라 예측 기온과 트렌드 선이"
    " 어떻게 달라지는지 비교하고 확인해 보세요."
)

# 사이드바 설정
st.sidebar.header("1. 데이터 및 모델 설정")
uploaded_file = st.sidebar.file_uploader(
    "temperature.csv 파일을 업로드하세요", type=["csv"]
)

# 알고리즘 선택 옵션
model_choice = st.sidebar.selectbox(
    "사용할 회귀 알고리즘 선택",
    [
        "선형회귀 (Linear Regression)",
        "릿지 회귀 (Ridge Regression)",
        "랜덤 포레스트 회귀 (Random Forest)",
    ],
)


@st.cache_data
def load_data(file_source):
  return pd.read_csv(file_source)


# 데이터 로드 우선순위: 1) 사용자 업로드 -> 2) 저장소의 temperature.csv -> 3) 샘플 데이터
if uploaded_file is not None:
  df = load_data(uploaded_file)
elif os.path.exists("temperature.csv"):
  df = load_data("temperature.csv")
  st.sidebar.success("📁 저장소의 `temperature.csv` 파일을 자동으로 불러왔습니다.")
else:
  st.sidebar.info(
      "📁 `temperature.csv` 파일이 없어 시연용 샘플 데이터를 사용합니다."
  )
  np.random.seed(42)
  years = np.repeat(np.arange(2000, 2026), 12)
  months = np.tile(np.arange(1, 13), 26)
  temps = (
      15
      + 10 * np.sin(2 * np.pi * months / 12)
      + (years - 2000) * 0.05
      + np.random.normal(0, 1.2, len(years))
  )
  df = pd.DataFrame({"연도": years, "월": months, "평균기온": temps})

# 필수 컬럼 확인
expected_cols = ["연도", "월", "평균기온"]
if not all(col in df.columns for col in expected_cols):
  st.error(
      "CSV 파일의 컬럼명은 반드시 **'연도'**, **'월'**, **'평균기온'**을"
      " 포함해야 합니다."
  )
  st.write("현재 파일의 컬럼명:", list(df.columns))
  st.stop()

# 사용자 입력 (월 및 예측 연도)
selected_month = st.sidebar.selectbox(
    "조회할 월(Month) 선택", list(range(1, 13)), format_func=lambda x: f"{x}월"
)
target_year = st.sidebar.number_input(
    "예측할 연도 (Target Year)",
    min_value=2026,
    max_value=2100,
    value=2030,
    step=1,
)

# 선택한 월 데이터 필터링
filtered_df = df[df["월"] == selected_month].sort_values("연도")

if filtered_df.empty:
  st.warning(f"선택한 {selected_month}월에 해당하는 데이터가 없습니다.")
  st.stop()

# 머신러닝 학습용 데이터 분리 (X: 2차원 형태 필요)
X = filtered_df[["연도"]].values
y = filtered_df["평균기온"].values

# 선택한 알고리즘에 따른 모델 학습 및 예측
if model_choice == "선형회귀 (Linear Regression)":
  model = LinearRegression()
  model.fit(X, y)
  predicted_temp = model.predict(np.array([[target_year]]))[0]
  # 시각화를 위한 전체 연도 예측선 생성
  all_years = np.arange(X.min(), max(X.max(), target_year) + 1).reshape(-1, 1)
  y_pred_line = model.predict(all_years)

elif model_choice == "릿지 회귀 (Ridge Regression)":
  model = Ridge(alpha=1.0)
  model.fit(X, y)
  predicted_temp = model.predict(np.array([[target_year]]))[0]
  all_years = np.arange(X.min(), max(X.max(), target_year) + 1).reshape(-1, 1)
  y_pred_line = model.predict(all_years)

else:  # 랜덤 포레스트 회귀
  model = RandomForestRegressor(n_estimators=100, random_state=42)
  model.fit(X, y)
  predicted_temp = model.predict(np.array([[target_year]]))[0]
  all_years = np.arange(X.min(), max(X.max(), target_year) + 1).reshape(-1, 1)
  y_pred_line = model.predict(all_years)

# 메인 화면 레이아웃
col1, col2 = st.columns([2, 1])

with col1:
  st.subheader(
      f"📊 연도별 {selected_month}월 평균기온 추이 및 [{model_choice}] 모델"
  )

  fig, ax = plt.subplots(figsize=(10, 6))

  # 1. 실제 데이터 산점도
  ax.scatter(
      X,
      y,
      color="#FF1493",
      s=70,
      zorder=5,
      label=f"실제 {selected_month}월 평균기온",
  )

  # 2. 알고리즘 예측 트렌드 선
  ax.plot(
      all_years,
      y_pred_line,
      color="#00BFFF",
      linewidth=3,
      label=f"{model_choice} 예측선",
  )

  # 3. 목표 연도 예측 포인트 표시
  ax.scatter(
      [target_year],
      [predicted_temp],
      color="red",
      s=160,
      marker="*",
      zorder=6,
      label=f"목표 예측 ({target_year}년): {predicted_temp:.2f}°C",
  )

  ax.set_xlabel("연도 (Year)", fontsize=12)
  ax.set_ylabel("평균기온 (°C)", fontsize=12)
  ax.set_title(f"Algorithm Prediction: {model_choice}", fontsize=14)
  ax.legend(loc="upper left")
  ax.grid(True, linestyle="--", alpha=0.4)

  st.pyplot(fig)

with col2:
  st.subheader("🎯 예측 결과 요약")
  st.metric(
      label=f"📌 {target_year}년 {selected_month}월 예상 평균기온",
      value=f"{predicted_temp:.2f} °C",
  )

  st.markdown("---")
  st.markdown("### ⚙️ 선택한 알고리즘 특징")

  if "Linear Regression" in model_choice:
    st.info(
        "**선형회귀:** 가장 단순하고 직관적인 직선 모델입니다. 데이터 전체의"
        " 전반적인 장기 추세(상승/하강)를 일직선 형태로 파악하는 데"
        " 적합합니다."
    )
  elif "Ridge" in model_choice:
    st.info(
        "**릿지 회귀:** 선형회귀에 규제(Regularization)를 더한 모델입니다."
        " 이상치나 급격한 데이터 변동에 과하게 흔들리지 않고 안정적인"
        " 직선 트렌드를 유지합니다."
    )
  else:
    st.info(
        "**랜덤 포레스트:** 여러 개의 의사결정 나무를 결합한 앙상블"
        " 알고리즘입니다. 직선뿐만 아니라 데이터의 미세한 비선형적 굴곡과"
        " 복잡한 패턴을 유연하게 반영할 수 있습니다."
    )

st.markdown("---")

# 알고리즘 비교 설명 섹션
st.subheader("📘 알고리즘별 작동 방식 및 차이점 비교")
st.markdown("""
사이드바에서 알고리즘을 변경해가며 **그래프의 형태와 예측값($°C$)이 어떻게 달라지는지** 직접 비교해 보세요.

1. **선형회귀 (Linear Regression)**
   * **원리:** 오차 제곱합이 최소가 되는 단 하나의 완벽한 직선($y = wx + b$)을 찾습니다.
   * **특징:** 구조가 단순하지만, 최근 급격한 기온 변화나 비선형적 흐름을 섬세하게 담아내기엔 한계가 있습니다.
2. **릿지 회귀 (Ridge Regression)**
   * **원리:** 기본적으로 선형회귀와 같지만, 계수($w$)가 너무 커지지 않도록 제약(규제)을 줍니다.
   * **특징:** 데이터에 이상치(Outlier)가 많거나 변동성이 심할 때 모델이 너무 민감하게 반응하지 않도록 중심을 잡아줍니다.
3. **랜덤 포레스트 회귀 (Random Forest)**
   * **원리:** 수많은 나무(Decision Tree)들이 각자 학습한 뒤, 그 예측값들을 평균 내어 최종 결과를 도출합니다.
   * **특징:** 직선 형태가 아닌 계단식 혹은 유연한 곡선 형태로 학습되므로, 과거 데이터의 복잡한 등락 패턴을 반영하는 데 유리합니다.
""")
