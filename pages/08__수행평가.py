from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="지역별 범죄 통계 대시보드",
    page_icon="📊",
    layout="wide",
)

HOT_PINK = "#FF69B4"
SKY_BLUE = "#87CEEB"
ACCENT_PURPLE = "#9B5DE5"
ACCENT_TEAL = "#2EC4B6"

ID_COLS = ["범죄대분류", "범죄중분류"]


def extract_sido(col_name: str) -> str:
    if col_name == "세종시":
        return "세종시"
    return col_name.split(" ")[0]


@st.cache_data
def load_crime_data() -> tuple[pd.DataFrame, list[str]]:
    # 파일 위치: pages/의 상위 폴더(프로젝트 루트)
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


def apply_clean_layout(fig: go.Figure, title: str, height: int = 440) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=17, family="sans-serif")),
        height=height,
        template="plotly_white",
        hovermode="closest",
        margin=dict(l=24, r=24, t=54, b=24),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    return fig


def main() -> None:
    st.title("📊 지역별 범죄 통계 인터랙티브 분석")
    st.caption("`crime statistics by region.csv` 기반 · 범죄 대분류·중분류 및 시·도/시·군·구별 발생 현황")

    try:
        df, region_cols = load_crime_data()
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        st.stop()

    sido_map = {col: extract_sido(col) for col in region_cols}
    all_sidos = sorted(set(sido_map.values()))
    all_majors = df["범죄대분류"].unique().tolist()

    # 사이드바 필터
    with st.sidebar:
        st.header("🔎 조회 조건 설정")
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

    # 핵심 KPI
    total_cases = int(filtered_df[active_regions].values.sum())
    region_totals = filtered_df[active_regions].sum(axis=0).sort_values(ascending=False)
    sub_totals = (
        filtered_df.assign(합계=filtered_df[active_regions].sum(axis=1))
        .groupby(["범죄대분류", "범죄중분류"], as_index=False)["합계"]
        .sum()
        .sort_values("합계", ascending=False)
    )

    top_region_name = region_totals.index[0]
    top_region_val = int(region_totals.iloc[0])
    top_crime_name = sub_totals.iloc[0]["범죄중분류"]
    top_crime_val = int(sub_totals.iloc[0]["합계"])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("선택 조건 총 발생 건수", f"{total_cases:,}건")
    k2.metric("선택 지역 수", f"{len(active_regions):,}곳")
    k3.metric("최다 발생 지역", f"{top_region_name}", f"{top_region_val:,}건")
    k4.metric("최다 범죄 중분류", f"{top_crime_name}", f"{top_crime_val:,}건")

    st.divider()

    # 탭 1: 범죄 유형별 비교
    tab1, tab2, tab3 = st.tabs(["📌 범죄 유형별 분석", "🗺️ 지역별 순위 비교", "🔥 지역 × 범죄 히트맵"])

    with tab1:
        major_totals = (
            filtered_df.assign(합계=filtered_df[active_regions].sum(axis=1))
            .groupby("범죄대분류", as_index=False)["합계"]
            .sum()
            .sort_values("합계", ascending=True)
        )

        col_a, col_b = st.columns([1.15, 1])

        with col_a:
            fig_major = go.Figure(
                go.Bar(
                    x=major_totals["합계"],
                    y=major_totals["범죄대분류"],
                    orientation="h",
                    marker=dict(color=HOT_PINK, line=dict(width=0)),
                    text=[f"{v:,}건" for v in major_totals["합계"]],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>발생 건수: %{x:,}건<extra></extra>",
                )
            )
            fig_major.update_xaxes(title_text="발생 건수 (건)", gridcolor="#F0F0F0")
            fig_major.update_yaxes(title_text="범죄대분류")
            apply_clean_layout(fig_major, "범죄 대분류별 발생 건수", height=460)
            st.plotly_chart(fig_major, use_container_width=True)

        with col_b:
            top_sub = sub_totals.head(12).iloc[::-1]
            fig_sub = go.Figure(
                go.Bar(
                    x=top_sub["합계"],
                    y=top_sub["범죄중분류"],
                    orientation="h",
                    marker=dict(color=SKY_BLUE, line=dict(width=0)),
                    text=[f"{v:,}건" for v in top_sub["합계"]],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b> (%{customdata})<br>발생 건수: %{x:,}건<extra></extra>",
                    customdata=top_sub["범죄대분류"],
                )
            )
            fig_sub.update_xaxes(title_text="발생 건수 (건)", gridcolor="#F0F0F0")
            fig_sub.update_yaxes(title_text="범죄중분류")
            apply_clean_layout(fig_sub, "범죄 중분류 상위 12개", height=460)
            st.plotly_chart(fig_sub, use_container_width=True)

    with tab2:
        top_regions = region_totals.head(top_n).iloc[::-1]
        sido_totals = (
            region_totals.groupby(sido_map)
            .sum()
            .sort_values(ascending=False)
        )

        col_r1, col_r2 = st.columns([1.25, 1])

        with col_r1:
            fig_reg = go.Figure(
                go.Bar(
                    x=top_regions.values,
                    y=top_regions.index,
                    orientation="h",
                    marker=dict(color=HOT_PINK),
                    text=[f"{v:,}건" for v in top_regions.values],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>합계: %{x:,}건<extra></extra>",
                )
            )
            fig_reg.update_xaxes(title_text="발생 건수 (건)", gridcolor="#F0F0F0")
            fig_reg.update_yaxes(title_text="지역 / 구분")
            apply_clean_layout(fig_reg, f"지역별 발생 건수 상위 {top_n}곳", height=480)
            st.plotly_chart(fig_reg, use_container_width=True)

        with col_r2:
            fig_sido = go.Figure(
                go.Bar(
                    x=sido_totals.index,
                    y=sido_totals.values,
                    marker=dict(color=SKY_BLUE),
                    text=[f"{v:,}" for v in sido_totals.values],
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>합계: %{y:,}건<extra></extra>",
                )
            )
            fig_sido.update_xaxes(title_text="시·도 / 구분")
            fig_sido.update_yaxes(title_text="발생 건수 (건)", gridcolor="#F0F0F0")
            apply_clean_layout(fig_sido, "시·도별 발생 건수 합계", height=480)
            st.plotly_chart(fig_sido, use_container_width=True)

        # 선택 지역 상세 프로파일 (단일 지역 비교)
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
            fig_rd = go.Figure(
                go.Bar(
                    x=top10_reg_crime["발생건수"],
                    y=top10_reg_crime["범죄중분류"],
                    orientation="h",
                    marker=dict(color=ACCENT_TEAL),
                    text=[f"{v:,}건" for v in top10_reg_crime["발생건수"]],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>%{x:,}건<extra></extra>",
                )
            )
            fig_rd.update_xaxes(title_text="발생 건수 (건)", gridcolor="#F0F0F0")
            apply_clean_layout(fig_rd, f"{target_region} 주요 범죄 Top 10", height=380)
            st.plotly_chart(fig_rd, use_container_width=True)

        with c_right:
            st.dataframe(region_detail.reset_index(drop=True), use_container_width=True, height=380)

    with tab3:
        heat_regions = region_totals.head(min(top_n, 20)).index.tolist()
        heat_major_df = (
            filtered_df.groupby("범죄대분류", sort=False)[heat_regions]
            .sum()
        )
        heat_major_df = heat_major_df.loc[heat_major_df.sum(axis=1).sort_values(ascending=True).index]

        fig_heat = go.Figure(
            go.Heatmap(
                z=heat_major_df.values,
                x=heat_major_df.columns.tolist(),
                y=heat_major_df.index.tolist(),
                colorscale=[
                    [0.0, "#FFF5F9"],
                    [0.35, SKY_BLUE],
                    [0.7, HOT_PINK],
                    [1.0, ACCENT_PURPLE],
                ],
                hovertemplate="지역: <b>%{x}</b><br>대분류: <b>%{y}</b><br>건수: <b>%{z:,}건</b><extra></extra>",
            )
        )
        fig_heat.update_xaxes(title_text="지역 (상위 기준)")
        fig_heat.update_yaxes(title_text="범죄대분류")
        apply_clean_layout(fig_heat, "상위 지역 × 범죄 대분류 발생 강도 히트맵", height=520)
        st.plotly_chart(fig_heat, use_container_width=True)


if __name__ == "__main__":
    main()
