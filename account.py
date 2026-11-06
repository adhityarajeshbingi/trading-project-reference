# Reference: Kousik Hazra
#
# account.py -- holds the cash and shares, and says yes or no to every order.
# The desk (hand trades) and the engine (agent trades) both call it. It calls nothing.

FEE = 0.001


class Account:
    """Cash and shares, and the only code that changes them."""

    def __init__(self, cash=10000.0, shares=0.0):
        """Start an account with this cash and these shares.
        Takes cash (float), shares (float). Returns nothing."""
        self.cash = float(cash)
        self.shares = float(shares)

    def execute(self, action, amount, price):
        """Try one order at this price, with the 0.1% fee.
        Changes the cash and shares only if the order is accepted.
        Takes action (str: "BUY", "SELL" or "HOLD"), amount (int or float; -1 = as many
        as possible), price (float). Returns str: "ACCEPT" or a "REJECT ..." message."""
        # 1. HOLD does nothing.
        if action == "HOLD":
            return "ACCEPT"

        # 2. Anything else that is not BUY or SELL is a mistake in the caller.
        if action != "BUY" and action != "SELL":
            raise ValueError("Unknown action: " + str(action))

        # 3. BUY
        if action == "BUY":
            if amount < 0:                           # -1: as many as the cash allows
                n = int(self.cash / (price * (1 + FEE)))
                if n * price * (1 + FEE) > self.cash:
                    n = n - 1                        # rounding guard
            else:
                n = amount
            if n == 0:
                return "ACCEPT"
            cost = n * price * (1 + FEE)
            if cost > self.cash:
                return "REJECT currency balance: " + str(round(self.cash, 2))
            self.cash = self.cash - cost
            self.shares = self.shares + n

        # 4. SELL
        if action == "SELL":
            if amount < 0:                           # -1: everything we hold
                n = self.shares
            else:
                n = amount
            if n == 0:
                return "ACCEPT"
            if n > self.shares:
                return "REJECT stock owned: " + str(round(self.shares, 2))
            self.cash = self.cash + n * price * (1 - FEE)
            self.shares = self.shares - n

        # 5. The rules can never leave us with negative money or shares.
        assert self.cash >= 0
        assert self.shares >= 0
        return "ACCEPT"

    def equity(self, price):
        """Work out what the account is worth at this price.
        Takes price (float). Returns float: cash + shares * price."""
        return self.cash + self.shares * price
