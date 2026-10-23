# desk.py -- the trading desk: the text menu a person uses. Start the program here:
#     python3 desk.py          (no arguments needed; on Windows: python desk.py)
# Reference: Adhitya <surname>
#
# The desk keeps one SESSION: a loaded market, the current day, and an account. Every
# menu option works on that session. Manual trades fill at today's close; the agent's
# orders fill at tomorrow's open (the brief, section 10). The market data is read from
# data/training/ beside this file, as given.

import copy

import analytics
import engine
import market_data
import storage
from agent import TradingAgent

DATA_FOLDER = market_data.DEFAULT_FOLDER

MENU = """
========== Glacial Pace Capital trading desk ==========
  [1] Load dataset             [2] Set starting cash/shares
  [3] Step one day             [4] Manual buy
  [5] Manual sell              [6] Run agent to end
  [7] Show price chart         [8] Show equity + drawdown
  [9] Save / load              [0] Quit
======================================================="""


def ask(prompt):
    """input() that never crashes: Ctrl-D, Ctrl-C or closed input counts as 'quit'."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "0"


def ask_number(prompt, default):
    """A number typed by the user, or the default on Enter. None (with a message) if bad."""
    text = ask(prompt + " [" + str(default) + "]: ")
    if text == "":
        return default
    try:
        return float(text)
    except ValueError:
        print("  '" + text + "' is not a number; nothing changed.")
        return None


def money(value):
    return str(round(value, 2))


class Desk:
    def __init__(self):
        self.start_cash = engine.START_CASH
        self.start_shares = 0.0
        self.ticker = None
        self.session = None         # an engine.Simulator: the market, the day, the account
        self.last_run = None        # the latest agent run (a copy that went to the end)
        self.unsaved_run = None     # (name, final equity, trades), until [9] saves it
        self.chart_run = False      # True: the charts show the agent run, not the session

    # --- what the user sees after every action ---------------------------------------------
    def show_status(self):
        if self.session is None:
            print("  no dataset loaded | cash " + money(self.start_cash)
                  + " | shares " + str(self.start_shares))
            return
        s = self.session
        print("  day " + str(s.day) + "/" + str(s.last_day()) + " | price " + money(s.close())
              + " | cash " + money(s.account.cash) + " | shares " + str(s.account.shares)
              + " | equity " + money(s.account.equity(s.close())))
        print("  last event: " + s.last_event)

    def need_dataset(self):
        if self.session is None:
            print("  Load a dataset first (option 1).")
            return False
        return True

    def start_session(self, bars, news):
        account = engine.Account(self.start_cash, self.start_shares)
        self.session = engine.Simulator(bars, news, account)
        self.last_run = None
        self.chart_run = False

    # --- [1] and [2] ------------------------------------------------------------------------
    def load_dataset(self):
        ticker = ask("  Ticker (e.g. VOLT, ZNTH, NOVA, QBIT): ").upper()
        if ticker == "":
            print("  No ticker given; nothing changed.")
            return
        try:
            bars, news = market_data.load_market(DATA_FOLDER, ticker)
        except FileNotFoundError:
            print("  There is no " + DATA_FOLDER + ticker + ".csv. Check the ticker, and "
                  "that the data is in " + DATA_FOLDER + ".")
            return
        except (ValueError, KeyError) as error:
            print("  " + ticker + ".csv could not be read: " + repr(error))
            return
        if len(bars) < 2:
            print("  " + ticker + " has fewer than two days of prices.")
            return
        self.ticker = ticker
        self.start_session(bars, news)
        print("  Loaded " + ticker + " (" + str(len(bars)) + " days).")

    def set_balances(self):
        cash = ask_number("  Starting cash", self.start_cash)
        if cash is None:
            return
        shares = ask_number("  Starting shares", self.start_shares)
        if shares is None:
            return
        if cash < 0 or shares < 0:
            print("  Balances cannot be negative; nothing changed.")
            return
        self.start_cash, self.start_shares = cash, shares
        if self.session is None:
            print("  Set. They apply when you load a dataset.")
        else:
            self.start_session(self.session.bars, self.session.news)
            print("  Set, and the session restarted at day 0.")

    # --- [3], [4] and [5]: the session, by hand ---------------------------------------------
    def step_day(self):
        if not self.need_dataset():
            return
        if not self.session.step():
            print("  Already at the last day.")
        self.chart_run = False

    def manual_trade(self, action):
        if not self.need_dataset():
            return
        word = "buy" if action == "BUY" else "sell"
        amount = ask_number("  How many shares to " + word + " (-1 = all/max)", -1)
        if amount is None:
            return
        if not engine.is_valid_order((action, amount)):
            print("  That is not a usable number of shares.")
            return
        print("  -> " + self.session.manual_trade(action, amount))
        self.chart_run = False

    def manual_buy(self):
        self.manual_trade("BUY")

    def manual_sell(self):
        self.manual_trade("SELL")

    # --- [6] the agent ----------------------------------------------------------------------
    def run_agent(self):
        """Run the agent from the session's day and balances to the end, on a copy, so
        the session itself stays where it is and can be traded on or run again."""
        if not self.need_dataset():
            return
        if self.session.day >= self.session.last_day():
            print("  Already at the last day: there is nothing left to run.")
            return
        run = copy.deepcopy(self.session)
        error = run.run_agent(TradingAgent)
        if error is not None:
            print("  The agent stopped early: " + error)
        summary = analytics.summarize(run.equity)
        trades = len(run.trades) - len(self.session.trades)
        name = "TradingAgent on " + self.ticker
        print("  Ran " + name + ":")
        print("    final equity : " + money(summary["final_equity"]))
        print("    total return : " + str(round(summary["total_return_pct"], 1)) + "%")
        print("    sharpe-like  : " + str(round(summary["sharpe_like"], 3)))
        print("    max drawdown : " + str(round(summary["max_drawdown_pct"], 1)) + "%")
        print("    trades       : " + str(trades))
        print("  The charts now show this run; [9] saves it to the leaderboard.")
        self.last_run = run
        self.unsaved_run = (name, summary["final_equity"], trades)
        self.chart_run = True

    # --- [7] and [8] the charts -------------------------------------------------------------
    def charted(self):
        """(simulator, title) of what the charts show: the latest agent run if that was
        the last thing done, otherwise the session so far."""
        if self.chart_run and self.last_run is not None:
            return self.last_run, "TradingAgent on " + self.ticker
        return self.session, "session on " + self.ticker

    def price_chart(self):
        if not self.need_dataset():
            return
        sim, title = self.charted()
        print("  Showing the price chart; close its window to go on.")
        analytics.show_price_chart(sim.bars[:len(sim.equity)], sim.trades, title)

    def equity_charts(self):
        if not self.need_dataset():
            return
        sim, title = self.charted()
        if len(sim.equity) < 2:
            print("  Only one day so far: step forward or run the agent first.")
            return
        summary = analytics.summarize(sim.equity)
        print("  " + title + ": return " + str(round(summary["total_return_pct"], 1))
              + "%, max drawdown " + str(round(summary["max_drawdown_pct"], 1))
              + "%, sharpe-like " + str(round(summary["sharpe_like"], 3)))
        print("  Showing the equity curve, then the drawdown; close each window to go on.")
        analytics.show_equity_and_drawdown(sim.equity, title)

    # --- [9] saving and loading -------------------------------------------------------------
    def save_or_load(self):
        choice = ask("  [s]ave or [l]oad? ").lower()
        if choice == "s":
            self.save()
        elif choice == "l":
            self.load()
        else:
            print("  Please type s or l.")

    def save(self):
        if not self.need_dataset():
            return
        try:
            storage.save_session(self.ticker, self.session)
            print("  Saved the session to " + storage.SESSION_FILE + ".")
            if self.unsaved_run is None:
                print("  No new agent run to save; the leaderboard is unchanged.")
                return
            name, final_equity, trades = self.unsaved_run
            storage.save_result(name, final_equity, trades)
            storage.write_leaderboard()
            self.unsaved_run = None
            print("  Saved the run to " + storage.RESULTS_FILE + " and the leaderboard to "
                  + storage.LEADERBOARD_FILE + ".")
        except OSError as error:
            print("  Could not write the file: " + repr(error))

    def load(self):
        try:
            saved = storage.load_session()
            bars, news = market_data.load_market(DATA_FOLDER, saved["ticker"])
        except FileNotFoundError as error:
            print("  Nothing to load: " + str(error.filename) + " is missing.")
            self.show_leaderboard()
            return
        except (ValueError, IndexError) as error:
            print("  " + storage.SESSION_FILE + " is damaged and was not loaded: " + str(error))
            return
        if saved["day"] > len(bars) - 1:
            print("  The saved day is past the end of " + saved["ticker"] + "; not loaded.")
            return
        self.ticker = saved["ticker"]
        self.start_session(bars, news)
        self.session.account = engine.Account(saved["cash"], saved["shares"])
        self.session.day = saved["day"]
        self.session.equity = saved["equity"]
        self.session.trades = saved["trades"]
        if "event" in saved:
            self.session.last_event = saved["event"]
        print("  Loaded session: " + self.ticker + " day " + str(saved["day"]) + ".")
        self.show_status()
        self.show_leaderboard()

    def show_leaderboard(self):
        entries = storage.load_leaderboard()
        print("  Leaderboard, best final equity first:")
        if len(entries) == 0:
            print("    (empty: run the agent, then save)")
        for rank, name, final_equity in entries[:10]:
            print("    " + str(rank) + ". " + name + " " + money(final_equity))

    # --- the menu loop ----------------------------------------------------------------------
    def run(self):
        print("Welcome. Starting cash " + str(self.start_cash) + ", shares "
              + str(self.start_shares) + ".")
        actions = {"1": self.load_dataset, "2": self.set_balances, "3": self.step_day,
                   "4": self.manual_buy, "5": self.manual_sell,
                   "6": self.run_agent, "7": self.price_chart, "8": self.equity_charts,
                   "9": self.save_or_load}
        choice = ""
        while choice != "0":
            print(MENU)
            choice = ask("  Choose: ")
            if choice in actions:
                actions[choice]()
                if choice != "9":           # load prints its own status
                    self.show_status()
            elif choice != "0":
                print("  Please type a number from 0 to 9.")
        if self.unsaved_run is not None:
            print("  (The last agent run was not saved.)")
        print("Goodbye.")


if __name__ == "__main__":
    Desk().run()
