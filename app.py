import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.title("📈 DC ETF 트레이더 (실전버전)")

etf_list = {
    "건설": "195970",
    "반도체": "091170",
    "S&P500": "360750",
    "코스피200": "069500"
}

selected = st.selectbox("ETF 선택", list(etf_list.keys()))
code = etf_list[selected]

df = yf.download(f"{code}.KS", period="3mo")

tp = (df['High'] + df['Low'] + df['Close']) / 3
df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
df['RSI'] = ta.rsi(df['Close'], length=14)

latest = df.iloc[-1]

st.write(f"현재가: {latest['Close']:.0f}")
st.write(f"VWAP: {latest['VWAP']:.0f}")
st.write(f"RSI: {latest['RSI']:.1f}")

if latest['Close'] < latest['VWAP'] and latest['RSI'] < 40:
    st.success("🔥 매수 가능")
elif latest['Close'] > latest['VWAP'] * 1.01:
    st.error("💰 익절 구간")
else:
    st.warning("대기")
