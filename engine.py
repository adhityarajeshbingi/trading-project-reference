# engine.py -- the account and the simulator: the desk's authority over the money.
# Reference: Kousik <surname>
#
# The rules come from the brief (project document 01, sections 1 and 10) and the agent
# contract (project document 03, sections 4 to 6):
#   - a 0.1% fee on every buy and every sell
#   - an amount of -1 (or any negative) means "as much as possible"
#   - an order fills whole or not at all, with an exact REJECT string otherwise
#   - two fill rules: the AGENT's order on day t fills at the OPEN of day t+1 (no
#     look-ahead); a MANUAL trade fills at TODAY's close (the price on the board)
#   - equity = cash + shares * close

import math
import random

import numpy as np

import market_data

START_CASH = 10000.0
FEE = 0.001


class Account:
    """Cash and shares, and the only code that changes them."""

    def __init__(self, cash=START_CASH, shares=0.0):
        self.cash = float(cash)
        self.shares = float(shares)

    def equity(self, price):
        return self.cash + self.shares * price

    def __str__(self):
        return "cash " + str(round(self.cash, 2)) + " | shares " + str(self.shares)

    def buy(self, amount, price):
        cost_per_share = price * (1.0 + FEE)
        if amount < 0:                              # -1: as many as the cash covers
            amount = int(self.cash / cost_per_share)
            if amount * cost_per_share > self.cash:     # a rounding edge: one too many
                amount = amount - 1
        if amount <= 0:
            return "ACCEPT"                         # nothing to buy is not an error
        cost = amount * cost_per_share
        if cost > self.cash:
            return "REJECT currency balance: " + str(round(self.cash, 2))
        self.cash = self.cash - cost
        self.shares = self.shares + amount
        return "ACCEPT"

    def sell(self, amount, price):
        if amount < 0:                              # -1: everything we hold
            amount = self.shares
        if amount <= 0:
            return "ACCEPT"
        if amount > self.shares:
            return "REJECT stock owned: " + str(round(self.shares, 2))
        self.cash = self.cash + amount * price * (1.0 - FEE)
        self.shares = self.shares - amount
        return "ACCEPT"

    def execute(self, order, price):
        """Carry out one well-formed order at this price; return the desk's reply."""
        action = order[0]
        amount = float(order[1])
        if action == "BUY":
            return self.buy(amount, price)
        if action == "SELL":
            return self.sell(amount, price)
        return "ACCEPT"                             # HOLD


def is_valid_order(order):
    """True for (action, amount) with a known action and a finite number."""
    if not isinstance(order, (tuple, list)) or len(order) != 2:
        return False
    if order[0] not in ("BUY", "SELL", "HOLD"):
        return False
    if isinstance(order[1], (str, bool)):
        return False
    try:
        return math.isfinite(float(order[1]))      # also accepts numpy numbers
    except (TypeError, ValueError, OverflowError):
        return False


class Simulator:
    """One market, one account, and where we are in time.

    equity[d] is the equity at the close of day d, so the list grows by one value each
    day we move forward. trades holds (day, action, price) for every order that filled,
    which is what the price chart marks."""

    def __init__(self, bars, news, account, regime=market_data.BOTH):
        self.bars = bars
        self.news = news
        self.account = account
        self.regime = regime
        self.day = 0
        self.equity = [account.equity(bars[0]["close"])]
        self.trades = []
        self.last_event = "none yet"

    def __str__(self):
        """The desk's status line: day, price, balances and equity."""
        return ("day " + str(self.day) + "/" + str(self.last_day())
                + " | price " + str(round(self.close(), 2)) + " | " + str(self.account)
                + " | equity " + str(round(self.account.equity(self.close()), 2)))

    def restore(self, day, equity, trades, last_event):
        """Put a saved session back (the desk's [9] load). ValueError if it cannot fit."""
        if day > self.last_day() or len(equity) != day + 1:
            raise ValueError("the saved day does not fit this market")
        self.day = day
        self.equity = equity
        self.trades = trades
        self.last_event = last_event

    def last_day(self):
        return len(self.bars) - 1

    def close(self):
        return self.bars[self.day]["close"]

    def record(self, action, before, price, day):
        """Note a trade if the order actually changed the account."""
        if (self.account.cash, self.account.shares) != before:
            self.trades.append((day, action, price))

    def step(self):
        """Move one day forward. False if we are already on the last day."""
        if self.day >= self.last_day():
            return False
        self.day = self.day + 1
        self.equity.append(self.account.equity(self.close()))
        return True

    def manual_trade(self, action, amount):
        """A trade typed at the desk fills at TODAY's close. Returns the desk's reply."""
        price = self.close()
        before = (self.account.cash, self.account.shares)
        reply = self.account.execute((action, amount), price)
        self.record(action, before, price, self.day)
        self.equity[self.day] = self.account.equity(price)     # today's value, after it
        self.last_event = action + " " + str(amount) + " at " + str(price) + " -> " + reply
        return reply

    def run_agent(self, agent_class):
        """Let a fresh agent trade from today to the end. Returns None, or an error.

        The agent decides on day t and its order fills at day t+1's open: it is only
        ever handed today's bar, so it cannot see the future."""
        np.random.seed(12345)           # the same seeds the course tools use, so a run
        random.seed(12345)              # from day 0 gives exactly selfcheck.py's numbers
        try:
            agent = agent_class()
        except Exception as error:
            return "the agent crashed while starting: " + repr(error)
        last_response = None
        while self.day < self.last_day():           # the last day's order could never fill
            bar, headlines = market_data.inputs_for_day(self.bars, self.news,
                                                        self.day, self.regime)
            try:
                order = agent.decide(bar, headlines, self.account.cash,
                                     self.account.shares, last_response)
            except Exception as error:
                return "the agent crashed on day " + str(self.day) + ": " + repr(error)
            if not is_valid_order(order):
                return ("the agent sent a malformed order on day " + str(self.day)
                        + ": " + repr(order))
            price = self.bars[self.day + 1]["open"]     # tomorrow's open
            before = (self.account.cash, self.account.shares)
            last_response = self.account.execute(order, price)
            self.record(order[0], before, price, self.day + 1)
            self.last_event = ("agent " + order[0] + " " + str(order[1]) + " on day "
                               + str(self.day) + " -> " + last_response)
            self.step()
        return None