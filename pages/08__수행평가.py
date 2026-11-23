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

    # 1. 범죄 종류별 그래프 (각 대분류/중분류가 속한 대분류 색상을 가짐)
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
            fig_major.update_xaxes(title_text="발생 건수 (건)", gridcolor="#F0F0F0")
            fig_major.update_yaxes(title_text="범죄대분류")
            apply_clean_layout(fig_major, "범죄 대분류별 발생 건수 (대분류 고유 색상)", height=500, show_legend=True)
            st.plotly_chart(fig_major, use_container_width=True)

        with col_b:
            top_sub = sub_totals.head(12).iloc[::-1]
            fig_sub = go.Figure()
            seen_sub_majors: set[str] = set()
            for idx, row in top_sub.iterrows():
                s_name = row["범죄중분류"]
                m_name = row["범죄대분류"]
                s_val = int(row["합계"])
                show_leg = m_name not in seen_sub_majors
                seen_sub_majors.add(m_name)
                fig_sub.add_trace(
                    go.Bar(
                        x=[s_val],
                        y=[s_name],
                        name=m_name,
                        legendgroup=m_name,
                        showlegend=show_leg,
                        orientation="h",
                        marker=dict(color=get_major_color(m_name, idx)),
                        text=[f"{s_val:,}건"],
                        textposition="outside",
                        customdata=[[m_name]],
                        hovertemplate=(
                            "<b>%{y}</b> (%{customdata[0]})<br>"
                            "발생 건수: %{x:,}건<extra></extra>"
                        ),
                    )
                )
            fig_sub.update_xaxes(title_text="발생 건수 (건)", gridcolor="#F0F0F0")
            fig_sub.update_yaxes(title_text="범죄중분류")
            apply_clean_layout(fig_sub, "범죄 중분류 상위 12개 (상위 대분류 색상)", height=500, show_legend=True)
            st.plotly_chart(fig_sub, use_container_width=True)

    # 2. 지역별 그래프 (시·도별 색상 또는 최다 범죄대분류 색상)
    with tab2:
        top_regions = region_totals.head(top_n).iloc[::-1]
        sido_totals = region_totals.groupby(sido_map).sum().sort_values(ascending=False)

        col_r1, col_r2 = st.columns([1.2, 1])

        with col_r1:
            fig_reg = go.Figure()
            seen_groups: set[str] = set()
            for idx, (reg_name, reg_val) in enumerate(top_regions.items()):
                r_val = int(reg_val)
                s_name = sido_map[reg_name]
                top_m_row = filtered_df.loc[filtered_df[reg_name].idxmax()]
                top_m_name = top_m_row["범죄대분류"]
                top_m_sub = top_m_row["범죄중분류"]

                if region_color_mode == "시·도별 색상":
                    group_key = s_name
                    bar_color = get_sido_color(s_name, idx)
                else:
                    group_key = top_m_name
                    bar_color = get_major_color(top_m_name, idx)

                show_leg = group_key not in seen_groups
                seen_groups.add(group_key)

                fig_reg.add_trace(
                    go.Bar(
                        x=[r_val],
                        y=[reg_name],
                        name=group_key,
                        legendgroup=group_key,
                        showlegend=show_leg,
                        orientation="h",
                        marker=dict(color=bar_color),
                        text=[f"{r_val:,}건"],
                        textposition="outside",
                        customdata=[[s_name, top_m_sub, int(top_m_row[reg_name])]],
                        hovertemplate=(
                            "<b>%{y}</b> (%{customdata[0]})<br>"
                            "합계: %{x:,}건<br>"
                            "최다 범죄: %{customdata[1]} (%{customdata[2]:,}건)<extra></extra>"
                        ),
                    )
                )
            fig_reg.update_xaxes(title_text="발생 건수 (건)", gridcolor="#F0F0F0")
            fig_reg.update_yaxes(title_text="지역 / 구분")
            apply_clean_layout(
                fig_reg,
                f"지역별 발생 건수 상위 {top_n}곳 ({region_color_mode})",
                height=500,
                show_legend=True,
            )
            st.plotly_chart(fig_reg, use_container_width=True)

        with col_r2:
            fig_sido = go.Figure()
            for idx, (s_name, s_val) in enumerate(sido_totals.items()):
                val_int = int(s_val)
                fig_sido.add_trace(
                    go.Bar(
                        x=[s_name],
                        y=[val_int],
                        name=s_name,
                        marker=dict(color=get_sido_color(s_name, idx)),
                        text=[f"{val_int:,}"],
                        textposition="outside",
                        hovertemplate="<b>%{x}</b><br>합계: %{y:,}건<extra></extra>",
                    )
                )
            fig_sido.update_xaxes(title_text="시·도 / 구분")
            fig_sido.update_yaxes(title_text="발생 건수 (건)", gridcolor="#F0F0F0")
            apply_clean_layout(fig_sido, "시·도별 발생 건수 합계 (시·도 고유 색상)", height=500, show_legend=True)
            st.plotly_chart(fig_sido, use_container_width=True)

        st.subheader("🔍 특정 지역 세부 범죄 구성 보기")
        target_region = st.selectbox(
            "상세 범죄 항목을 확인할 지역 선택",
            options=region_totals.index.tolist(),
        )
        region_detail = (
            filtered_df[["범죄대분류", "범죄중분류", target_region]]
            .rename(columns={target_region: "발생건수"})
            .sort_values("발생건수", ascending=False)
        )
        c_left, c_right = st.columns([1.2, 1])
        with c_left:
            top10_reg_crime = region_detail.head(10).iloc[::-1]
            fig_rd = go.Figure()
            seen_rd_majors: set[str] = set()
            for idx, row in top10_reg_crime.iterrows():
                c_sub = row["범죄중분류"]
                c_maj = row["범죄대분류"]
                c_cnt = int(row["발생건수"])
                show_leg = c_maj not in seen_rd_majors
                seen_rd_majors.add(c_maj)
                fig_rd.add_trace(
                    go.Bar(
                        x=[c_cnt],
                        y=[c_sub],
                        name=c_maj,
                        legendgroup=c_maj,
                        showlegend=show_leg,
                        orientation="h",
                        marker=dict(color=get_major_color(c_maj, idx)),
                        text=[f"{c_cnt:,}건"],
                        textposition="outside",
                        customdata=[[c_maj]],
                        hovertemplate="<b>%{y}</b> (%{customdata[0]})<br>%{x:,}건<extra></extra>",
                    )
                )
            fig_rd.update_xaxes(title_text="발생 건수 (건)", gridcolor="#F0F0F0")
            apply_clean_layout(fig_rd, f"{target_region} 주요 범죄 Top 10 (대분류 색상)", height=400, show_legend=True)
            st.plotly_chart(fig_rd, use_container_width=True)

        with c_right:
            st.dataframe(region_detail.reset_index(drop=True), use_container_width=True, height=400)

    # 3. 히트맵
    with tab3:
        heat_regions = region_totals.head(min(top_n, 20)).index.tolist()
        heat_major_df = filtered_df.groupby("범죄대분류", sort=False)[heat_regions].sum()
        heat_major_df = heat_major_df.loc[heat_major_df.sum(axis=1).sort_values(ascending=True).index]

        fig_heat = go.Figure(
            go.Heatmap(
                z=heat_major_df.values,
                x=heat_major_df.columns.tolist(),
                y=heat_major_df.index.tolist(),
                colorscale=[
                    [0.0, "#FFF5F9"],
                    [0.35, "#87CEEB"],
                    [0.7, "#FF69B4"],
                    [1.0, "#9B5DE5"],
                ],
                hovertemplate="지역: <b>%{x}</b><br>대분류: <b>%{y}</b><br>건수: <b>%{z:,}건</b><extra></extra>",
            )
        )
        fig_heat.update_xaxes(title_text="지역 (상위 기준)")
        fig_heat.update_yaxes(title_text="범죄대분류")
        apply_clean_layout(fig_heat, "상위 지역 × 범죄 대분류 발생 강도 히트맵", height=520, show_legend=False)
        st.plotly_chart(fig_heat, use_container_width=True)


if __name__ == "__main__":
    main()
