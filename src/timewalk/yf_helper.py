from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd

# Interval can be 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
def get_ohlc_data(ticker: str, interval="1d") -> pd.DataFrame:
    limited_intervals = list(["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"])
    ticker_symbol = yf.Ticker(ticker)
    # ticker_data = pd.DataFrame()
    if interval not in limited_intervals:
        ticker_data = ticker_symbol.history(period="max", interval=interval)
    else:
        start_date = datetime.today().date() - timedelta(days=729)
        end_date = datetime.today().date()
        ticker_data = ticker_symbol.history(interval=interval, start=start_date, end=end_date)
    ticker_data.dropna(inplace=True)
    return ticker_data

#def get_sp500_basket() -> list:
#    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
#    tables = pd.read_html(url)
#    sp500_table = tables[0]
#    sp500_symbols = sp500_table['Symbol'].tolist()
#    return sp500_symbols