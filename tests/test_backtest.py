import timewalk.yf_helper as yf_helper
import pytest
import pandas as pd
import numpy as np
import timewalk.feature_builder as fb

@pytest.fixture
def get_1d_sample_data() -> pd.DataFrame:
    return pd.read_csv("SPY_1d.csv")

@pytest.fixture
def get_1h_sample_data() -> pd.DataFrame:
    return pd.read_csv("SPY_1h.csv")

def test_get_ohlcv_data():
    spy_1d = yf_helper.get_ohlc_data('SPY','1d')
    spy_1h = yf_helper.get_ohlc_data('SPY','1h')
    assert isinstance(spy_1d, pd.DataFrame)
    assert isinstance(spy_1h, pd.DataFrame)
    assert 'Close' in spy_1d.columns
    assert 'Close' in spy_1h.columns
    assert 'Open' in spy_1d.columns
    assert 'Open' in spy_1h.columns
    assert spy_1d.shape[0] > 1000
    assert spy_1h.shape[0] > 720

def test_pct_chg_1d(get_1d_sample_data):
    fb.calc_pct_chg(get_1d_sample_data)
    assert 'pct_chg' in get_1d_sample_data.columns
    expected = 0.01003
    actual = get_1d_sample_data['pct_chg'].iloc[-1]
    np.testing.assert_almost_equal(actual, expected, decimal=4)

def test_pct_chg_1h(get_1h_sample_data):
    fb.calc_pct_chg(get_1h_sample_data)
    assert 'pct_chg' in get_1h_sample_data.columns
    actual = get_1h_sample_data['pct_chg'].iloc[-1]
    expected = -0.00091
    np.testing.assert_almost_equal(actual, expected, decimal=4)

def test_features_rsi_1d(get_1d_sample_data):
    rsi_1d = fb.FeatureBuilder(get_1d_sample_data).with_rsi(20).build()
    assert 'rsi_20' in rsi_1d.columns
    expected = 54.41704
    actual = rsi_1d['rsi_20'].iloc[-1]
    np.testing.assert_almost_equal(actual, expected, decimal=4)

def test_features_rsi_1h(get_1h_sample_data):
    rsi_1h = fb.FeatureBuilder(get_1h_sample_data).with_rsi(20).build()
    assert 'rsi_20' in rsi_1h.columns
    expected = 62.070027
    actual = rsi_1h['rsi_20'].iloc[-1]
    np.testing.assert_almost_equal(actual, expected, decimal=4)

def test_features_atr_1d(get_1d_sample_data):
    atr_1d = fb.FeatureBuilder(get_1d_sample_data).with_atr(20).build()
    assert 'ATR' in atr_1d.columns
    expected = 0.0128231045410383
    actual = atr_1d['ATR'].iloc[-1]
    np.testing.assert_almost_equal(actual,expected, decimal=4)

def test_features_atr_1h(get_1h_sample_data):
    atr_1d = fb.FeatureBuilder(get_1h_sample_data).with_atr(20).build()
    assert 'ATR' in atr_1d.columns
    expected = 0.00279972855390122
    actual = atr_1d['ATR'].iloc[-1]
    np.testing.assert_almost_equal(actual,expected, decimal=4)


