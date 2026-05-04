import streamlit as st
import pandas as pd
import requests

st.title("🔥 KODEX / TIGER ETF 트레이딩 스캐너 (VWAP + MACD)")

# ✔ ETF 구성 (균형형)
etf_list = {
    "TIGER 2차전지테마": "305540",
    "KODEX 반도체": "091170",
    "TIGER 반도체": "091230",
    "KODEX 건설": "117700",
    "KODEX 철강": "139230",
    "TIGER 원자력": "457480",
    "TIGER 친환경에너지": "475070",
    "KODEX 기계장비": "102960",
    "TIGER 코리아테크": "329200",
    "KODEX 금융": "157450"
}

# ✔ 네이버 데이터
def get_price(code):
    url = f"https://finance.naver.com/item/sise_day.naver?code={code}"
    headers = {"User-Agent": "Mozilla/5.0"}

    df = pd.read_html(requests.get(url, headers=headers).text, encoding='euc-kr')[0]
    df = df.dropna()

    df = df.rename(columns={
        '종가': 'Close',
        '거래량': 'Volume'
    })

    df = df[['Close', 'Volume']]

    return df[::-1]


results = []

for name, code in etf_list.items():
    try:
        df = get_price(code)

        if df.empty or len(df) < 30:
            continue

        # -----------------------------
        # ✔ VWAP 계산
        # -----------------------------
        price = df['Close']
        volume = df['Volume']

        df['VWAP'] = (price * volume).cumsum() / volume.cumsum()

        # -----------------------------
        # ✔ MACD 계산
        # -----------------------------
        ema12 = price.ewm(span=12, adjust=False).mean()
        ema26 = price.ewm(span=26, adjust=False).mean()

        df['MACD'] = ema12 - ema26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        latest = df.iloc[-1]

        # -----------------------------
        # ✔ 거래량
        # -----------------------------
        avg_vol = volume.rolling(10).mean().iloc[-1]
        vol_score = latest['Volume'] / avg_vol if avg_vol > 0 else 0

        # -----------------------------
        # ✔ 점수 시스템 (핵심)
        # -----------------------------
        score = 0

        # VWAP 눌림
        if latest['Close'] < latest['VWAP']:
            score += 3

        # MACD 상승 전환
        if latest['MACD'] > latest['Signal']:
            score += 4

        # 거래량 증가
        if vol_score > 1.5:
            score += 3

        results.append({
            "ETF": name,
            "가격": int(latest['Close']),
            "VWAP": int(latest['VWAP']),
            "MACD": round(latest['MACD'], 2),
            "Signal": round(latest['Signal'], 2),
            "거래량배수": round(vol_score, 2),
            "점수": score
        })

    except:
        continue


# -----------------------------
# ✔ 결과 출력
# -----------------------------
if len(results) == 0:
    st.error("❌ 데이터 없음")
else:
    df_result = pd.DataFrame(results)

    top3 = df_result.sort_values(by="점수", ascending=False).head(3)

    st.subheader("🔥 TOP 3 추천 (VWAP + MACD)")
    st.dataframe(top3, use_container_width=True)

    st.subheader("📊 전체 ETF 순위")
    st.dataframe(df_result.sort_values(by="점수", ascending=False), use_container_width=True)
