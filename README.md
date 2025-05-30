# AlgoTrader2

This project demonstrates a simple back‑test of a **Percentage Allocation DCA (PAD)**
strategy applied to stocks or ETFs. Each month an investor contributes `$100` by
default. If the price drops by `20%` or more relative to the previous month, the
monthly contribution increases by `20%` (`$120`). When the price rises by
`20%` or more, the contribution is reduced by `20%` (`$80`).

The repository includes:

- `data/voo_prices.csv` – sample monthly price data used for testing.
- `src/pad_strategy.py` – implementation of the back‑test logic. The script can
  download historical prices automatically using `yfinance`. Prices are
  aggregated to month end so the PAD logic runs on monthly data.
- `tests/` – unit tests validating the strategy.

## Running the back‑test


Running without arguments downloads the full history of VOO prices:

```bash
python src/pad_strategy.py
```

You can also supply your own CSV file or specify a different ticker:

```bash
python src/pad_strategy.py --csv data/voo_prices.csv

python src/pad_strategy.py --ticker AAPL
```

The threshold for adjusting deposits can be specified with `--threshold` (default `20`).
Results can be logged to a directory using `--log <dir>`, which writes a file
named like `TICKER_YYYYMMDD.txt` containing the final summary and history.

This prints the month‑by‑month history. At the end it prints the final
portfolio value, the total amount deposited, the net profit and the final
total return as a percentage.

The strategy threshold can be changed from the command line. For example, to
use a 10% threshold and a $150 base deposit:

```bash
python src/pad_strategy.py --base 150 --threshold 10
```

## Running the tests

The project uses `pytest` for testing. Install dependencies and run tests with:

```bash
pip install pandas yfinance pytest
pytest
```
