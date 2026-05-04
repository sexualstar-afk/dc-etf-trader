import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.title("⚡ 전력/원전 ETF 자동 매매 스캐너 (TOP3 추천)")

# ✔ 실전용 ETF 10개 (엄선)
etf_list = {
    "에너지": "305540",
    "2차전지": "305720",
    "친환경에너지": "385510",
    "전력설비": "371460",
    "건설": "195970",
    "철강": "139230",
    "기계": "102960",
    "인프라": "329200",
    "고배당": "161510",
    "금융": "157450"
}

results = []

for name, code in etf_list.items():
    try:
        df = yf.download(f"{code}.KS", period="3mo", progress=False)

        if len(df) < 30:
            continue

        # ✔ VWAP 계산
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

        # ✔ RSI 계산 (pandas-ta 없이 직접 계산)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]

        # ✔ 거래량 분석
        avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
        vol_score = latest['Volume'] / avg_vol

        # ✔ 점수 시스템 (핵심 전략)
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

    except:
        continue

# ✔ 결과 정리
df_result = pd.DataFrame(results)

# ✔ TOP3 추출
top3 = df_result.sort_values(by="점수", ascending=False).head(3)

# ✔ 화면 출력
st.subheader("🔥 오늘의 TOP 3 추천")
st.dataframe(top3, use_container_width=True)

st.subheader("📊 전체 ETF 분석 결과")
st.dataframe(df_result.sort_values(by="점수", ascending=False), use_container_width=True)
