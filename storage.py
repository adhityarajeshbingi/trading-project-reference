# Reference: Tarun <full name>
#
# storage.py -- saves runs in plain text, so they are still there after a restart.
#   results.txt      one line per saved run:
#                    name,ticker,start_equity,final_equity,total_return,max_drawdown,sharpe_like,trade_count
#   leaderboard.txt  one line per saved run: name,final_equity, best first

RESULTS_FILE = "results.txt"
LEADERBOARD_FILE = "leaderboard.txt"


def save_run(name, result, metrics):
    """Save one run: add a line to results.txt, then rewrite leaderboard.txt, best first.
    Takes name (str), result (RunResult), metrics (dict). Returns nothing."""
    name = name.replace(",", " ")                    # commas separate the fields
    line = ",".join([name,
                     result.ticker,
                     str(round(result.start_equity, 2)),
                     str(round(result.final_equity, 2)),
                     str(round(metrics["total_return"], 4)),
                     str(round(metrics["max_drawdown"], 4)),
                     str(round(metrics["sharpe_like"], 4)),
                     str(result.trade_count)])
    out = open(RESULTS_FILE, "a")
    out.write(line + "\n")
    out.close()

    # The leaderboard is rebuilt from every saved run (time-series supplement recipe).
    rows = []
    for run in load_results():
        rows.append([run["final_equity"], run["name"]])
    rows.sort()
    rows.reverse()
    out = open(LEADERBOARD_FILE, "w")
    for final_equity, run_name in rows:
        out.write(run_name + "," + str(final_equity) + "\n")
    out.close()


def load_leaderboard():
    """Read leaderboard.txt back.
    Takes nothing. Returns list of (str, float): (name, final equity), best first;
    [] if no file."""
    try:
        lines = open(LEADERBOARD_FILE).readlines()
    except FileNotFoundError:
        return []
    board = []
    for line in lines:
        if line.strip() == "":
            continue
        parts = line.strip().split(",")
        try:
            if len(parts) != 2:
                raise ValueError("expected 2 fields")
            board.append((parts[0], float(parts[1])))
        except ValueError:
            print("Skipped a damaged leaderboard line: " + line.strip())
    return board


def load_results():
    """Read results.txt back.
    Takes nothing. Returns list of dict, one per saved run; [] if no file."""
    try:
        lines = open(RESULTS_FILE).readlines()
    except FileNotFoundError:
        return []
    results = []
    for line in lines:
        if line.strip() == "":
            continue
        parts = line.strip().split(",")
        try:
            if len(parts) != 8:
                raise ValueError("expected 8 fields")
            results.append({"name": parts[0],
                            "ticker": parts[1],
                            "start_equity": float(parts[2]),
                            "final_equity": float(parts[3]),
                            "total_return": float(parts[4]),
                            "max_drawdown": float(parts[5]),
                            "sharpe_like": float(parts[6]),
                            "trade_count": int(parts[7])})
        except ValueError:
            print("Skipped a damaged results line: " + line.strip())
    return results
