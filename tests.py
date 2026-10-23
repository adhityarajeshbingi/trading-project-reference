# tests.py -- asserts that prove the account's rules.
# Reference: Tarun <surname>
#
# Run it with:   python3 tests.py      (on Windows: python tests.py)
# Every test is a function whose name starts with test_. A failed assert stops the run
# and names the test, so a broken rule cannot go unnoticed.

import agent
import analytics
import engine
import market_data
import storage


def close_to(a, b):
    return abs(a - b) < 1e-9


# --- the account ------------------------------------------------------------------------
def test_buy_charges_the_fee():
    account = engine.Account()
    assert account.execute(("BUY", 10), 25.0) == "ACCEPT"
    assert account.shares == 10
    assert close_to(account.cash, 10000 - 10 * 25 * 1.001)       # 250.25 spent


def test_buy_max_floors_after_the_fee():
    # The contract's worked example: $500 at $25 buys 19 shares, not 20.
    account = engine.Account(cash=500)
    assert account.execute(("BUY", -1), 25.0) == "ACCEPT"
    assert account.shares == 19
    assert close_to(account.cash, 500 - 19 * 25.025)


def test_any_negative_amount_means_max():
    account = engine.Account(cash=500)
    account.execute(("BUY", -7), 25.0)
    assert account.shares == 19


def test_buy_too_much_is_rejected_exactly_and_changes_nothing():
    account = engine.Account(cash=100)
    assert account.execute(("BUY", 10), 25.0) == "REJECT currency balance: 100.0"
    assert account.cash == 100 and account.shares == 0


def test_sell_too_much_is_rejected_exactly_and_changes_nothing():
    account = engine.Account(cash=0, shares=19)
    assert account.execute(("SELL", 20), 25.0) == "REJECT stock owned: 19.0"
    assert account.shares == 19 and account.cash == 0


def test_reject_number_parses_the_way_the_contract_says():
    reply = engine.Account(cash=0, shares=19).execute(("SELL", 20), 25.0)
    assert float(reply.split(": ")[1]) == 19.0


def test_sell_all_charges_the_fee():
    account = engine.Account(cash=0, shares=10)
    assert account.execute(("SELL", -1), 25.0) == "ACCEPT"
    assert account.shares == 0
    assert close_to(account.cash, 10 * 25 * 0.999)


def test_max_orders_with_nothing_to_do_are_accepted():
    account = engine.Account(cash=0, shares=0)
    assert account.execute(("BUY", -1), 25.0) == "ACCEPT"
    assert account.execute(("SELL", -1), 25.0) == "ACCEPT"
    assert account.execute(("HOLD", 0), 25.0) == "ACCEPT"


def test_order_validation():
    assert engine.is_valid_order(("BUY", 5))
    assert engine.is_valid_order(["SELL", -1])
    assert not engine.is_valid_order(("buy", 5))
    assert not engine.is_valid_order(("BUY", "5"))
    assert not engine.is_valid_order(("BUY", float("nan")))
    assert not engine.is_valid_order("HOLD")


def test_account_prints_its_balances():
    assert str(engine.Account(cash=500, shares=2)) == "cash 500.0 | shares 2.0"


# --- the simulator: two fill rules, no look-ahead -----------------------------------------------
BARS = [
    {"open": 10.0, "high": 11.0, "low": 9.0, "close": 10.0, "volume": 1.0},
    {"open": 12.0, "high": 13.0, "low": 11.0, "close": 13.0, "volume": 1.0},
    {"open": 14.0, "high": 15.0, "low": 13.0, "close": 15.0, "volume": 1.0},
]
NEWS = {0: ["TEST surge"], 2: ["TEST crash"]}


def new_simulator():
    return engine.Simulator(BARS, NEWS, engine.Account())


class BuyOneOnDayZero:
    """A test agent: buys 1 share on its first call and records what it was shown."""
    def __init__(self):
        self.seen = []

    def decide(self, bar, headlines, cash, shares, last_response):
        self.seen.append((bar, headlines, last_response))
        if len(self.seen) == 1:
            return ("BUY", 1)
        return ("HOLD", 0)


def test_manual_trade_fills_at_todays_close():
    sim = new_simulator()
    assert sim.manual_trade("BUY", 1) == "ACCEPT"
    assert close_to(sim.account.cash, 10000 - 10.0 * 1.001)      # day 0's close
    assert sim.trades == [(0, "BUY", 10.0)]


def test_agent_order_fills_at_the_next_open():
    sim = new_simulator()
    assert sim.run_agent(BuyOneOnDayZero) is None
    cash = 10000 - 12.0 * 1.001                                  # day 1's open
    assert close_to(sim.equity[1], cash + 1 * 13.0)
    assert close_to(sim.equity[2], cash + 1 * 15.0)
    assert sim.trades == [(1, "BUY", 12.0)]


def test_step_and_one_equity_value_per_day():
    sim = new_simulator()
    assert sim.step() and sim.step()
    assert not sim.step()                                        # already on the last day
    assert sim.day == 2 and len(sim.equity) == 3


def test_regimes_hide_the_right_inputs():
    bar, headlines = market_data.inputs_for_day(BARS, NEWS, 0, market_data.OHLCV_ONLY)
    assert bar is not None and headlines is None
    bar, headlines = market_data.inputs_for_day(BARS, NEWS, 0, market_data.NEWS_ONLY)
    assert bar is None and headlines == ["TEST surge"]
    bar, headlines = market_data.inputs_for_day(BARS, NEWS, 1, market_data.BOTH)
    assert bar is not None and headlines == []          # no news that day: empty, not None


def test_agent_never_sees_the_future():
    agents = []

    class Recording(BuyOneOnDayZero):
        def __init__(self):
            BuyOneOnDayZero.__init__(self)
            agents.append(self)

    new_simulator().run_agent(Recording)
    seen = agents[0].seen
    assert len(seen) == len(BARS) - 1                   # never asked on the last day
    for day in range(len(seen)):
        assert seen[day][0] == BARS[day]                # day t sees bar t, nothing later
    assert seen[0][2] is None and seen[1][2] == "ACCEPT"


def test_a_crashing_agent_is_reported_not_raised():
    class Crashes:
        def decide(self, bar, headlines, cash, shares, last_response):
            return 1 / 0
    assert "day 0" in new_simulator().run_agent(Crashes)


def test_restore_refuses_a_session_that_does_not_fit():
    sim = new_simulator()
    try:
        sim.restore(5, [10000.0] * 6, [], "none yet")       # day 5 of a 3-day market
        assert False, "restore should have refused"
    except ValueError:
        pass
    assert sim.day == 0                                     # nothing changed


# --- the data -------------------------------------------------------------------------------
def test_agent_lexicon_matches_the_course_file():
    # agent.py may not read files, so it carries its own copy of the lexicon. This
    # proves the copy matches sentiment_words.csv (needs the data in data/training/).
    scores = market_data.load_lexicon(market_data.DEFAULT_FOLDER)
    nonzero = {}
    for word in scores:
        if scores[word] != 0:
            nonzero[word] = scores[word]
    assert nonzero == agent.LEXICON


def test_prices_load_with_their_types():
    bars = market_data.load_prices(market_data.DEFAULT_FOLDER, "NOVA")
    assert len(bars) == 750
    assert bars[0] == {"open": 100.0, "high": 101.75, "low": 99.46, "close": 101.33,
                       "volume": 973514.0}                  # the dataset guide's first row


# --- the analytics --------------------------------------------------------------------------
def test_daily_returns():
    returns = analytics.daily_returns([100, 110, 99])
    assert len(returns) == 2
    assert close_to(returns[0], 0.10) and close_to(returns[1], -0.10)


def test_moving_average():
    assert analytics.moving_average([1, 2, 3, 4], 2) == [None, 1.5, 2.5, 3.5]


def test_drawdown_measures_from_the_best_so_far():
    values = analytics.drawdowns([100, 120, 90, 130])
    assert close_to(values[2], -0.25)                    # 90 is 25% below 120
    assert values[3] == 0.0


def test_the_three_numbers():
    summary = analytics.summarize([100, 120, 90, 110])
    assert close_to(summary["total_return_pct"], 10.0)
    assert close_to(summary["max_drawdown_pct"], 25.0)
    assert analytics.sharpe_like([0.0, 0.0, 0.0]) == 0.0


# --- saving and loading -----------------------------------------------------------------------
def test_session_round_trip():
    sim = new_simulator()
    sim.manual_trade("BUY", 1)
    sim.step()
    storage.save_session("TEST", sim, "test_session.txt")
    saved = storage.load_session("test_session.txt")
    assert saved["ticker"] == "TEST" and saved["day"] == 1
    assert saved["cash"] == sim.account.cash and saved["shares"] == 1.0
    assert saved["equity"] == sim.equity and saved["trades"] == sim.trades


def test_leaderboard_is_best_final_equity_first():
    out = open("test_results.txt", "w")                  # start from an empty file
    out.close()
    storage.save_result("low", 9000.0, 3, "test_results.txt")
    storage.save_result("high, with comma", 11000.0, 5, "test_results.txt")
    storage.write_leaderboard("test_results.txt", "test_leaderboard.txt")
    entries = storage.load_leaderboard("test_leaderboard.txt")
    assert entries[0] == (1, "high  with comma", 11000.0)    # comma cleaned, best first
    assert entries[1] == (2, "low", 9000.0)


def run_all():
    tests = []
    for name, value in list(globals().items()):
        if name.startswith("test_") and callable(value):
            tests.append((name, value))
    for name, test in tests:
        test()
        print("  ok  " + name)
    print(str(len(tests)) + " tests passed.")


if __name__ == "__main__":
    run_all()