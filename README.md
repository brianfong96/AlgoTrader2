# AlgoTrader2

This project demonstrates a simple back‑test of a **Percentage Allocation DCA (PAD)**
strategy applied to the ETF VOO. Each month an investor contributes `$100` by
default. If the VOO price drops by `20%` or more relative to the previous month,
the monthly contribution increases by `20%` (`$120`). When the price rises by
`20%` or more, the contribution is reduced by `20%` (`$80`).

The repository includes:

- `data/voo_prices.csv` – sample monthly price data used for testing.
- `src/pad_strategy.py` – implementation of the back‑test logic.
- `tests/` – unit tests validating the strategy.

## Running the back‑test

```bash
python src/pad_strategy.py data/voo_prices.csv
```

This prints the month‑by‑month history and the final portfolio value.

## Running the tests

The project uses `pytest` for testing. Install dependencies and run tests with:

```bash
pip install pandas pytest
pytest
```
