GROUP_CODE = "G18-DRL4"
# Group: Kousik Hazra, Laveeza Sayed, Adhitya Rajesh Bingi, Tarun <full name>
# Reference: Laveeza Sayed

# Strategy: "buy the dip".
# When the price falls well below its recent average, it often bounces back.
# So we buy when the price is 2% below its 10-day average,
# and sell when the price is back above that average.

WINDOW = 10          # how many days the average covers
DIP = 0.98           # buy when the close is below 98% of the average (2% below)


class TradingAgent:
    """Buys with all the cash on a dip below the 10-day average,
    and sells all the shares when the price is back above it."""

    def __init__(self):
        """Start with an empty memory of prices."""
        self.closes = []                  # every closing price seen so far

    def decide(self, bar, headlines, cash, shares, last_response):
        """Called once a day. Returns (action, amount)."""
        if bar is None:
            return ("HOLD", 0)            # news-only round: this agent reads prices only

        close = bar["close"]
        self.closes.append(close)         # remember today's price

        if len(self.closes) < WINDOW:
            return ("HOLD", 0)            # days 0 to 8: not enough prices yet

        average = self.moving_average()

        if close < average * DIP and shares == 0:
            return ("BUY", -1)            # dip: buy with all the cash
        if close > average and shares > 0:
            return ("SELL", -1)           # recovered: sell all the shares
        return ("HOLD", 0)                # otherwise do nothing

    def moving_average(self):
        """Average of the last WINDOW closing prices, today included."""
        recent = self.closes[-WINDOW:]
        return sum(recent) / WINDOW
