<table border=1 cellpadding=10><tr><td>

#### \*\*\* IMPORTANT LEGAL DISCLAIMER! \*\*\*

---

This is a fun project I am writing to simulate/backtest basic strategies.
It should not be used with real capital. I am not responsible for any
monetary losses. You should not make decisions based solely on basic strategies such as technical indicators anyways.

</td></tr></table>

---
### Install
```angular2html
pip install timewalk
```
## Main components

- `FeatureBuilder`: A class that handles feature generation such as RSI, MACD etc.
- `IStrategy`: An abstract class used to implement strategies
- `BackTester`: A class used to run strategies and load data

## Usage
Create the backtester and run a strategy:
```angular2html
import timewalk as tw
from timewalk.strategy_classes import *

bt = tw.BackTester()
results = (bt.load_data("TSLA", "1d")
 .run(RsiStrategy(rsi_window=20)))
```
BackTester().run() returns a Pandas dataframe with various details on the strategy
___
You can also implement your own strategies by implementing the IStrategy interface in your class:
```angular2html
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

# Run our strategy
bt.load_data("TSLA", "1d").run(MyRsiStrat(rsi_window=20))
```


