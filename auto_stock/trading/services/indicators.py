import pandas as pd
import numpy as np

def calculate_rsi(df: pd.DataFrame, period: int = 2) -> pd.Series:
    delta = df['close'].diff(1)
    U = np.where(delta > 0, delta, 0)
    D = np.where(delta < 0, -delta, 0)
    AU = pd.Series(U, index=df.index).rolling(window=period).mean()
    AD = pd.Series(D, index=df.index).rolling(window=period).mean()
    RSI = AU / (AU + AD) * 100
    return RSI