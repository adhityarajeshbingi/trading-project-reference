# Glacial Pace Capital trading simulator (MIS41110, group G18)

Built to our Interface Contract v1.2 and Developer Specs.

| File | Reference | Job |
|---|---|---|
| `desk.py` | Adhitya | the menu (start here) |
| `market_data.py` | Tarun | reads the data files |
| `account.py` | Kousik | cash, shares, fee |
| `engine.py` | Kousik | runs the days |
| `agent.py` | Laveeza | the trading rule |
| `analytics.py` | Laveeza | 3 numbers, 3 charts |
| `storage.py` | Tarun | saves runs |
| `check_*.py` | each file's reference | plain-assert tests |

Put the nine training files in `data/training/`, then from this folder:

    python desk.py                 # the program, no arguments
    python check_account.py        # and the other four check_*.py files
    python agent_unittest.py       # professor's: 10/10
    python selfcheck.py            # professor's: all green, 14525.6 on ZNTH
