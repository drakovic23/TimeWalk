import pandas as pd
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Dict, List, Optional
from .feature_builder import FeatureBuilder


@dataclass
class StrategyConfig:
    """Class to hold strategy-specific parameters"""
    name: str
    parameters: Dict

class IStrategy(ABC):
    """Abstract base class for to be implemented by every strategy class"""

    def __init__(self, config: StrategyConfig):
        self.config = config
        self.required_features: List[str] = []

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def should_buy(self, row: pd.Series) -> bool:
        pass

    @abstractmethod
    def should_sell(self, row: pd.Series) -> bool:
        pass

    @abstractmethod
    def on_bar(self, row: pd.Series) -> None:
        pass

    @abstractmethod
    def prepare_features(self, builder: FeatureBuilder) -> FeatureBuilder:
        pass


class RsiStrategy(IStrategy):
    def __init__(self, oversold_threshold: float = 30, overbought_threshold: float = 70, rsi_window: int = 20, atr_window: int=0):
        self.buy_threshold = oversold_threshold
        self.sell_threshold = overbought_threshold
        config = StrategyConfig(
            name="RSI Strategy",
            parameters={
                "buy_threshold": oversold_threshold,
                "sell_threshold": overbought_threshold,
                "rsi_window": rsi_window,
                "atr_window": atr_window
            }
        )
        super().__init__(config)
        self.required_features = [f'rsi_{rsi_window}']

    def prepare_features(self, builder: FeatureBuilder) -> FeatureBuilder:
        ret = builder.with_rsi(self.config.parameters['rsi_window'])
        if self.config.parameters['atr_window'] > 0:
            ret.with_atr(self.config.parameters['atr_window'])
        return ret

    def name(self):
        return self.config.name

    # Not needed for this strategy
    def on_bar(self, bar):
        pass

    def should_buy(self, row: pd.Series):
        return row[self.required_features[0]] <= self.buy_threshold

    def should_sell(self, row: pd.Series):
        return row[self.required_features[0]] >= self.sell_threshold

class MacdStrategy(IStrategy):
    def __init__(self, fast_window:int = 26, short_window: int = 12, signal_window: int = 9, atr_window: int=0):
        self.fast_window = fast_window
        self.short_window = short_window
        self.signal_window = signal_window
        config = StrategyConfig(
            name="MACD Strategy",
            parameters={
                "fast_window": fast_window,
                "short_window": short_window,
                "signal_window": signal_window,
                "atr_window": atr_window
            }
        )
        super().__init__(config)
        self.required_features = [f'MACD_signal', 'MACD']

    def prepare_features(self, builder: FeatureBuilder) -> FeatureBuilder:
        ret = builder.with_macd(self.config.parameters['fast_window'], self.config.parameters['short_window'])
        if self.config.parameters['atr_window'] > 0:
            ret.with_atr(self.config.parameters['atr_window'])
        return ret

    def name(self):
        return self.config.name

    # Not needed for this strategy
    def on_bar(self, bar):
        pass

    def should_buy(self, row: pd.Series):
        if row[self.required_features[0]] > row[self.required_features[1]]:
            return True


    def should_sell(self, row: pd.Series):
        if row[self.required_features[0]] < row[self.required_features[1]]:
            return True
        pass
