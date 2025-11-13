import pandas as pd
import numpy as np

from kis.api.quote import kis_get_last_quota

# RSI 수식 계산 함수
def calculate_rsi(df: pd.DataFrame, period: int) -> pd.Series:
    delta = df["close"].diff(1)

    U = np.where(delta > 0, delta, 0) # 상승분
    D = np.where(delta < 0, -delta, 0) # 하락분

    AU = pd.Series(U, index=df.index).rolling(window=period).mean() # 평균 상승폭
    AD = pd.Series(D, index=df.index).rolling(window=period).mean() # 평균 하락폭

    # RSI 게산 결과
    RSI = AU / (AU + AD) * 100
    return RSI

# 하나의 종목(symbol)의 최근 주가에 대한 RSI 계산
def get_rsi_for_symbol(symbol: str, period: int) -> pd.DataFrame:

    # 최근 100일치 일별 주가 데이터 (OHLCV)
    df = kis_get_last_quota(symbol, count=100)

    if df.empty:
        return pd.DataFrame(columns=["date", "close", "RSI"])

    # RSI 계산 함수 호출
    df["RSI"] = calculate_rsi(df, period)
    df = df.dropna(subset=["RSI"])

    return df[["date", "close", "RSI"]]

def update_rsi(df: pd.DataFrame, new_price: float, period: int = 14) -> pd.DataFrame:
    # 기존 데이터 복사
    df = df.copy()

    # 새 가격 추가
    next_date = pd.Timestamp.now().normalize()  # 오늘 날짜
    new_row = pd.DataFrame([{"date": next_date, "close": new_price}])
    df = pd.concat([df, new_row], ignore_index=True)

    # RSI 업데이트 계산
    delta = df["close"].diff(1)
    U = np.where(delta > 0, delta, 0)
    D = np.where(delta < 0, -delta, 0)
    AU = pd.Series(U, index=df.index).rolling(window=period).mean()
    AD = pd.Series(D, index=df.index).rolling(window=period).mean()
    df["RSI"] = AU / (AU + AD) * 100

    # 최신 1개 RSI 값만 반환할 수도 있음
    return df.tail(1)[["date", "close", "RSI"]]