# Reference: Tarun <full name>
#
# market_data.py -- reads one market's files once, then answers questions about any day.
# The desk and the engine call it. It never changes, cleans or re-saves the data files.

import numpy as np
import pandas as pd

DATA_DIR = "data/training/"


class MarketData:
    """One market's prices, news and word list, read once from the data files."""

    def __init__(self, ticker, folder=DATA_DIR):
        """Read one market's price, news and word-list files into memory.
        Takes ticker (str), folder (str). Returns nothing."""
        self.ticker = ticker.strip().upper()

        # Prices: one dict per day. Each column becomes a numpy array first, then floats.
        path = folder + self.ticker + ".csv"
        try:
            table = pd.read_csv(path)
        except FileNotFoundError:
            raise FileNotFoundError("No price file: " + path)
        opens = np.array(table["open"])
        highs = np.array(table["high"])
        lows = np.array(table["low"])
        closes = np.array(table["close"])
        volumes = np.array(table["volume"])
        self.bars = []
        for i in range(len(closes)):
            self.bars.append({"open": float(opens[i]), "high": float(highs[i]),
                              "low": float(lows[i]), "close": float(closes[i]),
                              "volume": float(volumes[i])})

        # News: day -> list of headlines. A missing news file is not an error.
        self.news = {}
        self.has_news = True
        try:
            lines = open(folder + self.ticker + "_news.txt").readlines()
        except FileNotFoundError:
            self.has_news = False
            lines = []
        for line in lines[1:]:                       # lines[0] is the header
            parts = line.strip().split(",", 1)       # split once: a headline may hold a comma
            if len(parts) < 2:
                continue
            day = int(parts[0])
            if day not in self.news:
                self.news[day] = []
            self.news[day].append(parts[1])

        # Word list: word -> score. A missing file gives {}.
        self.lexicon = {}
        try:
            lines = open(folder + "sentiment_words.csv").readlines()
        except FileNotFoundError:
            lines = []
        for line in lines[1:]:                       # lines[0] is the header
            parts = line.strip().split(",")
            if len(parts) == 2:
                self.lexicon[parts[0]] = float(parts[1])

    def num_days(self):
        """Count the days in the price file.
        Takes nothing. Returns int, e.g. 750."""
        return len(self.bars)

    def bar(self, day):
        """Give one day's prices.
        Takes day (int). Returns dict (open, high, low, close, volume), or None if the
        day is outside the data."""
        if day < 0 or day >= len(self.bars):
            return None
        return self.bars[day]

    def headlines(self, day):
        """Give one day's news.
        Takes day (int). Returns list of str; [] if there is no news that day."""
        if day in self.news:
            return list(self.news[day])              # a copy, so nobody changes ours
        return []

    def closes(self):
        """Give every closing price, for the charts.
        Takes nothing. Returns list of float, one per day."""
        result = []
        for bar in self.bars:
            result.append(bar["close"])
        return result

    def opens(self):
        """Give every opening price.
        Takes nothing. Returns list of float, one per day."""
        result = []
        for bar in self.bars:
            result.append(bar["open"])
        return result
