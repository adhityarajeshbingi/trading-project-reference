# Reference: Tarun <full name>
#
# check_market_data.py -- the four training markets, plus a tiny test market with gaps.
# Run from the project folder: python check_market_data.py

from market_data import MarketData

# All four markets load, each with 750 days
for ticker in ["VOLT", "ZNTH", "NOVA", "QBIT"]:
    assert MarketData(ticker).num_days() == 750

# The first row of NOVA, exactly as the dataset guide prints it
nova = MarketData("NOVA")
assert nova.bar(0) == {"open": 100.0, "high": 101.75, "low": 99.46, "close": 101.33,
                       "volume": 973514.0}
assert nova.bar(750) is None
assert nova.bar(-1) is None
assert len(nova.closes()) == 750 and nova.closes()[0] == 101.33
assert nova.opens()[0] == 100.0
assert nova.has_news
assert len(nova.headlines(0)) > 0
assert nova.lexicon["surge"] == 1.0

# Ticker is cleaned: spaces and lower case are fine
assert MarketData("  nova ").ticker == "NOVA"

# An unknown ticker raises FileNotFoundError
try:
    MarketData("XXXX")
    assert False, "XXXX should raise FileNotFoundError"
except FileNotFoundError:
    pass

# Every training day has news, so a tiny test market checks the missing cases:
# two days of prices, no news file, no word list. Written beside this file.
out = open("TESTMKT.csv", "w")
out.write("day,open,high,low,close,volume\n0,10,11,9,10.5,100\n1,10.5,12,10,11,200\n")
out.close()
test = MarketData("TESTMKT", folder="")
assert test.num_days() == 2
assert test.has_news is False                   # no news file is not an error
assert test.headlines(0) == []                  # a day with no news gives []
assert test.lexicon == {}                       # no word list gives {}

print("All tests passed")
