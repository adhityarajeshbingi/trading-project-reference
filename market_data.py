# market_data.py -- loading the data.
# Reference: Tarun <surname>
#
# Reads the course files exactly as given, every time (project document 06): never a
# converted or edited copy. A market is two files in one folder:
#   <TICKER>.csv        day,open,high,low,close,volume   (one row per day)
#   <TICKER>_news.txt   day,headline                      (any number per day)

import pandas as pd

DEFAULT_FOLDER = "data/training/"
TRAINING_TICKERS = ["VOLT", "ZNTH", "NOVA", "QBIT"]

# The three ways a market is run (project document 03, section 3).
OHLCV_ONLY = "OHLCV-only"
NEWS_ONLY = "news-only"
BOTH = "OHLCV+news"
REGIMES = [OHLCV_ONLY, NEWS_ONLY, BOTH]


def load_prices(folder, ticker):
    """A list of bar dicts, one per day: {"open":.., "high":.., "low":.., "close":.., "volume":..}."""
    frame = pd.read_csv(folder + ticker + ".csv")
    # Whole columns to plain lists once, rather than reading the frame row by row.
    opens = list(frame["open"])
    highs = list(frame["high"])
    lows = list(frame["low"])
    closes = list(frame["close"])
    volumes = list(frame["volume"])
    bars = []
    for i in range(len(closes)):
        bars.append({"open": float(opens[i]), "high": float(highs[i]),
                     "low": float(lows[i]), "close": float(closes[i]),
                     "volume": float(volumes[i])})
    return bars


def load_news(folder, ticker):
    """A dict from day number to that day's list of headlines.

    A day with no news is simply missing from the dict. A market with no news file at
    all gives an empty dict, so the program still runs on prices alone."""
    news = {}
    try:
        lines = open(folder + ticker + "_news.txt", encoding="utf-8").readlines()
    except FileNotFoundError:
        return news
    for line in lines[1:]:                  # lines[0] is the header "day,headline"
        line = line.strip()
        if line == "":
            continue
        parts = line.split(",", 1)          # split once: a headline may hold a comma
        day = int(parts[0])
        if day not in news:
            news[day] = []
        news[day].append(parts[1])
    return news


def load_lexicon(folder):
    """sentiment_words.csv as a dict from word to score."""
    scores = {}
    for line in open(folder + "sentiment_words.csv", encoding="utf-8").readlines()[1:]:
        parts = line.strip().split(",")
        if len(parts) == 2:
            scores[parts[0]] = float(parts[1])
    return scores


def load_market(folder, ticker):
    """(bars, news) for one ticker. Raises FileNotFoundError if the prices are missing."""
    return load_prices(folder, ticker), load_news(folder, ticker)


def inputs_for_day(bars, news, day, regime):
    """What the agent is shown on one day in one regime: (bar, headlines).

    OHLCV-only hides the news (headlines is None), news-only hides the prices (bar is
    None). A day with no headlines gives an empty list, not None, when news is on."""
    bar = bars[day]
    headlines = news.get(day, [])
    if regime == OHLCV_ONLY:
        headlines = None
    if regime == NEWS_ONLY:
        bar = None
    return bar, headlines
