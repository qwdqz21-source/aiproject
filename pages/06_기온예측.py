import os
from matplotlib import font_manager, rc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# OS 환경에 맞춰 한글 폰트 설정
try:
  if os.name == "posix":  # Linux (Streamlit Cloud 환경)
    # 나눔고딕 등 리눅스 환경의 대표적인 한글 폰트 확인
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    if os.path.exists(font_path):
      font_name = font_manager.FontProperties(fname=font_path).get_name()
      rc("font", family=font_name)
    else:
      # 시스템에 설치된 나눔 폰트 자동 탐색
      font_files = font_manager.findSystemFonts(fontpaths=["/usr/share/fonts"])
      nanum_files = [f for f in font_files if "Nanum" in f]
      if nanum_files:
        font_name = font_manager.FontProperties(fname=nanum_files[0]).get_name()
        rc("font", family=font_name)
      else:
        plt.rcParams["font.family"] = "DejaVu Sans"
  else:  # Windows
    rc("font", family="Malgun Gothic")
except Exception:
  pass

plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지

# 스트림릿 페이지 설정
st.set_page_config(
    page_title="월별 평균기온 분석 및 선형회귀 예측", layout="wide"
)

st.title("🌡️ 월별 평균기온 분석 및 선형회귀 예측 대시보드")
st.markdown(
    "사용자가 선택한 월의 과거 평균기온 데이터를 시각화하고, **선형회귀(Linear"
    " Regression)** 알고리즘을 통해 미래 기온을 예측합니다."
)

# 사이드바 설정
st.sidebar.header("1. 데이터 및 옵션 설정")
uploaded_file = st.sidebar.file_uploader(
    "temperature.csv 파일을 업로드하세요", type=["csv"]
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
      + np.random.normal(0, 1, len(years))
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

X = filtered_df["연도"].values
y = filtered_df["평균기온"].values

# 선형회귀 알고리즘 계산 (최소제곱법: y = wx + b)
mean_x = np.mean(X)
mean_y = np.mean(y)

numerator = np.sum((X - mean_x) * (y - mean_y))
denominator = np.sum((X - mean_x) ** 2)
w = numerator / denominator
b = mean_y - w * mean_x

# 예측선 및 목표 연도 기온 계산
y_pred_line = w * X + b
predicted_temp = w * target_year + b

# 미래 예측 구간 연장선 (과거 마지막 연도 ~ 목표 연도)
future_X = np.array([X[-1], target_year])
future_y = w * future_X + b

# 메인 화면 레이아웃
col1, col2 = st.columns([2, 1])

with col1:
  st.subheader(f"📊 연도별 {selected_month}월 평균기온 추이 및 선형회귀 모델")

  fig, ax = plt.subplots(figsize=(10, 6))

  # 1. 실제 데이터 산점도 (핫핑크)
  ax.scatter(
      X,
      y,
      color="#FF1493",
      s=70,
      zorder=5,
      label=f"실제 {selected_month}월 평균기온",
  )

  # 2. 과거 데이터 학습 직선 (스카이 블루 실선)
  ax.plot(
      X,
      y_pred_line,
      color="#00BFFF",
      linewidth=3,
      label=f"선형회귀 학습선 (y = {w:.4f}x + {b:.2f})",
  )

  # 3. 미래 예측 연장선 (스카이 블루 점선)
  ax.plot(
      future_X,
      future_y,
      color="#00BFFF",
      linewidth=2,
      linestyle="--",
      label="미래 예측 연장선",
  )

  # 4. 잔차(오차) 시각화 - 알고리즘 작동 원리 표현
  for xi, yi, ypi in zip(X, y, y_pred_line):
    ax.plot([xi, xi], [yi, ypi], color="gray", linestyle=":", alpha=0.5)

  # 5. 예측 연도 포인트 표시
  ax.scatter(
      [target_year],
      [predicted_temp],
      color="red",
      s=150,
      marker="*",
      zorder=6,
      label=f"목표 예측 ({target_year}년): {predicted_temp:.2f}°C",
  )

  ax.set_xlabel("연도 (Year)", fontsize=12)
  ax.set_ylabel("평균기온 (°C)", fontsize=12)
  ax.set_title(
      f"연도별 {selected_month}월 평균기온 및 선형회귀 예측 그래프", fontsize=14
  )
  ax.legend(loc="upper left")
  ax.grid(True, linestyle="--", alpha=0.4)

  st.pyplot(fig)

with col2:
  st.subheader("🎯 기온 예측 결과")
  st.metric(
      label=f"📌 {target_year}년 {selected_month}월 예상 평균기온",
      value=f"{predicted_temp:.2f} °C",
  )

  st.markdown("---")
  st.markdown("### 📐 회귀 모델 파라미터")
  st.write(f"- **기울기 (w):** `{w:.4f}` (연간 기온 변화율)")
  st.write(f"- **절편 (b):** `{b:.2f}`")
  st.info(
      "💡 그래프의 **회색 점선**은 실제 기온과 예측선 사이의 오차(잔차)를"
      " 나타냅니다. 선형회귀는 이 오차들의 제곱합이 가장 작아지는 위치에"
      " **스카이 블루 직선**을 긋습니다."
  )

st.markdown("---")

# 5. 선형회귀 알고리즘 설명 섹션
st.subheader("📘 선형회귀(Linear Regression) 알고리즘 작동 원리")
st.markdown("""
선형회귀는 독립 변수($X$, 연도)와 종속 변수($Y$, 평균기온) 사이의 **선형 상관관계**를 찾아 직선 방정식($y = wx + b$)으로 모델링하는 예측 알고리즘입니다.

1. **추세선 설정 ($y = wx + b$):**
   * 과거 데이터 점들의 전반적인 흐름을 가장 잘 대변하는 하나의 직선을 찾습니다. 여기서 $w$는 **기울기**(연도당 평균 기온 변화량), $b$는 **절편**을 의미합니다.
2. **오차(잔차) 최소화 (최소제곱법):**
   * 그래프에서 각 데이터 점(핫핑크)과 직선(스카이 블루) 사이의 세로 거리인 **회색 점선(오차)**을 계산합니다.
   * 모든 데이터에 대해 이 **오차의 제곱 합이 최소**가 되도록 수학적으로 최적의 기울기($w$)와 절편($b$)을 도출합니다.
3. **미래 기온 예측:**
   * 도출된 직선 방정식을 미래 구간(파란색 점선)까지 연장한 뒤, 사용자가 입력한 예측 연도($X$)를 대입하여 예상 평균기온($Y$)을 계산합니다.
""")
