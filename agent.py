# agent.py -- our competition entry. Reference member: Laveeza.
#
# What it trades on, in two sentences:
#   When it can read the news, it owns shares tomorrow only if today's headlines score
#   positive (80% of its money when it can see the price, all of it when it cannot).
#   With prices only, it holds 50% when the price is below its 20-day average and 15%
#   when above, and drops to 15% whenever it is 20% below its best equity so far.
#
# Rules this file must keep (project document 03): import only numpy, pandas, math,
# random; never import our other files; never read or write a file.

GROUP_CODE = "G18-VMLQ"       # <- replace with the group code from the email
# Group: Kousik <surname>, Tarun <surname>, Laveeza <surname>, Adhitya <surname>, Ayesha <surname>
# Reference: Laveeza <surname>


# The course lexicon (sentiment_words.csv), copied in because agent.py may not read
# files. The 12 neutral words score 0, so they are left out: looking them up adds 0.
LEXICON = {
    "surge": 1, "rally": 1, "soar": 1, "gain": 1, "bullish": 1, "breakout": 1,
    "upgrade": 1, "beat": 1, "record": 1, "boom": 1, "jump": 1, "optimism": 1,
    "inflow": 1, "adoption": 1,
    "crash": -1, "plunge": -1, "slump": -1, "loss": -1, "bearish": -1, "selloff": -1,
    "downgrade": -1, "miss": -1, "fear": -1, "dump": -1, "drop": -1, "panic": -1,
    "outflow": -1, "ban": -1,
}

NEWS_SHARE = 0.8        # share of our money in shares after good news (price known)
DIP_SHARE = 0.5         # price-only: share held when the price is below its average
CALM_SHARE = 0.15       # price-only: share held otherwise (never 0, see document 03)
AVERAGE_DAYS = 20       # length of the moving average
BRAKE = 0.8             # price-only: below 80% of our best equity, hold only CALM_SHARE
MIN_TRADE = 0.05        # skip trades smaller than 5% of equity: the fee is not worth it
PRICE_BUFFER = 1.03     # we decide on today's close but fill at tomorrow's open


class TradingAgent:
    def __init__(self):
        self.closes = []            # every close we have seen, oldest first
        self.best_equity = 0.0      # the highest equity we have seen

    def decide(self, bar, headlines, cash, shares, last_response):
        if bar is not None:
            self.closes.append(bar["close"])
            equity = cash + shares * bar["close"]
            if equity > self.best_equity:
                self.best_equity = equity

        if headlines is not None:
            target = self.news_target(headlines)
        elif bar is not None:
            target = self.price_target(bar, cash, shares)
        else:
            return ("HOLD", 0)          # nothing to go on (never happens in practice)

        if target is None:
            return ("HOLD", 0)          # not enough history yet
        return self.order_for(target, bar, cash, shares)

    def mood(self, headlines):
        """Sum of the lexicon scores of every word in today's headlines."""
        total = 0
        for line in headlines:
            for mark in ":;,.!?":
                line = line.replace(mark, " ")     # "outlook:" -> "outlook"
            for word in line.lower().split():
                if word in LEXICON:
                    total = total + LEXICON[word]
        return total

    def news_target(self, headlines):
        """Share of our money to hold tomorrow, judged from today's news."""
        if self.mood(headlines) > 0:
            return NEWS_SHARE
        return 0.0                      # bad or neutral news: be out tomorrow

    def price_target(self, bar, cash, shares):
        """Share of our money to hold tomorrow, judged from prices only."""
        if len(self.closes) < AVERAGE_DAYS:
            return None
        recent = self.closes[len(self.closes) - AVERAGE_DAYS:]
        average = sum(recent) / AVERAGE_DAYS
        equity = cash + shares * bar["close"]
        if equity < BRAKE * self.best_equity:
            return CALM_SHARE           # losing: keep risk small until we recover
        if bar["close"] < average:
            return DIP_SHARE            # price dipped below normal: hold more
        return CALM_SHARE

    def order_for(self, target, bar, cash, shares):
        """Turn 'hold this share of our money' into one order."""
        if target == 0.0:
            if shares > 0:
                return ("SELL", -1)
            return ("HOLD", 0)

        if bar is None:                 # news-only: no price, so all in or nothing
            if shares == 0:
                return ("BUY", -1)
            return ("HOLD", 0)

        price = bar["close"]
        equity = cash + shares * price
        cost_per_share = price * 1.001 * PRICE_BUFFER
        wanted = int(equity * target / cost_per_share)
        change = wanted - shares
        if change > 0:
            affordable = int(cash / cost_per_share)
            if change > affordable:
                change = affordable
            if change * price > MIN_TRADE * equity:
                return ("BUY", change)
        if change < 0 and -change * price > MIN_TRADE * equity:
            return ("SELL", -change)
        return ("HOLD", 0)
