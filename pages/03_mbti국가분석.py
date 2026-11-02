import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(
    page_title="국가별 MBTI 비율 분석기",
    page_icon="📊",
    layout="wide"
)

# 2. 데이터 로드 (캐싱 적용)
@st.cache_data
def load_data():
    df = pd.read_csv("countriesMBTI_16types.csv")
    mbti_cols = [col for col in df.columns if col != 'Country']
    return df, mbti_cols

try:
    df, mbti_cols = load_data()
except FileNotFoundError:
    st.error("⚠️ 'countriesMBTI_16types.csv' 파일을 찾을 수 없습니다. 앱과 같은 폴더에 업로드해주세요.")
    st.stop()

# 3. 타이틀 및 설명
st.title("🌍 국가별 MBTI 비율 시각화 대시보드")
st.markdown("원하는 국가를 선택하여 16가지 MBTI 유형별 분포 비율을 확인해보세요!")
st.markdown("---")

# 4. 사이드바 - 국가 선택
st.sidebar.header("🔍 조회 설정")
selected_country = st.sidebar.selectbox("국가를 선택하세요:", sorted(df['Country'].unique()))

# 5. 데이터 가공
country_row = df[df['Country'] == selected_country].iloc[0]
mbti_values = country_row[mbti_cols] * 100  # 백분율로 변환

# 데이터프레임으로 정렬 (내림차순)
chart_df = pd.DataFrame({
    'MBTI': mbti_values.index,
    'Percentage': mbti_values.values
}).sort_values(by='Percentage', ascending=False).reset_index(drop=True)

# 6. 색상 매핑 설정 (1등: 빨간색, 나머지: 파란색 그라데이션)
colors = []
for i in range(len(chart_df)):
    if i == 0:
        colors.append('#FF4B4B')  # 1등: 강렬한 빨간색
    else:
        colors.append('#1F77B4')  # 나머지: 기본 파란색 계열 (Plotly가 값에 따라 명도 조절)

chart_df['Color'] = colors

# 7. 메인 화면 레이아웃 (지표 요약 및 그래프)
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader(f"📌 {selected_country}")
    st.metric(label="1위 MBTI", value=chart_df.iloc[0]['MBTI'], delta=f"{chart_df.iloc[0]['Percentage']:.2f}%")
    st.metric(label="최하위 MBTI", value=chart_df.iloc[-1]['MBTI'], delta=f"{chart_df.iloc[-1]['Percentage']:.2f}%", delta_color="inverse")
    
    with st.expander("전체 순위 표 보기"):
        display_df = chart_df[['MBTI', 'Percentage']].copy()
        display_df['Percentage'] = display_df['Percentage'].round(2).astype(str) + '%'
        st.dataframe(display_df, hide_index=True, use_container_width=True)

with col2:
    st.subheader(f"📊 {selected_country}의 MBTI 유형별 비율 (%)")
    
    # Plotly 막대 그래프 생성
    fig = px.bar(
        chart_df,
        x='MBTI',
        y='Percentage',
        text=chart_df['Percentage'].round(2).astype(str) + '%',
        labels={'Percentage': '비율 (%)', 'MBTI': 'MBTI 유형'},
        color='Percentage',
        color_continuous_scale=['#A0C4FF', '#0077B6'] # 파란색 계열 그라데이션 베이스
    )
    
    # 1등 막대 색상을 빨간색으로 개별 오버라이드
    fig.update_traces(
        marker_color=['#FF4B4B'] + ['#1F77B4'] * (len(chart_df) - 1),
        textposition='outside'
    )
    
    fig.update_layout(
        xaxis_title="MBTI 유형",
        yaxis_title="비율 (%)",
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        coloraxis_showscale=False, # 컬러바 숨기기
        margin=dict(t=30, b=30, l=30, r=30)
    )
    
    st.plotly_chart(fig, use_container_width=True)
