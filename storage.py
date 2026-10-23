# storage.py -- saving and loading, all in plain text.
# Reference: Tarun <surname>
#
# Three files, written beside the program:
#   session.txt       where the desk is: market, day, balances, equity so far, trades
#   results.txt       one line per saved agent run:  name,final_equity,trades
#   leaderboard.txt   written again from results.txt on every save, best final equity
#                     first:  rank,name,final_equity   (the brief, section 1)

SESSION_FILE = "session.txt"
RESULTS_FILE = "results.txt"
LEADERBOARD_FILE = "leaderboard.txt"


def clean(text):
    """Commas separate the fields, so a name may not contain one."""
    return str(text).replace(",", " ").strip()


# --- the session ---------------------------------------------------------------------------
def save_session(ticker, simulator, filename=SESSION_FILE):
    """One 'key,value' line per setting, then one 'trade,day,action,price' per trade."""
    out = open(filename, "w")
    out.write("ticker," + ticker + "\n")
    out.write("day," + str(simulator.day) + "\n")
    out.write("cash," + str(simulator.account.cash) + "\n")
    out.write("shares," + str(simulator.account.shares) + "\n")
    out.write("event," + clean(simulator.last_event) + "\n")
    values = []
    for value in simulator.equity:
        values.append(str(value))
    out.write("equity," + ",".join(values) + "\n")
    for day, action, price in simulator.trades:
        out.write("trade," + str(day) + "," + action + "," + str(price) + "\n")
    out.close()


def load_session(filename=SESSION_FILE):
    """The saved session as a dict. Raises FileNotFoundError if there is none, and
    ValueError if the file is damaged."""
    session = {"trades": []}
    for line in open(filename, "r").readlines():
        parts = line.strip().split(",")
        if parts[0] == "ticker":
            session["ticker"] = parts[1]
        elif parts[0] == "day":
            session["day"] = int(parts[1])
        elif parts[0] == "cash":
            session["cash"] = float(parts[1])
        elif parts[0] == "shares":
            session["shares"] = float(parts[1])
        elif parts[0] == "event":
            session["event"] = ",".join(parts[1:])
        elif parts[0] == "equity":
            session["equity"] = []
            for value in parts[1:]:
                session["equity"].append(float(value))
        elif parts[0] == "trade":
            session["trades"].append((int(parts[1]), parts[2], float(parts[3])))
    for key in ("ticker", "day", "cash", "shares", "equity"):
        if key not in session:
            raise ValueError(filename + " has no '" + key + "' line")
    if len(session["equity"]) != session["day"] + 1:
        raise ValueError(filename + ": the equity list does not match the day")
    return session


# --- results and the leaderboard -------------------------------------------------------------
def save_result(name, final_equity, trades, filename=RESULTS_FILE):
    out = open(filename, "a")
    out.write(clean(name) + "," + str(round(final_equity, 2)) + "," + str(trades) + "\n")
    out.close()


def load_results(filename=RESULTS_FILE):
    """Every saved run as (final_equity, name, trades). A missing file has none."""
    try:
        lines = open(filename, "r").readlines()
    except FileNotFoundError:
        return []
    results = []
    for line in lines:
        parts = line.strip().split(",")
        if len(parts) == 3:
            try:
                results.append((float(parts[1]), parts[0], int(parts[2])))
            except ValueError:
                continue                    # skip a damaged line, keep the rest
    return results


def write_leaderboard(results_file=RESULTS_FILE, filename=LEADERBOARD_FILE):
    """Rebuild the leaderboard from every saved run, best final equity first."""
    # The supplement's recipe: [final, name] pairs sort by their first item, the final
    # equity, and reverse() then puts the best first.
    ranked = []
    for final_equity, name, trades in load_results(results_file):
        ranked.append([final_equity, name])
    ranked.sort()
    ranked.reverse()
    out = open(filename, "w")
    out.write("rank,name,final_equity\n")
    rank = 1
    for final_equity, name in ranked:
        out.write(str(rank) + "," + name + "," + str(final_equity) + "\n")
        rank = rank + 1
    out.close()


def load_leaderboard(filename=LEADERBOARD_FILE):
    """The leaderboard as (rank, name, final_equity), best first. Missing file: empty."""
    try:
        lines = open(filename, "r").readlines()
    except FileNotFoundError:
        return []
    entries = []
    for line in lines[1:]:                  # lines[0] is the header
        parts = line.strip().split(",")
        if len(parts) == 3:
            entries.append((int(parts[0]), parts[1], float(parts[2])))
    return entries