import pandas as pd
from . import yf_helper
from .strategy_classes import IStrategy
from .feature_builder import FeatureBuilder


class Account:
    def __init__(self, starting_capital: float = 20000, commission: float = 0, pos_size: float = 40):
        self.starting_capital = starting_capital
        self.commission = commission
        self.pos_size = pos_size


# TODO: Implement risk profile class and account specifications
class BackTester:
    def __init__(self):
        self.ohlcv_data = None

    # Returns a DataFrame with strategy details
    def run(self, strategy: IStrategy, account: Account = Account()) -> pd.DataFrame:
        builder = FeatureBuilder(self.ohlcv_data)
        features = strategy.prepare_features(builder).build()
        results = self.__run_backtest(strategy, features, account)

        return results

    # TODO: Needs refactoring
    def __run_backtest(self, strategy: IStrategy, features: pd.DataFrame, account: Account) -> pd.DataFrame:
        use_atr = False
        if features.empty:
            raise ValueError("No data passed in features DataFrame")
        if "ATR" in features.columns:
            use_atr = True
        print("Running backtest with: ", strategy.name(), " Using ATR: ", use_atr)
        features_data = features.copy()
        starting_capital = account.starting_capital
        current_capital = starting_capital
        position_size = account.pos_size
        position_type = 0  # -1 for short/sell, 0 for flat, 1 for buy
        entry_price = 0.0
        commission = account.commission

        df = pd.DataFrame(index=features.index.copy())
        df['Signal'] = None
        df['RealizedPnL'] = 0.0
        df['UnrealizedPnL'] = 0.0
        df['TotalRealPnL'] = 0.0
        df['CurrentCapital'] = 0.00
        df['Position'] = 0  # Track current position size (negative for shorts)
        df['EntryPrice'] = 0.0  # Track entry price for unrealized PnL calculation
        df['ClosingPrice'] = features['Close']
        df['Commission'] = 0.0
        df['TotalCommission'] = 0.0

        # Used if ATR is passed to see if we are stopped out
        def check_stop_loss(current_price: float, current_atr: float) -> bool:
            if pd.isna(current_atr) or position_type == 0:
                return False
            if position_type == 1:  # Long position
                pct_change = (current_price - entry_price) / entry_price
                return pct_change <= -current_atr
            else:  # Short position
                pct_change = (current_price - entry_price) / entry_price
                return pct_change >= current_atr

        for i in range(len(features_data) - 1):
            row = features_data.iloc[i]
            current_price = features_data['Close'].iloc[i]
            fill_price = features_data['Open'].iloc[i + 1]  # Our fill price is the next bars open

            if use_atr:
                current_atr = features_data['ATR'].iloc[i]
                if check_stop_loss(current_price, current_atr):
                    df.at[features_data.index[i], 'Commission'] = commission
                    if position_type == 1:
                        # Close long position at stop
                        realized_pnl = ((current_price - entry_price) * position_size)
                        current_capital += realized_pnl
                        position_type = 0
                        df.at[features_data.index[i], 'Signal'] = 'Stop Loss - Close Long'
                        df.at[features_data.index[i], 'Position'] = 0
                        df.at[features_data.index[i], 'RealizedPnL'] = realized_pnl
                        df.at[features_data.index[i], 'EntryPrice'] = 0.0
                    elif position_type == -1:
                        # Close short position at stop
                        realized_pnl = ((entry_price - current_price) * position_size)
                        current_capital += realized_pnl
                        position_type = 0
                        df.at[features_data.index[i], 'Signal'] = 'Stop Loss - Close Short'
                        df.at[features_data.index[i], 'Position'] = 0
                        df.at[features_data.index[i], 'RealizedPnL'] = realized_pnl
                        df.at[features_data.index[i], 'EntryPrice'] = 0.0

            strategy.on_bar(row)
            if strategy.should_buy(row):
                if position_type == 0:
                    # Open long
                    position_type = 1
                    entry_price = fill_price
                    if df.at[features_data.index[i], 'Signal'] is not None:
                        df.at[features_data.index[i], 'Signal'] += ', Open Long'
                    else:
                        df.at[features_data.index[i], 'Signal'] = 'Open Long'
                    df.at[features_data.index[i], 'Position'] = position_size
                    df.at[features_data.index[i], 'EntryPrice'] = entry_price
                    df.at[features_data.index[i], 'Commission'] = commission
                elif position_type == -1:
                    # Close short
                    position_type = 0
                    realized_pnl = ((entry_price - fill_price) * position_size)
                    current_capital += realized_pnl
                    if df.at[features_data.index[i], 'Signal'] is not None:
                        df.at[features_data.index[i], 'Signal'] += ', Close Short'
                    else:
                        df.at[features_data.index[i], 'Signal'] = 'Close Short'
                    df.at[features_data.index[i], 'Position'] = 0
                    df.at[features_data.index[i], 'RealizedPnL'] = realized_pnl
                    df.at[features_data.index[i], 'EntryPrice'] = 0.0
                    df.at[features_data.index[i], 'Commission'] = commission

            if strategy.should_sell(row):
                if position_type == 0:
                    # Open short
                    position_type = -1
                    entry_price = fill_price
                    if df.at[features_data.index[i], 'Signal'] is not None:
                        df.at[features_data.index[i], 'Signal'] += ', Open Short'
                    else:
                        df.at[features_data.index[i], 'Signal'] = 'Open Short'
                    df.at[features_data.index[i], 'Position'] = -position_size
                    df.at[features_data.index[i], 'EntryPrice'] = entry_price
                    df.at[features_data.index[i], 'Commission'] = commission
                elif position_type == 1:
                    # Close long
                    position_type = 0
                    realized_pnl = ((fill_price - entry_price) * position_size)
                    current_capital += realized_pnl
                    if df.at[features_data.index[i], 'Signal'] is not None:
                        df.at[features_data.index[i], 'Signal'] += ', Close Long'
                    else:
                        df.at[features_data.index[i], 'Signal'] = 'Close Long'
                    df.at[features_data.index[i], 'Position'] = 0
                    df.at[features_data.index[i], 'RealizedPnL'] = realized_pnl
                    df.at[features_data.index[i], 'EntryPrice'] = 0.0
                    df.at[features_data.index[i], 'Commission'] = commission

            # Calculate unrealized PnL for current position
            current_price = features_data['Close'].iloc[i]
            if position_type == 1:  # Long position
                unrealized_pnl = (current_price - entry_price) * position_size
            elif position_type == -1:  # Short position
                unrealized_pnl = (entry_price - current_price) * position_size
            else:
                unrealized_pnl = 0.0

            df.at[features_data.index[i], 'UnrealizedPnL'] = unrealized_pnl
            df.at[features_data.index[i], 'TotalRealPnL'] = df.at[features_data.index[i], 'RealizedPnL']
            df.at[features_data.index[i], 'CurrentCapital'] = current_capital + unrealized_pnl
            df.at[features_data.index[i], 'TotalCommission'] = df.at[features_data.index[i], 'Commission']
            if i > 0:
                # Add the previous TotalPnL to current TotalPnL so we have a rolling total
                df.at[features_data.index[i], 'TotalRealPnL'] += df.at[features_data.index[i - 1], 'TotalRealPnL']
                df.at[features_data.index[i], 'TotalCommission'] += df.at[features_data.index[i - 1], 'TotalCommission']

            if df.at[features_data.index[i], 'CurrentCapital'] <= 0:  # The account blew up :(
                break

        # Final mark to market step
        last_index = features_data.index[-1]
        unrealized_pnl = 0.0
        if position_type != 0:
            current_price = features_data['Close'].iloc[-1]
            if position_type == 1:
                unrealized_pnl = (current_price - entry_price) * position_size
            elif position_type == -1:
                unrealized_pnl = (entry_price - current_price) * position_size

        df.at[last_index, 'UnrealizedPnL'] = unrealized_pnl
        df.at[last_index, 'TotalRealPnL'] = df['TotalRealPnL'].iloc[-2]  # carry forward the previous total real PnL
        df.at[last_index, 'CurrentCapital'] = current_capital + unrealized_pnl
        df.at[last_index, 'TotalCommission'] = df['TotalCommission'].iloc[-2]
        return df

    def load_data(self, symbol: str, interval: str) -> "BackTester":
        self.ohlcv_data = yf_helper.get_ohlc_data(symbol, interval)
        return self
