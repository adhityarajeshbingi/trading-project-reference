# Reference: Laveeza Sayed
#
# analytics.py -- the three numbers and the three charts. Lists in, numbers or lists out.
# Built by hand: no rolling, shift, pct_change, cumprod or plt.hist (library policy).

import numpy as np
import matplotlib.pyplot as plt


def daily_returns(values):
    """Work out each day's change: today / yesterday - 1.
    Takes values (list of float). Returns list of float, one shorter than values."""
    a = np.array(values, dtype=float)                # an array before we slice it
    returns = a[1:] / a[:-1] - 1
    result = []
    for r in returns:
        result.append(float(r))
    return result


def moving_average(values, window):
    """Average each run of `window` values, sliding forward one day at a time.
    Takes values (list of float), window (int). Returns list of float,
    len(values) - window + 1 long."""
    result = []
    for i in range(window, len(values) + 1):
        result.append(float(sum(values[i - window:i]) / window))
    return result


def total_return(equity):
    """Gain or loss over the whole run: (last - first) / first.
    Takes equity (list of float). Returns float, e.g. 0.45 for +45%."""
    return float((equity[-1] - equity[0]) / equity[0])


def drawdown_series(equity):
    """For each day, how far equity is below its best so far: (value - best) / best.
    Takes equity (list of float). Returns list of float, one per day, each 0 or below."""
    result = []
    best = equity[0]
    for value in equity:
        if value > best:
            best = value
        result.append(float((value - best) / best))
    return result


def max_drawdown(equity):
    """The worst drop from a high point.
    Takes equity (list of float). Returns float, 0 or below, e.g. -0.16 for a 16% drop."""
    return min(drawdown_series(equity))


def sharpe_like(equity):
    """Reward for the risk: the average daily return divided by its standard deviation.
    Takes equity (list of float). Returns float; 0.0 if the standard deviation is 0."""
    r = np.array(daily_returns(equity))
    if len(r) == 0 or r.std() == 0:
        return 0.0
    return float(r.mean() / r.std())


def plot_equity(equity):
    """Draw equity day by day, save equity.png, and show it.
    Takes equity (list of float). Returns nothing."""
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(equity)), equity)
    plt.title("Equity curve")
    plt.xlabel("day")
    plt.ylabel("equity (USD)")
    plt.savefig("equity.png")
    plt.show()
    plt.close()


def plot_drawdown(equity):
    """Draw the drawdown day by day, save drawdown.png, and show it.
    Takes equity (list of float). Returns nothing."""
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(equity)), drawdown_series(equity), color="firebrick")
    plt.title("Drawdown")
    plt.xlabel("day")
    plt.ylabel("fraction below best so far")
    plt.savefig("drawdown.png")
    plt.show()
    plt.close()


def plot_price_with_trades(closes, trades):
    """Draw the price as a grey line, buys as ^ and sells as v; save
    price_with_trades.png; show it.
    Takes closes (list of float), trades (list of dict). Returns nothing."""
    buy_days, buy_prices, sell_days, sell_prices = [], [], [], []
    for trade in trades:
        if trade["action"] == "BUY":
            buy_days.append(trade["day"])
            buy_prices.append(trade["price"])
        else:
            sell_days.append(trade["day"])
            sell_prices.append(trade["price"])
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(closes)), closes, color="gray", label="close")
    plt.scatter(buy_days, buy_prices, marker="^", color="green", label="buy", zorder=3)
    plt.scatter(sell_days, sell_prices, marker="v", color="red", label="sell", zorder=3)
    plt.title("Price with trades")
    plt.xlabel("day")
    plt.ylabel("price (USD)")
    plt.legend()
    plt.savefig("price_with_trades.png")
    plt.show()
    plt.close()
