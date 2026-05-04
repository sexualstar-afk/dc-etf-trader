import streamlit as st
import pandas as pd
import requests

st.title("🔥 KODEX / TIGER ETF 트레이딩 스캐너 (VWAP + MACD)")

# ✔ ETF 리스트 (균형형)
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

# ✔ 네이버 데이터 안정 수집
def get_price(code):
    url = f"https://finance.naver.com/item/sise_day.naver?code={code}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ko-KR,ko;q=0.9"
    }

    try:
        res = requests.get(url, headers=headers, timeout=5)

        if res.status_code != 200:
            return pd.DataFrame()

        tables = pd.read_html(res.text, encoding='euc-kr')
        df = tables[0]

        df = df.dropna()

        if '종가' not in df.columns:
            return pd.DataFrame()

        df = df.rename(columns={
            '종가': 'Close',
            '거래량': 'Volume'
        })

        df = df[['Close', 'Volume']]

        return df[::-1]

    except:
        return pd.DataFrame()


results = []

for name, code in etf_list.items():
    df = get_price(code)

    # 👉 디버그 (데이터 확인용)
    st.write(f"{name} 데이터 수:", len(df))

    if df.empty or len(df) < 30:
        continue

    try:
        price = df['Close']
        volume = df['Volume']

        # ✔ VWAP
        df['VWAP'] = (price * volume).cumsum() / volume.cumsum()

        # ✔ MACD
        ema12 = price.ewm(span=12, adjust=False).mean()
        ema26 = price.ewm(span=26, adjust=False).mean()

        df['MACD'] = ema12 - ema26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        latest = df.iloc[-1]

        # ✔ 거래량
        avg_vol = volume.rolling(10).mean().iloc[-1]
        vol_score = latest['Volume'] / avg_vol if avg_vol > 0 else 0

        # ✔ 점수 계산
        score = 0

        if latest['Close'] < latest['VWAP']:
            score += 3

        if latest['MACD'] > latest['Signal']:
            score += 4

        if vol_score > 1.5:
            score += 3

        results.append({
            "ETF": name,
            "가격": int(latest['Close']),
            "VWAP": int(latest['VWAP']),
            "MACD": round(latest['MACD'], 2),
            "거래량배수": round(vol_score, 2),
            "점수": score
        })

    except:
        continue


# ✔ 결과 출력
if len(results) == 0:
    st.error("❌ 데이터 없음 → 네이버 차단 또는 종목 문제")
else:
    df_result = pd.DataFrame(results)

    top3 = df_result.sort_values(by="점수", ascending=False).head(3)

    st.subheader("🔥 TOP 3 추천")
    st.dataframe(top3, use_container_width=True)

    st.subheader("📊 전체 ETF 순위")
    st.dataframe(df_result.sort_values(by="점수", ascending=False), use_container_width=True)
