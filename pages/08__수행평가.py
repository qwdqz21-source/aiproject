from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="지역별 범죄 통계 대시보드",
    page_icon="📊",
    layout="wide",
)

ID_COLS = ["범죄대분류", "범죄중분류"]

# 범죄 대분류별 고정 색상 팔레트
CRIME_MAJOR_COLORS: dict[str, str] = {
    "지능범죄": "#FF69B4",     # 핫핑크
    "기타범죄": "#87CEEB",     # 하늘색
    "교통범죄": "#4EA8DE",     # 선명한 블루
    "폭력범죄": "#F77F00",     # 오렌지
    "절도범죄": "#9B5DE5",     # 퍼플
    "특별경제범죄": "#2EC4B6", # 틸 그린
    "풍속범죄": "#F15BB5",     # 핑크 마젠타
    "강력범죄": "#D62828",     # 크림슨 레드
    "마약범죄": "#7209B7",     # 딥 바이올렛
    "병역범죄": "#577590",     # 슬레이트 블루
    "보건범죄": "#43AA8B",     # 에메랄드
    "선거범죄": "#F9C74F",     # 앰버 옐로우
    "환경범죄": "#90BE6D",     # 라임 그린
    "안보범죄": "#2B2D42",     # 차콜 네이비
    "노동범죄": "#A8DADC",     # 파스텔 아쿠아
}

# 시·도 / 구분별 고정 색상 팔레트
SIDO_COLORS: dict[str, str] = {
    "경기도": "#FF69B4",
    "서울": "#87CEEB",
    "부산": "#4EA8DE",
    "경남": "#9B5DE5",
    "인천": "#2EC4B6",
    "대구": "#F77F00",
    "경북": "#90BE6D",
    "충남": "#F9C74F",
    "전북": "#F15BB5",
    "전남": "#43AA8B",
    "충북": "#577590",
    "대전": "#A29BFE",
    "광주": "#FF8FA3",
    "강원도": "#48CAE4",
    "울산": "#E07A5F",
    "제주": "#00B4D8",
    "세종시": "#B5838D",
    "외국": "#6C757D",
}

FALLBACK_PALETTE = [
    "#FF69B4", "#87CEEB", "#9B5DE5", "#2EC4B6", "#F77F00",
    "#4EA8DE", "#90BE6D", "#F9C74F", "#F15BB5", "#577590",
]


def get_major_color(major: str, idx: int = 0) -> str:
    return CRIME_MAJOR_COLORS.get(major, FALLBACK_PALETTE[idx % len(FALLBACK_PALETTE)])


def get_sido_color(sido: str, idx: int = 0) -> str:
    return SIDO_COLORS.get(sido, FALLBACK_PALETTE[idx % len(FALLBACK_PALETTE)])


def extract_sido(col_name: str) -> str:
    if col_name == "세종시":
        return "세종시"
    return col_name.split(" ")[0]


@st.cache_data
def load_crime_data() -> tuple[pd.DataFrame, list[str]]:
    csv_path = Path(__file__).resolve().parent.parent / "crime statistics by region.csv"
    if not csv_path.exists():
        csv_path = Path("crime statistics by region.csv")

    df = None
    for enc in ("cp949", "euc-kr", "utf-8-sig", "utf-8"):
        try:
            df = pd.read_csv(csv_path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError("CSV 파일 인코딩을 읽을 수 없습니다. (cp949 / utf-8 확인 필요)")

    region_cols = [c for c in df.columns if c not in ID_COLS]
    df[region_cols] = df[region_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
    return df, region_cols


def apply_clean_layout(
    fig: go.Figure,
    title: str,
    height: int = 450,
    show_legend: bool = True,
) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=17, family="sans-serif")),
        height=height,
        template="plotly_white",
        hovermode="closest",
        showlegend=show_legend,
        margin=dict(l=24, r=24, t=60, b=24),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=11),
        ),
    )
    return fig


def main() -> None:
    st.title("📊 지역별 범죄 통계 인터랙티브 분석")
    st.caption("범죄 대분류 및 시·도 구분별 고유 컬러 매핑이 적용된 인터랙티브 대시보드")

    try:
        df, region_cols = load_crime_data()
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        st.stop()

    sido_map = {col: extract_sido(col) for col in region_cols}
    all_sidos = sorted(set(sido_map.values()))
    all_majors = df["범죄대분류"].unique().tolist()

    with st.sidebar:
        st.header("🔎 조회 및 색상 설정")
        default_sidos = [s for s in ["경기도", "서울", "부산", "인천", "대구"] if s in all_sidos]
        selected_sidos = st.multiselect(
            "시·도 / 구분 선택",
            options=all_sidos,
            default=default_sidos if default_sidos else all_sidos[:5],
        )
        selected_majors = st.multiselect(
            "범죄 대분류 선택",
            options=all_majors,
            default=all_majors,
        )
        region_color_mode = st.radio(
            "지역 순위 막대 색상 기준",
            options=["시·도별 색상", "최다 발생 범죄대분류 색상"],
            index=0,
        )
        top_n = st.slider("상위 지역 표시 개수 (Top N)", min_value=5, max_value=30, value=15, step=1)
        include_foreign = st.checkbox("'외국' 구분 포함", value=True)

    active_regions = [
        col for col in region_cols
        if sido_map[col] in (selected_sidos if selected_sidos else all_sidos)
        and (include_foreign or not col.startswith("외국 "))
    ]
    filtered_df = df[df["범죄대분류"].isin(selected_majors if selected_majors else all_majors)].copy()

    if not active_regions or filtered_df.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해 주세요.")
        st.stop()

    total_cases = int(filtered_df[active_regions].values.sum())
    region_totals = filtered_df[active_regions].sum(axis=0).sort_values(ascending=False)
    sub_totals = (
        filtered_df.assign(합계=filtered_df[active_regions].sum(axis=1))
        .groupby(["범죄대분류", "범죄중분류"], as_index=False)["합계"]
        .sum()
        .sort_values("합계", ascending=False)
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("선택 조건 총 발생 건수", f"{total_cases:,}건")
    k2.metric("선택 지역 수", f"{len(active_regions):,}곳")
    k3.metric("최다 발생 지역", f"{region_totals.index[0]}", f"{int(region_totals.iloc[0]):,}건")
    k4.metric("최다 범죄 중분류", f"{sub_totals.iloc[0]['범죄중분류']}", f"{int(sub_totals.iloc[0]['합계']):,}건")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["📌 범죄 종류별 색상 비교", "🗺️ 지역별 색상 비교", "🔥 지역 × 범죄 히트맵"])

    with tab1:
        major_totals = (
            filtered_df.assign(합계=filtered_df[active_regions].sum(axis=1))
            .groupby("범죄대분류", as_index=False)["합계"]
            .sum()
            .sort_values("합계", ascending=True)
        )

        col_a, col_b = st.columns([1.1, 1])

        with col_a:
            fig_major = go.Figure()
            for idx, row in major_totals.iterrows():
                m_name = row["범죄대분류"]
                m_val = int(row["합계"])
                fig_major.add_trace(
                    go.Bar(
                        x=[m_val],
                        y=[m_name],
                        name=m_name,
                        orientation="h",
                        marker=dict(color=get_major_color(m_name, idx)),
                        text=[f"{m_val:,}건"],
                        textposition="outside",
                        hovertemplate="<b>%{y}</b><br>발생 건수: %{x:,}건<extra></extra>",
                    )
                )
            fig_major.update_xaxes(title_text="발생 건
