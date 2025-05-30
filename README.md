# AlgoTrader2

This project demonstrates a simple back‑test of a **Percentage Allocation DCA (PAD)**
strategy applied to the ETF VOO. Each month an investor contributes `$100` by
default. If the VOO price drops by `20%` or more relative to the previous month,
the monthly contribution increases by `20%` (`$120`). When the price rises by
`20%` or more, the contribution is reduced by `20%` (`$80`).

The repository includes:

- `data/voo_prices.csv` – sample monthly price data used for testing.
- `src/pad_strategy.py` – implementation of the back‑test logic. The script can
  download historical VOO prices automatically using `yfinance`. Prices are
  aggregated to month end so the PAD logic runs on monthly data.
- `tests/` – unit tests validating the strategy.

## Running the back‑test


Running without arguments downloads the full history of VOO prices:

```bash
python src/pad_strategy.py
```

You can also supply your own CSV file:

```bash
python src/pad_strategy.py --csv data/voo_prices.csv
```

This prints the month‑by‑month history. At the end it prints the final
portfolio value, the net profit and the final total return as a percentage.

## Running the tests

The project uses `pytest` for testing. Install dependencies and run tests with:

```bash
pip install pandas yfinance pytest
pytest
```
