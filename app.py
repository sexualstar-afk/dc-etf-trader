import time
import pandas as pd
import requests
from pykrx import stock

# 🔔 텔레그램 설정
TOKEN = "여기에_토큰"
CHAT_ID = "여기에_ID"

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# 🔥 요즘 테마 ETF 12종목
etf_list = {
    "반도체": "091170",
    "2차전지": "305720",
    "AI반도체": "396500",
    "전력인프라": "117460",
    "건설": "195970",
    "기계": "102780",
    "철강": "139230",
    "금융": "157450",
    "증권": "102970",
    "보험": "140700",
    "친환경": "385510",
    "로봇": "457450"
}

# 중복 알림 방지
last_signal = {}

print("🔥 ETF 자동 스캐너 시작")

while True:
    try:
        today = pd.Timestamp.today().strftime("%Y%m%d")

        for name, code in etf_list.items():
            df = stock.get_etf_ohlcv_by_date(
                fromdate="20240101",
                todate=today,
                ticker=code
            )

            if df.empty or len(df) < 30:
                continue

            df = df.rename(columns={
                "종가": "Close",
                "거래량": "Volume",
                "고가": "High",
                "저가": "Low"
            })

            # -----------------
            # 지표 계산
            # -----------------

            # VWAP
            tp = (df['High'] + df['Low'] + df['Close']) / 3
            df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

            # MACD
            ema12 = df['Close'].ewm(span=12).mean()
            ema26 = df['Close'].ewm(span=26).mean()
            df['MACD'] = ema12 - ema26
            df['Signal'] = df['MACD'].ewm(span=9).mean()

            # 이동평균선
            df['MA20'] = df['Close'].rolling(20).mean()

            latest = df.iloc[-1]

            # 거래량
            avg_vol = df['Volume'].rolling(10).mean().iloc[-1]
            vol_ratio = latest['Volume'] / avg_vol if avg_vol > 0 else 0

            # -----------------
            # 매수 조건
            # -----------------
            buy = (
                latest['Close'] < latest['VWAP'] and
                latest['MACD'] > latest['Signal'] and
                latest['Close'] > latest['MA20'] and
                vol_ratio > 1.5
            )

            # -----------------
            # 매도 조건
            # -----------------
            sell = (
                latest['Close'] > latest['VWAP'] and
                latest['MACD'] < latest['Signal']
            )

            signal = None
            if buy:
                signal = "BUY"
            elif sell:
                signal = "SELL"

            # -----------------
            # 중복 알림 방지
            # -----------------
            if signal and last_signal.get(name) != signal:
                msg = f"{'🟢 매수' if signal=='BUY' else '🔴 매도'}\n{name}\n가격:{int(latest['Close'])}"
                send(msg)
                last_signal[name] = signal

        print("✔ 스캔 완료")

    except Exception as e:
        print("에러:", e)

    # 🔥 3분마다 실행
    time.sleep(180)
