# Reference: Kousik Hazra
#
# check_engine.py -- a fake 5-day market and a fake agent that always says ("BUY", -1).
# Run: python check_engine.py

from engine import Simulator, is_valid


class FakeMarket:
    """Five days of made-up prices, with the same methods as MarketData."""
    def __init__(self):
        """Takes nothing. Returns nothing."""
        self.ticker = "FAKE"
        self.bars = [{"open": 10.0, "high": 10.0, "low": 10.0, "close": 10.0, "volume": 1.0},
                     {"open": 20.0, "high": 21.0, "low": 19.0, "close": 21.0, "volume": 1.0},
                     {"open": 22.0, "high": 23.0, "low": 21.0, "close": 23.0, "volume": 1.0},
                     {"open": 24.0, "high": 25.0, "low": 23.0, "close": 25.0, "volume": 1.0},
                     {"open": 26.0, "high": 27.0, "low": 25.0, "close": 27.0, "volume": 1.0}]

    def num_days(self):
        """Takes nothing. Returns int."""
        return len(self.bars)

    def bar(self, day):
        """Takes day (int). Returns dict."""
        return self.bars[day]

    def headlines(self, day):
        """Takes day (int). Returns []."""
        return []


class AlwaysBuy:
    """A fake agent that always asks to buy as much as it can."""
    def decide(self, bar, headlines, cash, shares, last_response):
        """Takes the day's inputs. Returns ("BUY", -1)."""
        return ("BUY", -1)


result = Simulator(FakeMarket(), AlwaysBuy(), 1000.0, 0.0).run()

# One equity value per day
assert len(result.equity) == 5
assert result.equity[0] == 1000.0

# The first trade is on day 1, at day 1's OPEN (20.0), not day 0's close
assert result.trades[0]["day"] == 1
assert result.trades[0]["price"] == 20.0

# By hand: 1000 / (20 * 1.001) = 49.95 -> 49 shares, costing 49 * 20.02 = 980.98.
# Cash left 19.02, too little for a share later. Final equity = 19.02 + 49 * 27.
assert result.trades[0]["shares"] == 49.0
assert result.trade_count == 1
assert round(result.final_equity, 2) == round(1000 - 49 * 20 * 1.001 + 49 * 27.0, 2)
assert round(result.final_equity, 2) == 1342.02

# A broken order counts as HOLD
assert is_valid(("BUY", 5))
assert is_valid(["SELL", -1])
assert not is_valid(("buy", 5))
assert not is_valid(("BUY", "5"))
assert not is_valid("HOLD")
assert not is_valid(None)

print("All tests passed")
