# Reference: Tarun <full name>
#
# check_account.py -- proves that account.py follows the rules. Run: python check_account.py
# Money is compared with round(x, 3), because floats aren't exact.

from account import Account

# BUY -1 buys as many whole shares as the cash allows, fee included: 500 / 25.025 -> 19
a = Account(500.0, 0.0)
assert a.execute("BUY", -1, 25.0) == "ACCEPT"
assert a.shares == 19.0
assert round(a.cash, 3) == 24.525

# Not enough cash: exact REJECT, nothing changes
a = Account(500.0, 0.0)
assert a.execute("BUY", 20, 25.0) == "REJECT currency balance: 500.0"
assert a.cash == 500.0 and a.shares == 0.0

# The cash in the message is rounded to the cent
a = Account(1234.567, 0.0)
assert a.execute("BUY", 100, 25.0) == "REJECT currency balance: 1234.57"
assert a.cash == 1234.567 and a.shares == 0.0

# Not enough shares: exact REJECT, nothing changes
a = Account(0.0, 19.0)
assert a.execute("SELL", 20, 25.0) == "REJECT stock owned: 19.0"
assert a.shares == 19.0 and a.cash == 0.0

# SELL -1 sells everything, fee taken off: 19 * 25 * 0.999
a = Account(0.0, 19.0)
assert a.execute("SELL", -1, 25.0) == "ACCEPT"
assert a.shares == 0.0
assert round(a.cash, 3) == 474.525

# HOLD changes nothing
a = Account(500.0, 3.0)
assert a.execute("HOLD", 0, 25.0) == "ACCEPT"
assert a.cash == 500.0 and a.shares == 3.0

# SELL -1 with nothing to sell is fine
a = Account(500.0, 0.0)
assert a.execute("SELL", -1, 25.0) == "ACCEPT"
assert a.cash == 500.0 and a.shares == 0.0

# An unknown action is a mistake in the caller
a = Account(500.0, 0.0)
try:
    a.execute("JUMP", 1, 25.0)
    assert False, "JUMP should raise ValueError"
except ValueError:
    pass
assert a.cash == 500.0 and a.shares == 0.0

# Equity is cash plus shares at the price
assert Account(100.0, 2.0).equity(25.0) == 150.0

print("All tests passed")
