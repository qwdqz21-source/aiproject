import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="붓꽃 품종 예측 앱", page_icon="🌸", layout="centered"
)

st.title("🌸 붓꽃(Iris) 품종 예측 머신러닝 앱")
st.write(
    "사용자가 입력한 **꽃잎 길이**와 **꽃잎 너비**를 바탕으로 가장 널리 쓰이는 **KNN(K-Nearest Neighbors) 알고리즘**을 통해 붓꽃의 품종을 예측합니다."
)


# 데이터 로드 및 모델 학습 (캐싱 활용)
@st.cache_resource
def load_data_and_model():
  # 한글 인코딩 고려
  try:
    df = pd.read_csv("Iris.csv", encoding="cp949")
  except:
    df = pd.read_csv("Iris.csv", encoding="utf-8")

  # 학습에 사용할 특성(꽃잎 길이, 꽃잎 너비)과 타겟(품종) 분리
  X = df[["꽃잎 길이", "꽃잎 너비"]]
  y = df["품종"]

  # KNN 모델 학습 (가장 많이 쓰이는 k=5 설정)
  model = KNeighborsClassifier(n_neighbors=5)
  model.fit(X, y)

  return df, model, X, y


df, model, X, y = load_data_and_model()

# 2. 입력 범위 안내 및 사용자 입력 받기
min_length, max_length = float(X["꽃잎 길이"].min()), float(
    X["꽃잎 길이"].max()
)
min_width, max_width = float(X["꽃잎 너비"].min()), float(X["꽃잎 너비"].max())

st.sidebar.header("🌿 입력 변수 설정")
st.sidebar.markdown(f"**- 꽃잎 길이 범위:** `{min_length} cm ~ {max_length} cm`")
st.sidebar.markdown(f"**- 꽃잎 너비 범위:** `{min_width} cm ~ {max_width} cm`")

input_length = st.sidebar.slider(
    "꽃잎 길이 (Petal Length, cm)",
    min_value=min_length,
    max_value=max_length,
    value=float(X["꽃잎 길이"].mean()),
    step=0.1,
)

input_width = st.sidebar.slider(
    "꽃잎 너비 (Petal Width, cm)",
    min_value=min_width,
    max_value=max_width,
    value=float(X["꽃잎 너비"].mean()),
    step=0.1,
)

# 3. 예측 수행
user_input = np.array([[input_length, input_width]])
prediction = model.predict(user_input)[0]
probabilities = model.predict_proba(user_input)[0]

st.subheader("📊 예측 결과")
st.success(f"입력하신 조건의 붓꽃 품종은 **[{prediction}]**으로 예측됩니다!")

# 확률 바 표시
prob_df = pd.DataFrame(
    {"품종": model.classes_, "확률": probabilities}
).set_index("품종")
st.write("품종별 예측 확률:")
st.bar_chart(prob_df)

# 4. 시각화 (가로축: 꽃잎 길이, 세로축: 꽃잎 너비, 사용자 입력: 초록색 별)
st.subheader("📈 품종별 분포 및 사용자 입력 시각화")
st.write(
    "그래프에서 **초록색 별표(*)** 위치가 사용자님의 입력값이며, 주변 데이터 분포를 통해 왜 해당 품종으로 분류되었는지 확인할 수 있습니다."
)

fig, ax = plt.subplots(figsize=(8, 6))

# 품종별 색상 지정
colors = {
    "Iris-setosa": "#ff9999",
    "Iris-versicolor": "#66b3ff",
    "Iris-virginica": "#99ff99",
}

for species, color in colors.items():
  subset = df[df["품종"] == species]
  ax.scatter(
      subset["꽃잎 길이"],
      subset["꽃잎 너비"],
      c=color,
      label=species,
      alpha=0.7,
      edgecolors="k",
      s=50,
  )

# 사용자 입력값을 초록색 별로 표시
ax.scatter(
    input_length,
    input_width,
    c="green",
    marker="*",
    s=300,
    label="사용자 입력",
    edgecolors="black",
    zorder=5,
)

ax.set_xlabel("Petal Length (꽃잎 길이, cm)")
ax.set_ylabel("Petal Width (꽃잎 너비, cm)")
ax.set_title("Iris Petal Length vs Width & User Input")
ax.legend()
ax.grid(True, linestyle="--", alpha=0.5)

st.pyplot(fig)
