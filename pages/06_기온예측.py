import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# 한글 폰트 깨짐 방지 (시스템 환경에 맞춰 설정)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="기온 예측 및 선형회귀 분석", layout="wide")

st.title("🌡️ 월별 평균기온 분석 및 선형회귀 예측 대시보드")
st.markdown(
    "사용자가 선택한 월의 과거 평균기온 데이터를 시각화하고, **선형회귀(Linear Regression)** 알고리즘을 통해 미래 기온을 예측합니다."
)

# 파일 업로드 또는 기본 데이터 로드 안내
st.sidebar.header("1. 데이터 및 옵션 설정")
uploaded_file = st.sidebar.file_uploader(
    "temperature.csv 파일을 업로드하세요", type=["csv"]
)


@st.cache_data
def load_data(file):
  df = pd.read_csv(file)
  return df


# 샘플 데이터 혹은 업로드된 데이터 처리
if uploaded_file is not None:
  df = load_data(uploaded_file)
else:
  st.sidebar.info(
      "📁 `temperature.csv` 파일이 업로드되지 않아, 시연용 샘플 데이터를"
      " 사용합니다."
  )
  # 테스트용 가상 데이터 생성 코드 (실제 사용 시 temperature.csv 업로드 필요)
  np.random.seed(42)
  years = np.repeat(np.arange(2000, 2026), 12)
  months = np.tile(np.arange(1, 13), 26)
  # 기온 트렌드 (지구온난화 경향 반영 + 노이즈)
  temps = (
      15
      + 10 * np.sin(2 * np.pi * months / 12)
      + (years - 2000) * 0.05
      + np.random.normal(0, 1, len(years))
  )
  df = pd.DataFrame({"연도": years, "월": months, "평균기온": temps})

# 데이터 컬럼 이름 확인 및 정제 (일반적인 '연도', '월', '평균기온' 컬럼 가정)
# 사용자의 CSV 구조에 따라 컬럼명을 수정해야 할 수 있습니다.
expected_cols = ["연도", "월", "평균기온"]
if not all(col in df.columns for col in expected_cols):
  st.error(
      "CSV 파일의 컬럼명은 반드시 **'연도'**, **'월'**, **'평균기온'**을"
      " 포함해야 합니다."
  )
  st.stop()

# 사이드바 사용자 입력
selected_month = st.sidebar.selectbox("조회할 월(Month) 선택", list(range(1, 13)), format_func=lambda x: f"{x}월")
target_year = st.sidebar.number_input(
    "예측할 연도 (Target Year)",
    min_value=2026,
    max_value=2100,
    value=2030,
    step=1,
)

# 데이터 필터링
filtered_df = df[df["월"] == selected_month].sort_values("연도")

if filtered_df.empty:
  st.warning(f"선택한 {selected_month}월에 해당하는 데이터가 없습니다.")
  st.stop()

X = filtered_df["연도"].values
y = filtered_df["평균기온"].values

# 선형회귀 알고리즘 수동 구현 (원리 시각화를 위해 최소제곱법 활용)
# y = wx + b
n = len(X)
mean_x = np.mean(X)
mean_y = np.mean(Y := y)

# 가중치(기울기 w)와 편향(절편 b) 계산
numerator = np.sum((X - mean_x) * (y - mean_y))
denominator = np.sum((X - mean_x) ** 2)
w = numerator / denominator
b = mean_y - w * mean_x

# 예측값 계산
y_pred_line = w * X + b
predicted_temp = w * target_year + b

# 메인 화면 레이아웃
col1, col2 = st.columns([2, 1])

with col1:
  st.subheader(f"📊 연도별 {selected_month}월 평균기온 추이 및 선형회귀 모델")

  # 그래프 시각화
  fig, ax = plt.subplots(figsize=(10, 6))

  # 1. 실제 데이터 산점도 (핫핑크 포인트)
  ax.scatter(
      X,
      y,
      color="#FF1493",
      s=80,
      zorder=5,
      label=f"실제 {selected_month}월 평균기온",
  )

  # 2. 선형회귀 학습 직선 (스카이 블루 라인)
  ax.plot(
      X,
      y_pred_line,
      color="#00BFFF",
      linewidth=3,
      label=f"선형회귀 예측선 (y = {w:.4f}x + {b:.2f})",
  )

  # 3. 예측 연도 포인트 표시
  ax.scatter(
      [target_year],
      [predicted_temp],
      color="red",
      s=120,
      marker="*",
      zorder=6,
      label=f"목표 예측 ({target_year}년): {predicted_temp:.2f}°C",
  )
  ax.vlines(
      x=target_year,
      ymin=min(y.min(), predicted_temp) - 2,
      ymax=predicted_temp,
      colors="red",
      linestyles="dashed",
      alpha=0.7,
  )

  ax.set_xlabel("연도 (Year)", fontsize=12)
  ax.set_ylabel("평균기온 (°C)", fontsize=12)
  ax.set_title(
      f"Historical Data & Linear Regression Trend ({selected_month}월)",
      fontsize=14,
  )
  ax.legend(loc="upper left")
  ax.grid(True, linestyle="--", alpha=0.5)

  st.pyplot(fig)

with col2:
  st.subheader("🎯 기온 예측 결과")
  st.metric(
      label=f"📌 {target_year}년 {selected_month}월 예상 평균기온",
      value=f"{predicted_temp:.2f} °C",
  )

  st.markdown("---")
  st.markdown("### 📐 회귀 모델 파라미터")
  st.write(- **기울기 (w):** f"`{w:.4f}` (연간 기온 변화율)")
  st.write(- **절편 (b):** f"`{b:.2f}`")
  st.info(
      "💡 그래프 위의 **스카이 블루 직선**은 과거 데이터의 오차 제곱합을"
      " 최소화하여 도출된 최적의 트렌드 라인입니다."
  )

st.markdown("---")

# 5. 선형회귀 알고리즘 설명 섹션
st.subheader("📘 선형회귀(Linear Regression) 알고리즘 작동 원리")
st.markdown("""
선형회귀는 독립 변수($X$, 연도)와 종속 변수($Y$, 평균기온) 사이의 **선형 상관관계**를 모델링하는 가장 기본적인 예측 알고리즘입니다.

1. **가상 직선의 설정 ($y = wx + b$):**
   * 알고리즘은 데이터 점들 사이에 임의의 직선을 긋습니다. 여기서 $w$는 직선의 기울기(연도별 기온 상승/하강 속도), $b$는 절편을 의미합니다.
2. **오차(Loss) 최소화 (최소제곱법, Ordinary Least Squares):**
   * 실제 기온 데이터(점)와 직선 사이의 거리(오차)를 계산한 뒤, 이 **오차들의 제곱 합이 최소**가 되는 최적의 $w$와 $b$를 수학적 공식이나 경사하강법으로 찾아냅니다.
3. **미래 예측:**
   * 학습이 완료된 직선 식에 사용자가 입력한 미래의 연도($X = \text{target\_year}$)를 대입하여 미래의 기온($Y$) 값을 도출합니다.
""")
