# Reference: Kousik Hazra
#
# engine.py -- runs one back-test. It gives the agent one day at a time and fills each
# order at the NEXT day's opening price, so the agent can never trade on a price it
# could not have known.

import math

from account import Account


class RunResult:
    """Hold the record of one run: what we were worth each day, and every trade.
    Holds data only; no methods."""
    # .ticker (str), .start_equity (float), .equity (list of float, one per day),
    # .trades (list of dict), .final_equity (float), .trade_count (int), .name (str, "")


class Simulator:
    """One back-test: an agent trading one market, day by day."""

    def __init__(self, market, agent, start_cash=10000.0, start_shares=0.0,
                 use_prices=True, use_news=True):
        """Store what one run needs. The two switches turn prices or news off.
        Takes market (MarketData), agent (TradingAgent), start_cash (float),
        start_shares (float), use_prices (bool), use_news (bool). Returns nothing."""
        self.market = market
        self.agent = agent
        self.start_cash = float(start_cash)
        self.start_shares = float(start_shares)
        self.use_prices = use_prices
        self.use_news = use_news

    def run(self):
        """Run the agent over every day; fill each order at the next day's open.
        Takes nothing. Returns RunResult."""
        market = self.market
        account = Account(self.start_cash, self.start_shares)
        start_equity = self.start_cash + self.start_shares * market.bar(0)["close"]
        equity = [start_equity]
        trades = []
        last_response = None

        for t in range(market.num_days() - 1):       # the last day's order could never fill
            bar = market.bar(t) if self.use_prices else None
            headlines = market.headlines(t) if self.use_news else None
            order = self.agent.decide(bar, headlines, account.cash, account.shares,
                                      last_response)
            if not is_valid(order):
                order = ("HOLD", 0)                  # a broken order counts as HOLD

            open_price = market.bar(t + 1)["open"]   # tomorrow's open: no look-ahead
            shares_before = account.shares
            last_response = account.execute(order[0], order[1], open_price)
            if account.shares != shares_before:
                trades.append({"day": t + 1, "action": order[0],
                               "shares": abs(account.shares - shares_before),
                               "price": open_price})
            equity.append(account.equity(market.bar(t + 1)["close"]))

        assert len(equity) == market.num_days()

        result = RunResult()
        result.ticker = market.ticker
        result.start_equity = start_equity
        result.equity = equity
        result.trades = trades
        result.final_equity = equity[-1]
        result.trade_count = len(trades)
        result.name = ""
        return result


def is_valid(order):
    """Check the agent's order is a pair: a known action and a number.
    Takes order (anything). Returns bool."""
    if not isinstance(order, (tuple, list)) or len(order) != 2:
        return False
    if order[0] not in ("BUY", "SELL", "HOLD"):
        return False
    if isinstance(order[1], (str, bool)):
        return False
    try:
        return math.isfinite(float(order[1]))      # also accepts numpy numbers
    except (TypeError, ValueError):
        return False
