# Reference: Adhitya Rajesh Bingi
#
# desk.py -- the menu. It is the only file the user sees, and it calls every other file.
# Start it with:  python desk.py     (nothing typed after it)
#
# Hand trades fill at TODAY's close (the price on the board).
# The agent's trades fill at TOMORROW's open (inside engine.py).

from account import Account
from agent import TradingAgent
from analytics import (max_drawdown, plot_drawdown, plot_equity, plot_price_with_trades,
                       sharpe_like, total_return)
from engine import Simulator
from market_data import MarketData
from storage import load_leaderboard, save_run


def main():
    """Run the menu until the user types 0.
    Takes nothing. Returns nothing."""
    market = None                 # a MarketData, or None until a market is loaded
    start_cash = 10000.0
    start_shares = 0.0
    account = Account(start_cash, start_shares)     # for trading by hand
    day = 0
    last_event = "none yet"
    result = None                 # a RunResult, or None until the agent has run
    metrics = None

    print("Welcome. Starting cash " + str(start_cash) + ", shares " + str(start_shares) + ".")
    while True:
        show_menu()
        try:
            choice = input("Choose: ").strip()
        except EOFError:
            choice = "0"                             # input closed: treat as quit

        try:
            if choice == "0":
                print("Goodbye.")
                return

            elif choice == "1":
                loaded = load_market()
                if loaded is not None:
                    market = loaded
                    day = 0
                    account = Account(start_cash, start_shares)
                    result = None                    # a run belongs to one market
                    metrics = None
                    last_event = "loaded " + market.ticker

            elif choice == "2":
                balances = ask_balances()
                if balances is not None:
                    start_cash, start_shares = balances
                    account = Account(start_cash, start_shares)
                    last_event = "set cash " + str(start_cash) + ", shares " + str(start_shares)

            elif choice == "3":
                if market is None:
                    print("Load a market first")
                elif day >= market.num_days() - 1:
                    print("No more days")
                else:
                    day = day + 1

            elif choice == "4" or choice == "5":
                if market is None:
                    print("Load a market first")
                else:
                    action = "BUY" if choice == "4" else "SELL"
                    event = hand_trade(action, market, day, account)
                    if event is not None:
                        last_event = event

            elif choice == "6":
                if market is None:
                    print("Load a market first")
                else:
                    result, metrics = run_agent(market, start_cash, start_shares)
                    last_event = "ran TradingAgent on " + market.ticker

            elif choice == "7":
                if result is None:
                    print("Run the agent first")
                else:
                    print("Close each chart window to see the next one.")
                    plot_price_with_trades(market.closes(), result.trades)
                    plot_equity(result.equity)
                    plot_drawdown(result.equity)

            elif choice == "8":
                if result is None:
                    print("Run the agent first")
                elif save(result, metrics):
                    last_event = "saved run " + result.name

            elif choice == "9":
                show_leaderboard()

            else:
                print("Please choose a number from 0 to 9")

        except EOFError:
            print("Goodbye.")
            return

        print_status(market, day, account, last_event)


def show_menu():
    """Print the 10 menu options.
    Takes nothing. Returns nothing."""
    print()
    print("========== Glacial Pace Capital trading desk ==========")
    print("  [1] Load market            [2] Set cash and shares")
    print("  [3] Step one day           [4] Buy by hand")
    print("  [5] Sell by hand           [6] Run agent")
    print("  [7] Show charts            [8] Save run")
    print("  [9] Show leaderboard       [0] Quit")
    print("=======================================================")


def print_status(market, day, account, last_event):
    """Print one status line: day, price, cash, shares, equity, last order.
    Takes market (MarketData), day (int), account (Account), last_event (str).
    Returns nothing."""
    if market is None:
        print("no market loaded | cash " + str(round(account.cash, 2))
              + " | shares " + str(account.shares) + " | last: " + last_event)
        return
    price = market.bar(day)["close"]
    print("day " + str(day) + "/" + str(market.num_days() - 1)
          + " | price " + str(round(price, 2))
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


def load_market():
    """Option 1: ask for a ticker and load its market.
    Takes nothing. Returns MarketData, or None if there is no such market."""
    ticker = input("Ticker (e.g. VOLT, ZNTH, NOVA, QBIT): ")
    try:
        market = MarketData(ticker)
    except FileNotFoundError:
        print("No price file for that ticker")
        return None
    print("Loaded " + market.ticker + " (" + str(market.num_days()) + " days).")
    return market


def ask_balances():
    """Option 2: ask for the starting cash and shares, 0 or more.
    Takes nothing. Returns (float, float), or None if the input was bad."""
    cash = ask_number("Starting cash: ")
    if cash is None:
        return None
    shares = ask_number("Starting shares: ")
    if shares is None:
        return None
    if cash < 0 or shares < 0:
        print("Cash and shares must be 0 or more")
        return None
    return cash, shares


def hand_trade(action, market, day, account):
    """Options 4 and 5: buy or sell a whole number of shares at today's close.
    Takes action (str), market (MarketData), day (int), account (Account).
    Returns str, the event (e.g. "BUY 10 -> ACCEPT"), or None if the input was bad."""
    word = "buy" if action == "BUY" else "sell"
    n = ask_number("How many shares to " + word + "? ")
    if n is None:
        return None
    if n < 1:
        print("Amount must be at least 1")
        return None
    if n != int(n):
        print("Please type a whole number")
        return None
    reply = account.execute(action, int(n), market.bar(day)["close"])
    print("-> " + reply)
    return action + " " + str(int(n)) + " -> " + reply


def run_agent(market, start_cash, start_shares):
    """Option 6: run a new agent over the whole market and print the numbers.
    Takes market (MarketData), start_cash (float), start_shares (float).
    Returns (RunResult, dict): the run and its three numbers."""
    result = Simulator(market, TradingAgent(), start_cash, start_shares).run()
    metrics = {"total_return": total_return(result.equity),
               "max_drawdown": max_drawdown(result.equity),
               "sharpe_like": sharpe_like(result.equity)}
    print("Ran TradingAgent on " + market.ticker + ":")
    print("  final equity : " + str(round(result.final_equity, 2)))
    print("  total return : " + str(round(metrics["total_return"] * 100, 1)) + "%")
    print("  max drawdown : " + str(round(-metrics["max_drawdown"] * 100, 1)) + "%")
    print("  sharpe-like  : " + str(round(metrics["sharpe_like"], 3)))
    print("  trades       : " + str(result.trade_count))
    return result, metrics


def save(result, metrics):
    """Option 8: ask for a name and save the run.
    Takes result (RunResult), metrics (dict). Returns bool: True if it was saved."""
    name = input("Name for this run: ").strip().replace(",", " ")
    if name == "":
        print("The name can't be empty")
        return False
    save_run(name, result, metrics)
    result.name = name
    print("Saved to results.txt and leaderboard.txt.")
    return True


def show_leaderboard():
    """Option 9: print the saved runs, best final equity first.
    Takes nothing. Returns nothing."""
    board = load_leaderboard()
    print("Leaderboard, best final equity first:")
    if len(board) == 0:
        print("  (no saved runs yet)")
    rank = 1
    for name, final_equity in board:
        print("  " + str(rank) + ". " + name + "  " + str(round(final_equity, 2)))
        rank = rank + 1


if __name__ == "__main__":
    main()
