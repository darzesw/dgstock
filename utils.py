import streamlit as st
import yfinance as yf

# ===== 종목 딕셔너리 (모든 페이지에서 공유) =====
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

PERIOD_MAP = {
    "1개월": "1mo", "3개월": "3mo", "6개월": "6mo",
    "1년": "1y", "3년": "3y", "5년": "5y",
}


@st.cache_data(ttl=600)
def get_stock_data(ticker, period):
    """yfinance로 주가 데이터를 가져오는 함수"""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    return df
