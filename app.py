import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.title("⚡ KODEX / TIGER 테마 ETF 자동 스캐너 (TOP3 추천)")

# ✔ KODEX + TIGER 테마 ETF (데이터 검증된 것 위주)
etf_list = {
    "KODEX 2차전지": "305720",
    "KODEX 반도체": "091170",
    "KODEX 건설": "117700",
    "KODEX 철강": "139230",
    "KODEX IT": "266370",

    "TIGER 반도체TOP10": "396500",
    "TIGER 2차전지소재": "305540",
    "TIGER 코리아테크": "329200",
    "TIGER AI반도체": "466950",
    "TIGER 기후변화": "400570"
}

results = []

for name, code in etf_list.items():
    try:
        # ✔ 야후 데이터 가져오기
        df = yf.download(f"{code}.KS", period="3mo", progress=False)

        if df is None or df.empty or len(df) < 30:
            continue

        # ✔ VWAP 계산
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

        # ✔ RSI 계산 (직접 계산)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]

        # ✔ 거래량 분석
        avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
        vol_score = latest['Volume'] / avg_vol if avg_vol > 0 else 0

        # ✔ 점수 계산 (핵심 전략)
        score = 0
        if latest['Close'] < latest['VWAP']:
            score += 3
        if latest['RSI'] < 40:
            score += 3
        if vol_score > 2:
            score += 4

        results.append({
            "ETF": name,
            "가격": int(latest['Close']),
            "RSI": round(latest['RSI'], 1),
            "VWAP괴리%": round((latest['Close'] - latest['VWAP']) / latest['VWAP'] * 100, 2),
            "거래량배수": round(vol_score, 2),
            "점수": score
        })

    except Exception as e:
        continue

# ✔ 결과 처리
if len(results) == 0:
    st.error("❌ 데이터 없음 → 일부 ETF는 야후 미지원 (정상 현상)")
else:
    df_result = pd.DataFrame(results)

    if "점수" in df_result.columns:
        top3 = df_result.sort_values(by="점수", ascending=False).head(3)

        st.subheader("🔥 오늘의 TOP 3 추천")
        st.dataframe(top3, use_container_width=True)

        st.subheader("📊 전체 ETF 순위")
        st.dataframe(df_result.sort_values(by="점수", ascending=False), use_container_width=True)
    else:
        st.error("❌ 점수 계산 오류")
