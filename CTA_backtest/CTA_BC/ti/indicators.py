import pandas as pd
import numpy as np
from typing import Dict, Union, Callable, Tuple

def MA(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()

def EMA(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def RSI(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def MACD(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    fast_ema = EMA(series, fast)
    slow_ema = EMA(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = EMA(macd_line, signal)
    histogram = macd_line - signal_line
    return {
        "macd": macd_line,
        "signal": signal_line,
        "hist": histogram
    }

def ATR(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def BOLL(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
    middle = MA(series, period)
    std = series.rolling(window=period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return {
        "upper": upper,
        "middle": middle,
        "lower": lower
    }

# 指标访问器，用于条件语法
def macd_line(fast: int = 12, slow: int = 26, signal: int = 9) -> Callable[[pd.DataFrame], pd.Series]:
    return lambda df: MACD(df["close"],fast,slow,signal)["macd"]

def macd_signal(fast: int = 12, slow: int = 26, signal: int = 9) -> Callable[[pd.DataFrame], pd.Series]:
    return lambda df: MACD(df["close"],fast,slow,signal)["signal"]

def macd_hist(fast: int = 12, slow: int = 26, signal: int = 9) -> Callable[[pd.DataFrame], pd.Series]:
    return lambda df: MACD(df["close"],fast,slow,signal)["hist"]

def rsi(period: int = 14) -> Callable[[pd.DataFrame], pd.Series]:
    return lambda df: RSI(df["close"], period)

def bollinger_upper(period: int = 20, std_dev: float = 2.0) -> Callable[[pd.DataFrame], pd.Series]:
    return lambda df: BOLL(df["close"], period, std_dev)["upper"]

def bollinger_middle(period: int = 20) -> Callable[[pd.DataFrame], pd.Series]:
    return lambda df: BOLL(df["close"], period)["middle"]

def bollinger_lower(period: int = 20, std_dev: float = 2.0) -> Callable[[pd.DataFrame], pd.Series]:
    return lambda df: BOLL(df["close"], period, std_dev)["lower"]

def sma(period: int) -> Callable[[pd.DataFrame], pd.Series]:
    return lambda df: MA(df["close"], period)

def ema(period: int) -> Callable[[pd.DataFrame], pd.Series]:
    return lambda df: EMA(df["close"], period) 