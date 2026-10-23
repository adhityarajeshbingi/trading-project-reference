# analytics.py -- measuring a run and drawing it.
# Reference: Ayesha <surname>
#
# Everything is built from plain loops over lists. The pandas shortcuts that would do
# it for us (pct_change, rolling, shift, cumprod) and plt.hist are banned by the library
# policy (project document 02), because building these is the point.

import numpy as np
import matplotlib.pyplot as plt

AVERAGE_DAYS = 20       # the moving average drawn on the price chart


def daily_returns(equity):
    """Day-on-day returns as fractions: 0.01 means +1%. One fewer than equity values."""
    returns = []
    for i in range(1, len(equity)):
        if equity[i - 1] == 0:
            returns.append(0.0)
        else:
            returns.append(equity[i] / equity[i - 1] - 1)
    return returns


def moving_average(values, days):
    """The average of the last `days` values, for each day; None until there are enough.

    A running total keeps it to one pass: add today's value, take away the one that
    falls out of the window, instead of re-adding the whole window every day."""
    result = []
    total = 0.0
    for i in range(len(values)):
        total = total + values[i]
        if i >= days:
            total = total - values[i - days]
        if i >= days - 1:
            result.append(total / days)
        else:
            result.append(None)
    return result


def drawdowns(equity):
    """For each day, how far equity is below its best so far, as a fraction (0 or less)."""
    result = []
    best = equity[0]
    for value in equity:
        if value > best:
            best = value
        result.append(value / best - 1)
    return result


def sharpe_like(returns):
    """Mean daily return divided by its standard deviation (the brief, section 10).

    numpy's std, as the competition uses; 0 when there is nothing to divide by."""
    if len(returns) == 0:
        return 0.0
    values = np.array(returns)
    spread = np.std(values)
    if spread == 0:
        return 0.0
    return float(np.mean(values) / spread)


def summarize(equity):
    """The three numbers of a run, plus its final equity, as a dict."""
    return {
        "final_equity": equity[-1],
        "total_return_pct": (equity[-1] - equity[0]) / equity[0] * 100,
        "max_drawdown_pct": -min(drawdowns(equity)) * 100,
        "sharpe_like": sharpe_like(daily_returns(equity)),
    }


def show_price_chart(bars, trades, title):
    """Closing price with its moving average, a green triangle at each buy and a red
    one at each sell. plt.show() waits until the window is closed."""
    closes = []
    for bar in bars:
        closes.append(bar["close"])
    days = list(range(len(closes)))
    plt.figure(figsize=(10, 5))
    plt.plot(days, closes, color="gray", label="close")      # grey keeps it out of the way
    plt.plot(days, moving_average(closes, AVERAGE_DAYS),
             label=str(AVERAGE_DAYS) + "-day moving average")
    buy_days, buy_prices, sell_days, sell_prices = [], [], [], []
    for day, action, price in trades:
        if action == "BUY":
            buy_days.append(day)
            buy_prices.append(price)
        else:
            sell_days.append(day)
            sell_prices.append(price)
    plt.scatter(buy_days, buy_prices, marker="^", color="green", label="buy", zorder=3)
    plt.scatter(sell_days, sell_prices, marker="v", color="red", label="sell", zorder=3)
    plt.title("Price with trades: " + title)
    plt.xlabel("day")
    plt.ylabel("price (USD)")
    plt.legend()
    plt.show()


def show_equity_and_drawdown(equity, title):
    """The equity curve, then (once that window is closed) the drawdown."""
    days = list(range(len(equity)))
    plt.figure(figsize=(10, 5))
    plt.plot(days, equity)
    plt.title("Equity curve: " + title)
    plt.xlabel("day")
    plt.ylabel("equity (USD)")
    plt.show()

    plt.figure(figsize=(10, 5))
    plt.plot(days, drawdowns(equity), color="firebrick")
    plt.title("Drawdown: " + title)
    plt.xlabel("day")
    plt.ylabel("fraction below best so far")
    plt.show()