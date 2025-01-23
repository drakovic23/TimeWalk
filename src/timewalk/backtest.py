import pandas as pd
from . import yf_helper
from .strategy_classes import IStrategy
from .feature_builder import FeatureBuilder

# TODO: Implement risk profile class and account specifications
class BackTester:
    def __init__(self):
        self.ohlcv_data = None
    # Returns a DataFrame with strategy details
    def run(self, strategy: IStrategy) -> pd.DataFrame:
        builder = FeatureBuilder(self.ohlcv_data)
        features = strategy.prepare_features(builder).build()
        results = self.__run_backtest(strategy, features)

        return results
    #TODO: Needs refactoring
    def __run_backtest(self, strategy: IStrategy, features: pd.DataFrame) -> pd.DataFrame:
        use_atr = False
        if features.empty:
            raise ValueError("No data passed in features DataFrame")
        if "ATR" in features.columns:
            use_atr = True
        print("Running backtest with: ", strategy.name(), " Using ATR: ", use_atr)
        features_data = features.copy()
        starting_capital = 10000.00
        current_capital = starting_capital
        position_size = 20
        position_type = 0  # -1 for short/sell, 0 for flat, 1 for buy
        entry_price = 0.0

        df = pd.DataFrame(index=features.index.copy())
        df['Signal'] = None
        df['RealizedPnL'] = 0.0
        df['UnrealizedPnL'] = 0.0
        df['TotalRealPnL'] = 0.0
        df['CurrentCapital'] = 0.00
        df['Position'] = 0  # Track current position size (negative for shorts)
        df['EntryPrice'] = 0.0  # Track entry price for unrealized PnL calculation
        df['ClosingPrice'] = features['Close']

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
            fill_price = features_data['Open'].iloc[i + 1]
            if use_atr:
                current_atr = features_data['ATR'].iloc[i]
                if check_stop_loss(current_price, current_atr):
                    if position_type == 1:
                        # Close long position at stop
                        realized_pnl = (current_price - entry_price) * position_size
                        current_capital += realized_pnl
                        position_type = 0
                        df.at[features_data.index[i], 'Signal'] = 'Stop Loss - Close Long'
                        df.at[features_data.index[i], 'Position'] = 0
                        df.at[features_data.index[i], 'RealizedPnL'] = realized_pnl
                        df.at[features_data.index[i], 'EntryPrice'] = 0.0
                        #print(i, f"Stop loss hit - Closed long at @ {current_price} with pnl @ {realized_pnl}, ATR: {current_atr:.4f}")
                    elif position_type == -1:
                        # Close short position at stop
                        realized_pnl = (entry_price - current_price) * position_size
                        current_capital += realized_pnl
                        position_type = 0
                        df.at[features_data.index[i], 'Signal'] = 'Stop Loss - Close Short'
                        df.at[features_data.index[i], 'Position'] = 0
                        df.at[features_data.index[i], 'RealizedPnL'] = realized_pnl
                        df.at[features_data.index[i], 'EntryPrice'] = 0.0
                        #print(i, f"Stop loss hit - Closed short at @ {current_price} with pnl @ {realized_pnl}, ATR: {current_atr:.4f}")

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
                    #print(i, "Opened long at @", fill_price)
                elif position_type == -1:
                    # Close short
                    position_type = 0
                    realized_pnl = (entry_price - fill_price) * position_size
                    current_capital += realized_pnl
                    if df.at[features_data.index[i], 'Signal'] is not None:
                        df.at[features_data.index[i], 'Signal'] += ', Close Short'
                    else:
                        df.at[features_data.index[i], 'Signal'] = 'Close Short'
                    df.at[features_data.index[i], 'Position'] = 0
                    df.at[features_data.index[i], 'RealizedPnL'] = realized_pnl
                    df.at[features_data.index[i], 'EntryPrice'] = 0.0
                    #print(i, "Closed short at @", fill_price, "with pnl @", realized_pnl)
                #print(i, "Current capital: ", current_capital)

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
                    #print(i, "Opened short at @", fill_price)
                elif position_type == 1:
                    # Close long
                    position_type = 0
                    realized_pnl = (fill_price - entry_price) * position_size
                    current_capital += realized_pnl
                    if df.at[features_data.index[i], 'Signal'] is not None:
                        df.at[features_data.index[i], 'Signal'] += ', Close Long'
                    else:
                        df.at[features_data.index[i], 'Signal'] = 'Close Long'
                    df.at[features_data.index[i], 'Position'] = 0
                    df.at[features_data.index[i], 'RealizedPnL'] = realized_pnl
                    df.at[features_data.index[i], 'EntryPrice'] = 0.0
                    #print(i, "Closed long at @", fill_price, "with pnl @", realized_pnl)
                #print(i, "Current capital: ", current_capital)

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
            if i > 0:
                # Add the previous TotalPnL to current TotalPnL so we have a rolling total
                df.at[features_data.index[i], 'TotalRealPnL'] += df.at[features_data.index[i-1], 'TotalRealPnL']
            df.at[features_data.index[i], 'CurrentCapital'] = current_capital + unrealized_pnl

            if df.at[features_data.index[i], 'CurrentCapital'] <= 0: # The account blew up :(
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
        return df

    def load_data(self, symbol: str, interval: str) -> "BackTester":
        self.ohlcv_data = yf_helper.get_ohlc_data(symbol, interval)
        return self