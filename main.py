import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ===== 페이지 설정 =====
st.set_page_config(
    page_title="주식 분석 웹앱",
    page_icon="📈",
    layout="wide"
)

st.title("📈 한국·미국 주식 비교 분석")
st.caption("yfinance + Plotly를 활용한 주요 주식 수익률 & 차트 비교 도구")

# ===== 주요 종목 딕셔너리 (이름: 티커) =====
KOREA_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "현대차": "005380.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "기아": "000270.KS",
    "POSCO홀딩스": "005490.KS",
}

US_STOCKS = {
    "Apple (애플)": "AAPL",
    "Microsoft (마이크로소프트)": "MSFT",
    "NVIDIA (엔비디아)": "NVDA",
    "Amazon (아마존)": "AMZN",
    "Google (구글)": "GOOGL",
    "Tesla (테슬라)": "TSLA",
    "Meta (메타)": "META",
    "Netflix (넷플릭스)": "NFLX",
}

ALL_STOCKS = {**KOREA_STOCKS, **US_STOCKS}

# ===== 사이드바: 사용자 입력 =====
st.sidebar.header("⚙️ 설정")

selected_names = st.sidebar.multiselect(
    "비교할 종목을 선택하세요 (여러 개 가능)",
    options=list(ALL_STOCKS.keys()),
    default=["삼성전자", "Apple (애플)"]
)

period_option = st.sidebar.selectbox(
    "조회 기간",
    options=["1개월", "3개월", "6개월", "1년", "3년", "5년"],
    index=3
)

period_map = {
    "1개월": "1mo", "3개월": "3mo", "6개월": "6mo",
    "1년": "1y", "3년": "3y", "5년": "5y",
}
selected_period = period_map[period_option]

# 이동평균선 표시 여부
show_ma = st.sidebar.checkbox("이동평균선 표시 (20일, 60일)", value=True)


# ===== 데이터 불러오기 함수 (캐싱) =====
@st.cache_data(ttl=600)
def get_stock_data(ticker, period):
    """yfinance로 주가 데이터를 가져오는 함수"""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    return df


# ===== 메인 화면 =====
if not selected_names:
    st.info("👈 왼쪽 사이드바에서 비교할 종목을 선택해주세요!")
else:
    price_data = {}
    return_data = {}
    summary_list = []

    with st.spinner("주가 데이터를 불러오는 중..."):
        for name in selected_names:
            ticker = ALL_STOCKS[name]
            df = get_stock_data(ticker, selected_period)

            if df.empty:
                st.warning(f"⚠️ {name} 데이터를 불러올 수 없습니다.")
                continue

            price_data[name] = df["Close"]

            start_price = df["Close"].iloc[0]
            end_price = df["Close"].iloc[-1]
            return_data[name] = (df["Close"] / start_price - 1) * 100
            total_return = (end_price / start_price - 1) * 100

            currency = "원" if name in KOREA_STOCKS else "$"
            summary_list.append({
                "종목": name,
                "현재가": f"{end_price:,.0f} {currency}" if currency == "원"
                          else f"{currency}{end_price:,.2f}",
                "기간 수익률(%)": round(total_return, 2),
            })

    # ===== 1. 요약 표 =====
    st.subheader("📊 종목별 수익률 요약")
    if summary_list:
        summary_df = pd.DataFrame(summary_list)

        def highlight_return(val):
            if isinstance(val, (int, float)):
                color = "red" if val > 0 else "blue"
                return f"color: {color}; font-weight: bold;"
            return ""

        styled_df = summary_df.style.applymap(
            highlight_return, subset=["기간 수익률(%)"]
        )
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # ===== 2. 누적 수익률 비교 차트 (Plotly) =====
    st.subheader(f"📈 누적 수익률 비교 ({period_option})")
    if return_data:
        fig_return = go.Figure()
        for name, series in return_data.items():
            fig_return.add_trace(go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines",
                name=name,
                hovertemplate="%{y:.2f}%<extra>" + name + "</extra>"
            ))
        fig_return.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_return.update_layout(
            xaxis_title="날짜",
            yaxis_title="수익률 (%)",
            hovermode="x unified",
            height=500,
            legend=dict(orientation="h", y=1.1),
            template="plotly_white"
        )
        st.plotly_chart(fig_return, use_container_width=True)

    # ===== 3. 개별 종목 차트 (캔들 + 이동평균선 + 거래량) =====
    st.subheader("🔍 개별 종목 상세 차트")
    for name in selected_names:
        if name in price_data:
            with st.expander(f"📌 {name} 상세 차트 보기"):
                df = get_stock_data(ALL_STOCKS[name], selected_period)

                # 위(주가) / 아래(거래량) 2단 서브플롯 생성
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    row_heights=[0.7, 0.3],
                    subplot_titles=("주가 (캔들차트)", "거래량")
                )

                # (1) 캔들차트
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df["Open"], high=df["High"],
                    low=df["Low"], close=df["Close"],
                    name="주가",
                    increasing_line_color="red",   # 한국식: 상승=빨강
                    decreasing_line_color="blue"   # 하락=파랑
                ), row=1, col=1)

                # (2) 이동평균선 (선택 시)
                if show_ma:
                    ma20 = df["Close"].rolling(20).mean()
                    ma60 = df["Close"].rolling(60).mean()
                    fig.add_trace(go.Scatter(
                        x=df.index, y=ma20, name="MA20",
                        line=dict(color="orange", width=1.5)
                    ), row=1, col=1)
                    fig.add_trace(go.Scatter(
                        x=df.index, y=ma60, name="MA60",
                        line=dict(color="green", width=1.5)
                    ), row=1, col=1)

                # (3) 거래량 막대차트
                fig.add_trace(go.Bar(
                    x=df.index, y=df["Volume"],
                    name="거래량",
                    marker_color="lightgray"
                ), row=2, col=1)

                fig.update_layout(
                    height=600,
                    xaxis_rangeslider_visible=False,
                    template="plotly_white",
                    legend=dict(orientation="h", y=1.05),
                    hovermode="x unified"
                )
                fig.update_yaxes(title_text="가격", row=1, col=1)
                fig.update_yaxes(title_text="거래량", row=2, col=1)

                st.plotly_chart(fig, use_container_width=True)

# ===== 푸터 =====
st.divider()
st.caption("📌 데이터 출처: Yahoo Finance (yfinance) | 투자의 책임은 본인에게 있습니다.")
