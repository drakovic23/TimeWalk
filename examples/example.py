import stratsim as st
from stratsim.strategy_classes import *

bt = st.BackTester()

results = (bt.load_data("TSLA", "1d")
 .run(RsiStrategy(rsi_window=20)))

print(results['CurrentCapital'].tail(10)) # Get the current capital of the account

results = (bt.load_data("TSLA", "1d")
 .run(RsiStrategy(rsi_window=20,atr_window=20))) # Can use ATR (Average True Range) as a stop loss mechanism

print(results['CurrentCapital'].tail(10)) # Get the current capital of the account

# Implement your own strategies:
class MyRsiStrat(IStrategy):
    def __init__(self, rsi_window: int):
        self.rsi_window = rsi_window
        config = StrategyConfig(
            name="My strategy",
            parameters={
                "rsi_window": rsi_window,
            }
        )
        super().__init__(config)
        self.required_features = [f'rsi_{rsi_window}']

    # Prepare your features with the feature builder
    def prepare_features(self, builder: FeatureBuilder) -> FeatureBuilder:
        ret = builder.with_rsi(window=self.rsi_window)
        return ret

    def name(self):
        return self.config.name

    def on_bar(self, bar): # On bar processing
        pass

    def should_buy(self, row: pd.Series): # Should buy signal
        if row[self.required_features[0]] <= 30: # Buy when our feature (RSI) is <= than 30
            return True


    def should_sell(self, row: pd.Series): # Should sell signal
        if row[self.required_features[0]] >= 70: # Sell when our feature is >= 70
            return True
        pass

# Run our custom strategy
bt.load_data("TSLA", "1d").run(MyRsiStrat(rsi_window=20))