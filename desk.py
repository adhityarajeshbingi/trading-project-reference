# Reference: Adhitya Rajesh Bingi
#
# desk.py -- the menu. Start it with: python desk.py
# Hand trades fill at today's close. The agent's trades fill at tomorrow's open (engine.py).

from account import Account
from agent import TradingAgent
from analytics import total_return, max_drawdown, sharpe_like
from analytics import plot_price_with_trades, plot_equity, plot_drawdown
from engine import Simulator
from market_data import MarketData
from storage import save_run, load_leaderboard


def main():
    """Run the menu until the user types 0.
    Takes nothing. Returns nothing."""
    market = None                 # MarketData, or None until a market is loaded
    start_cash = 10000.0
    start_shares = 0.0
    account = Account(start_cash, start_shares)
    day = 0
    last_event = "none"
    result = None                 # RunResult, or None until the agent has run
    metrics = None

    while True:
        show_menu()
        choice = input("Choose: ").strip()

        if choice == "0":
            print("Goodbye.")
            return

        elif choice == "1":
            ticker = input("Ticker (VOLT, ZNTH, NOVA, QBIT): ")
            try:
                market = MarketData(ticker)
                day = 0
                account = Account(start_cash, start_shares)   # a fresh start on the new market
                result = None             # an old run belongs to the old market
                print("Loaded " + market.ticker)
            except FileNotFoundError:
                print("No price file for that ticker")

        elif choice == "2":
            cash = ask_number("Cash: ")
            shares = ask_number("Shares: ")
            if cash is not None and shares is not None:
                if cash < 0 or shares < 0:
                    print("Cash and shares must be 0 or more")
                else:
                    start_cash = cash
                    start_shares = shares
                    account = Account(cash, shares)

        elif choice == "9":
            board = load_leaderboard()
            if len(board) == 0:
                print("No saved runs yet")
            for name, final_equity in board:
                print(name + "  " + str(round(final_equity, 2)))

        elif choice not in ("3", "4", "5", "6", "7", "8"):
            print("Please choose a number from 0 to 9")

        # Options 3 to 8 all need a market.
        elif market is None:
            print("Load a market first")

        elif choice == "3":
            if day == market.num_days() - 1:
                print("No more days")
            else:
                day = day + 1

        elif choice == "4" or choice == "5":
            action = "BUY" if choice == "4" else "SELL"
            n = ask_number("How many shares? ")
            if n is not None:
                if n < 1:
                    print("Amount must be at least 1")
                else:
                    reply = account.execute(action, int(n), market.bar(day)["close"])
                    last_event = action + " " + str(int(n)) + " -> " + reply

        elif choice == "6":
            result = Simulator(market, TradingAgent(), start_cash, start_shares).run()
            metrics = {"total_return": total_return(result.equity),
                       "max_drawdown": max_drawdown(result.equity),
                       "sharpe_like": sharpe_like(result.equity)}
            print("final equity: " + str(round(result.final_equity, 2)))
            print("total return: " + str(round(metrics["total_return"] * 100, 1)) + "%")
            print("max drawdown: " + str(round(metrics["max_drawdown"] * 100, 1)) + "%")
            print("sharpe-like:  " + str(round(metrics["sharpe_like"], 3)))
            print("trades:       " + str(result.trade_count))

        # Options 7 and 8 also need a run.
        elif result is None:
            print("Run the agent first")

        elif choice == "7":
            plot_price_with_trades(market.closes(), result.trades)
            plot_equity(result.equity)
            plot_drawdown(result.equity)

        elif choice == "8":
            name = input("Name for this run: ").strip().replace(",", " ")
            if name == "":
                print("The name can't be empty")
            else:
                save_run(name, result, metrics)
                print("Saved")

        print_status(market, day, account, last_event)


def show_menu():
    """Print the 10 menu options.
    Takes nothing. Returns nothing."""
    print()
    print("[1] Load market     [2] Set cash and shares")
    print("[3] Step one day    [4] Buy by hand")
    print("[5] Sell by hand    [6] Run agent")
    print("[7] Show charts     [8] Save run")
    print("[9] Leaderboard     [0] Quit")


def print_status(market, day, account, last_event):
    """Print one status line: day, price, cash, shares, equity, last order.
    Takes market (MarketData), day (int), account (Account), last_event (str).
    Returns nothing."""
    if market is None:
        print("no market | cash " + str(round(account.cash, 2))
              + " | shares " + str(account.shares) + " | last: " + last_event)
        return
    price = market.bar(day)["close"]
    print("day " + str(day) + "/" + str(market.num_days() - 1)
          + " | price " + str(price)
          + " | cash " + str(round(account.cash, 2))
          + " | shares " + str(account.shares)
          + " | equity " + str(round(account.equity(price), 2))
          + " | last: " + last_event)


def ask_number(prompt):
    """Ask the user for a number, and catch letters.
    Takes prompt (str). Returns float, or None if it isn't a number."""
    try:
        return float(input(prompt))
    except ValueError:
        print("Please type a number")
        return None


if __name__ == "__main__":
    main()
