import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import ALL_STOCKS, KOREA_STOCKS, PERIOD_MAP, get_stock_data

st.set_page_config(page_title="주식 비교분석", page_icon="📊", layout="wide")

st.title("📊 주식 비교분석")
st.caption("여러 종목의 수익률과 차트를 한눈에 비교해보세요")

# ===== 사이드바 입력 =====
st.sidebar.header("⚙️ 설정")
selected_names = st.sidebar.multiselect(
    "비교할 종목 선택",
    options=list(ALL_STOCKS.keys()),
    default=["삼성전자", "Apple (애플)"]
)
period_option = st.sidebar.selectbox(
    "조회 기간", list(PERIOD_MAP.keys()), index=3
)
selected_period = PERIOD_MAP[period_option]
show_ma = st.sidebar.checkbox("이동평균선 표시 (20일, 60일)", value=True)

# ===== 메인 =====
if not selected_names:
    st.info("👈 비교할 종목을 선택해주세요!")
else:
    price_data, return_data, summary_list = {}, {}, []

    with st.spinner("데이터 불러오는 중..."):
        for name in selected_names:
            df = get_stock_data(ALL_STOCKS[name], selected_period)
            if df.empty:
                st.warning(f"⚠️ {name} 데이터 없음")
                continue
            price_data[name] = df["Close"]
            start, end = df["Close"].iloc[0], df["Close"].iloc[-1]
            return_data[name] = (df["Close"] / start - 1) * 100
            total_return = (end / start - 1) * 100
            currency = "원" if name in KOREA_STOCKS else "$"
            price_text = f"{end:,.0f}원" if currency == "원" else f"${end:,.2f}"
            summary_list.append({"종목": name, "현재가": price_text, "수익률": total_return})

    # 1. 수익률 요약
    st.subheader("📊 종목별 수익률 요약")
    if summary_list:
        cols = st.columns(len(summary_list))
        for i, info in enumerate(summary_list):
            cols[i].metric(info["종목"], info["현재가"], f"{info['수익률']:.2f}%")

    # 2. 누적 수익률 차트
    st.subheader(f"📈 누적 수익률 비교 ({period_option})")
    if return_data:
        fig = go.Figure()
        for name, series in return_data.items():
            fig.add_trace(go.Scatter(x=series.index, y=series.values,
                                     mode="lines", name=name))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(xaxis_title="날짜", yaxis_title="수익률 (%)",
                          hovermode="x unified", height=500,
                          template="plotly_white",
                          legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    # 3. 개별 상세 차트
    st.subheader("🔍 개별 종목 상세 차트")
    for name in selected_names:
        if name in price_data:
            with st.expander(f"📌 {name} 상세 차트"):
                df = get_stock_data(ALL_STOCKS[name], selected_period)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                    vertical_spacing=0.05, row_heights=[0.7, 0.3],
                                    subplot_titles=("주가", "거래량"))
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df["Open"], high=df["High"],
                    low=df["Low"], close=df["Close"], name="주가",
                    increasing_line_color="red", decreasing_line_color="blue"
                ), row=1, col=1)
                if show_ma:
                    fig.add_trace(go.Scatter(x=df.index, y=df["Close"].rolling(20).mean(),
                                             name="MA20", line=dict(color="orange")), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df["Close"].rolling(60).mean(),
                                             name="MA60", line=dict(color="green")), row=1, col=1)
                fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="거래량",
                                     marker_color="lightgray"), row=2, col=1)
                fig.update_layout(height=600, xaxis_rangeslider_visible=False,
                                  template="plotly_white", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
