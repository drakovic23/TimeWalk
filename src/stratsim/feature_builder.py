import pandas as pd
import numpy as np
import numba


class FeatureBuilder:
    """Builder class to construct feature sets for strategies"""

    def __init__(self, ohlc_data: pd.DataFrame):
        if "Open" not in ohlc_data.columns or "Close" not in ohlc_data.columns \
                or ohlc_data.shape[0] < 10:
            raise ValueError("ohlc_data does not contain sufficient OHLC data")
        self.features = ohlc_data.copy()

    def with_pct_change(self) -> "FeatureBuilder":
        calc_pct_chg(self.features)
        return self

    def with_rsi(self, window: int) -> "FeatureBuilder":
        calc_rsi_sma(self.features, window)
        return self

    def with_macd(self, fast: int = 12, slow: int = 26) -> "FeatureBuilder":
        calc_macd(self.features, ema_fast=fast, ema_slow=slow)
        return self

    def with_atr(self, window: int) -> "FeatureBuilder":
        calc_atr_vol(self.features, window)
        return self

    def build(self) -> pd.DataFrame:
        self.features.dropna(inplace=True)
        return self.features


def calc_pct_chg(ticker_data: pd.DataFrame) -> None:
    ticker_data['pct_chg'] = ticker_data['Close'].pct_change()


# Not currently used
def calc_atr_regular(ticker_data: pd.DataFrame) -> None:
    ticker_data['TR'] = np.maximum.reduce([
        ticker_data['High'] - ticker_data['Low'],
        abs(ticker_data['High'] - ticker_data['Close'].shift(1)),
        abs(ticker_data['Low'] - ticker_data['Close'].shift(1))
    ])
    # Rolling one day ATR
    ticker_data['ATR1D'] = (ticker_data['TR'] + ticker_data['TR'].shift(1)) * 1 / 2


# Calculates ATR for a given window
# Can also be used to calculate the rolling 1D ATR
# Adds an ATR column to the passed dataframe with the given window
def calc_atr_vol(ticker_data: pd.DataFrame, window: int) -> None:
    # This is different from the usual TR formula as it focuses on volatility
    df = ticker_data.copy()
    df['TR'] = ticker_data['High'] - ticker_data['Low']
    df['ATR1D_vol'] = (
            ((df['TR'] + df['TR'].shift(1)) / 2)
            / df['Open'].shift(1)
    )
    df['ATR'] = df['ATR1D_vol'].rolling(window=window).sum() / window
    ticker_data['ATR'] = df['ATR'].copy()


@numba.jit
def rma(x, n):
    """Running moving average"""
    a = np.full_like(x, np.nan)
    a[n] = x[1:n + 1].mean()
    for i in range(n + 1, len(x)):
        a[i] = (a[i - 1] * (n - 1) + x[i]) / n
    return a


# Adds a rsi column with given window to the passed dataframe
def calc_rsi_sma(ticker_data: pd.DataFrame, window: int = 14):
    rsi_column = f'rsi_{window}'
    ticker_data[rsi_column] = 100 - (100 / (
            1 + ticker_data['Close'].diff(1).mask(ticker_data['Close'].diff(1) < 0, 0)
            .ewm(alpha=1 / window, adjust=False).mean() /
            ticker_data['Close'].diff(1).mask(ticker_data['Close']
                                              .diff(1) > 0, -0.0).abs().ewm(alpha=1 / window, adjust=False).mean()))


# Adds sma with given window to the passed dataframe
def calc_sma(ticker_data: pd.DataFrame, window: int) -> None:
    ticker_data['SMA'] = ticker_data['Close'].rolling(window=window).sum() / window


# Adds
def calc_macd(ticker_data: pd.DataFrame, ema_fast: int, ema_slow: int) -> None:
    calc_ema(ticker_data, window=ema_fast, smoothing=2)
    calc_ema(ticker_data, window=ema_slow, smoothing=2)
    col_slow = f'EMA_{ema_slow}'
    col_fast = f'EMA_{ema_fast}'
    ticker_data['MACD'] = ticker_data[col_fast] - ticker_data[col_slow]
    # Should drop col_fast and col_slow here after testing perhaps
    calc_ema(ticker_data, window=9, col='MACD', smoothing=2) # Signal = EMA9(MACD)
    ticker_data.rename(columns={'EMA_9': 'MACD_signal'}, inplace=True)


# Adds ema column to the passed dataframe with the given window
# The col parameter is what column to calculate the EMA on
def calc_ema(ticker_data: pd.DataFrame, window: int, col: str = 'Close', smoothing: int = 2) -> None:
    if col not in ticker_data.columns:
        raise ValueError("Column: ", col, "not in passed dataframe")
    ema_column = f'EMA_{window}'
    smoothing = smoothing
    multiplier = smoothing / (window + 1)
    ticker_data[ema_column] = ticker_data[col].rolling(window=window, min_periods=1).mean()

    for i in range(window, len(ticker_data)):
        ticker_data.loc[ticker_data.index[i], ema_column] = (
                ticker_data.loc[ticker_data.index[i], col] * multiplier +
                ticker_data.loc[ticker_data.index[i - 1], ema_column] * (1 - multiplier)
        )
