import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "stock_data.db"

# -----------------------------
# DB 불러오기
# -----------------------------
def load_symbols():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT 종목코드, 종목명 FROM stocks", conn)
    conn.close()
    return df

def load_prices(code):
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT 날짜, 종가, 시가, 고가, 저가, 거래량, 종목명, 종목코드
        FROM prices
        WHERE 종목코드='{code}'
        ORDER BY 날짜
    """
    df = pd.read_sql(query, conn, parse_dates=["날짜"])
    conn.close()
    df["종가보정"] = df["종가"]  # 기본은 종가 그대로
    return df

# -----------------------------
# B/T 탐색
# -----------------------------
def find_bt(df, rise_threshold=0.3):
    closes = df["종가보정"].values
    dates = df["날짜"].values

    b_points, t_points = [], []
    prev_high = closes[0]

    for i in range(1, len(closes)):
        price = closes[i]
        if price > prev_high:
            b_date, b_price = dates[i], price
            b_points.append((b_date, b_price))

            for j in range(i+1, len(closes)):
                if closes[j] >= b_price * (1 + rise_threshold):
                    peak_idx = j
                    while peak_idx+1 < len(closes) and closes[peak_idx+1] >= closes[peak_idx]:
                        peak_idx += 1
                    t_date, t_price = dates[peak_idx], closes[peak_idx]
                    t_points.append((t_date, t_price))
                    prev_high = t_price
                    i = peak_idx
                    break

        prev_high = max(prev_high, price)

    return b_points, t_points

# -----------------------------
# 리테스트 분석
# -----------------------------
def analyze_retests(df, b_points, t_points):
    result = []
    closes = df.set_index("날짜")["종가보정"]

    b_points = [(pd.to_datetime(d).date(), p) for d, p in b_points]
    t_points = [(pd.to_datetime(d).date(), p) for d, p in t_points]

    for t_idx, (t_date, _) in enumerate(t_points):
        for b_idx in range(t_idx+1):
            b_date, b_price = b_points[b_idx]
            closes_after_t = closes.loc[str(t_date):]

            if closes_after_t.min() <= b_price:
                retest_date = closes_after_t.idxmin().date()
                later_t = [d for d, _ in t_points if d > retest_date]

                if later_t:
                    next_t_date = later_t[0]
                    next_t_price = closes.loc[str(next_t_date)]
                    period = (next_t_date - b_date).days
                    result.append({
                        "목표": "다음T",
                        "목표가격": next_t_price,
                        "목표일": next_t_date,
                        "기간(일)": period
                    })
                else:
                    future_high = closes.loc[str(retest_date):].max()
                    future_date = closes.loc[str(retest_date):].idxmax().date()
                    period = (future_date - b_date).days
                    result.append({
                        "목표": "최고가",
                        "목표가격": future_high,
                        "목표일": future_date,
                        "기간(일)": period
                    })

    return pd.DataFrame(result)

# -----------------------------
# 최종 목표가/기간/수익률 계산
# -----------------------------
def analyze_target(df):
    b_points, t_points = find_bt(df)
    results = analyze_retests(df, b_points, t_points)

    current_price = df["종가보정"].iloc[-1]
    if results.empty:
        return None

    last = results.iloc[-1]

    if last["목표"] == "다음T":
        # ✅ 다음 T가 있는 경우 → 그대로 사용
        target_price = last["목표가격"]
        period = last["기간(일)"]
    else:
        # ✅ 다음 T가 없는 경우 → 최근 변동성 기반으로 예측
        recent = df["종가보정"].tail(60)
        high, low = recent.max(), recent.min()
        volatility = (high - low) / low if low > 0 else 0.2

        growth = max(0.1, volatility)  # 최소 10% 가정
        target_price = int(current_price * (1 + growth))

        # ✅ 항상 현재가보다 높게 보정
        if target_price <= current_price:
            target_price = int(current_price * 1.1)  # 최소 10% 상승 보정

        period = int(np.mean(results["기간(일)"])) if not results["기간(일)"].empty else 30

    today = pd.Timestamp.today().normalize()
    target_date = today + pd.to_timedelta(period, unit="D")

    expected_return = round((target_price - current_price) / current_price * 100, 1)

    return target_price, expected_return, period, target_date.date()
