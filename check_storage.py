# Reference: Tarun <full name>
#
# check_storage.py -- saving and loading, on test files so the real ones aren't touched.
# Run: python check_storage.py

import storage

storage.RESULTS_FILE = "test_results.txt"
storage.LEADERBOARD_FILE = "test_leaderboard.txt"
open(storage.RESULTS_FILE, "w").close()          # empty both first
open(storage.LEADERBOARD_FILE, "w").close()


class FakeResult:
    """A small stand-in for a RunResult."""
    def __init__(self, ticker, final_equity, trade_count):
        """Takes ticker (str), final_equity (float), trade_count (int). Returns nothing."""
        self.ticker = ticker
        self.start_equity = 10000.0
        self.final_equity = final_equity
        self.trade_count = trade_count
        self.name = ""


metrics = {"total_return": 0.1, "max_drawdown": -0.05, "sharpe_like": 0.02}
storage.save_run("low run", FakeResult("NOVA", 9000.0, 3), metrics)
storage.save_run("high, run", FakeResult("ZNTH", 14525.6, 12), metrics)

# Both runs load back
results = storage.load_results()
assert len(results) == 2
assert results[0]["name"] == "low run" and results[0]["final_equity"] == 9000.0
assert results[1]["name"] == "high  run"        # the comma became a space
assert results[1]["trade_count"] == 12

# The leaderboard is best first
board = storage.load_leaderboard()
assert board == [("high  run", 14525.6), ("low run", 9000.0)]

# A damaged line is skipped, not a crash
out = open(storage.RESULTS_FILE, "a")
out.write("this line is broken\n")
out.close()
assert len(storage.load_results()) == 2

# No file at all gives []
storage.RESULTS_FILE = "no_such_file.txt"
storage.LEADERBOARD_FILE = "no_such_file.txt"
assert storage.load_results() == []
assert storage.load_leaderboard() == []

print("All tests passed")
