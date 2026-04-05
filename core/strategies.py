import numpy as np
import pandas as pd


def sma_signal(prices, fast, slow):
    return (prices.rolling(fast).mean() > prices.rolling(slow).mean()).astype(int).shift(1)


def rsi_signal(prices, period=14, oversold=30, overbought=70):
    delta = prices.diff()
    avg_gain = delta.clip(lower=0).ewm(com=period - 1, min_periods=period).mean()
    avg_loss = (-delta).clip(lower=0).ewm(com=period - 1, min_periods=period).mean()
    rsi = 100 - (100 / (1 + avg_gain / avg_loss))
    pos, cur = pd.Series(0.0, index=prices.index), 0
    for i in range(len(rsi)):
        if np.isnan(rsi.iloc[i]):
            pos.iloc[i] = 0
            continue
        if cur == 0 and rsi.iloc[i] < oversold:
            cur = 1
        elif cur == 1 and rsi.iloc[i] > overbought:
            cur = 0
        pos.iloc[i] = cur
    return pos.shift(1), rsi


def apply_costs(log_returns, signal, cost_bps):
    trades = signal.diff().abs().fillna(0)
    return log_returns - trades * (cost_bps / 10000)


def strategy_returns(prices, sig):
    log_ret = np.log(prices / prices.shift(1))
    strat = (log_ret * sig).dropna()
    bh = log_ret.loc[strat.index]
    return strat, bh

