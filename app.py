import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.title("🔥 한국 ETF 트레이딩 스캐너 (VWAP + MACD + TOP3)")

# 🔥 ETF 12개 (레버리지/인버스 제외, 테마 중심)
etf_list = {
    "반도체": "091170.KS",
    "2차전지": "305720.KS",
    "건설": "195970.KS",
    "금융": "157450.KS",
    "철강": "139230.KS",
    "에너지화학": "308620.KS",
    "증권": "102970.KS",
    "보험": "140700.KS",
    "은행": "091180.KS",
    "기계장비": "102780.KS",
    "미디어": "266420.KS",
    "바이오": "244580.KS"
}

# 🔔 텔레그램 설정 (원하면 사용)
USE_ALERT = False
TOKEN = "여기에_봇토큰"
CHAT_ID = "여기에_채팅ID"

def send_alert(msg):
    if USE_ALERT:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

results = []

for name, code in etf_list.items():
    try:
        df = yf.download(code, period="3mo", progress=False)

        if df.empty or len(df) < 30:
            continue

        # ✔ VWAP
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

        # ✔ MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        latest = df.iloc[-1]

        # ✔ 거래량 점수
        avg_vol = df['Volume'].rolling(10).mean().iloc[-1]
        vol_score = latest['Volume'] / avg_vol if avg_vol > 0 else 0

        # ✔ 점수 계산
        score = 0

        if latest['Close'] < latest['VWAP']:
            score += 3

        if latest['MACD'] > latest['Signal']:
            score += 4

        if vol_score > 1.5:
            score += 3

        # ✔ 매수 / 매도 신호
        buy = (
            latest['Close'] < latest['VWAP'] and
            latest['MACD'] > latest['Signal'] and
            vol_score > 1.5
        )

        sell = (
            latest['Close'] > latest['VWAP'] and
            latest['MACD'] < latest['Signal']
        )

        results.append({
            "ETF": name,
            "가격": int(latest['Close']),
            "VWAP": int(latest['VWAP']),
            "MACD": round(latest['MACD'], 2),
            "거래량배수": round(vol_score, 2),
            "점수": score,
            "매수": "🟢" if buy else "",
            "매도": "🔴" if sell else ""
        })

    except:
        continue

# 🔥 결과 처리
if len(results) == 0:
    st.error("❌ 데이터 없음 (종목 코드 확인 필요)")
else:
    df_result = pd.DataFrame(results)

    # TOP3
    top3 = df_result.sort_values(by="점수", ascending=False).head(3)

    st.subheader("🔥 TOP3 추천")
    st.dataframe(top3, use_container_width=True)

    st.subheader("📊 전체 순위")
    st.dataframe(df_result.sort_values(by="점수", ascending=False), use_container_width=True)

    # 🔔 TOP3 알림
    msg = "🔥 ETF TOP3\n"
    for i, row in top3.iterrows():
        msg += f"{row['ETF']} | 점수:{row['점수']}\n"

    send_alert(msg)
