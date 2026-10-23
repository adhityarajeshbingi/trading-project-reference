# Glacial Pace Capital trading desk (MIS41110)

| File | Piece | Reference |
|---|---|---|
| `desk.py` | The desk: the menu, manual trades at today's close, bad input | Adhitya |
| `engine.py` | `Account` and `Simulator`: cash, fee, rejects, next-open day loop | Kousik |
| `agent.py` | `TradingAgent`, the competition entry (self-contained) | Laveeza |
| `analytics.py` | Returns, moving average, drawdown, sharpe-like, the three charts | Ayesha |
| `market_data.py` | Loading prices, news and lexicon; the three regimes | Tarun |
| `storage.py`, `tests.py` | Session, results and leaderboard in plain text; the asserts | Tarun |

Put the course data in `data/training/`, then from this folder:

    python3 desk.py          # start the program (no arguments)
    python3 tests.py         # 21 asserts on the rules
    python3 selfcheck.py     # the course check on agent.py

On Windows, type `python` instead of `python3`.
