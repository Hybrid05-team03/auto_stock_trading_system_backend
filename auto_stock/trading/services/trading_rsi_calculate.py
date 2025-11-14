import numpy as np
import pandas as pd


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["close"].diff()

    U = np.where(delta > 0, delta, 0)
    D = np.where(delta < 0, -delta, 0)

    AU = pd.Series(U).rolling(period).mean()
    AD = pd.Series(D).rolling(period).mean()

    RSI = AU / (AU + AD) * 100
    return RSI