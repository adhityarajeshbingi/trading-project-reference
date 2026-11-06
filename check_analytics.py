# Reference: Laveeza Sayed
#
# check_analytics.py -- the three numbers and the two indicators. Run: python check_analytics.py

from analytics import (daily_returns, drawdown_series, max_drawdown, moving_average,
                       sharpe_like, total_return)

r = daily_returns([100, 110, 99])
assert len(r) == 2
assert round(r[0], 6) == 0.1 and round(r[1], 6) == -0.1

assert moving_average([1, 2, 3, 4, 5], 3) == [2.0, 3.0, 4.0]

assert round(total_return([100, 110, 99]), 6) == -0.01

d = drawdown_series([100, 110, 99])
assert d[0] == 0.0 and d[1] == 0.0 and round(d[2], 6) == -0.1

assert round(max_drawdown([100, 110, 99]), 6) == -0.1

assert sharpe_like([100, 110, 121]) == 0.0      # the same return every day: no spread

print("All tests passed")
