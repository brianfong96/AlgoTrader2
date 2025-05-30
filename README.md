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

Deposit adjustments are controlled with separate thresholds and multipliers.
`--inc-thresh` and `--dec-thresh` specify the percentage drop or rise that
triggers a change in deposits (both default to `20`). `--inc-pad` and
`--dec-pad` are multipliers applied to the base deposit when those thresholds
are met (defaults `1.2` and `0.8`).
Results can be logged to a directory using `--log <dir>`. The file is named
using the provided arguments so multiple runs can be stored side by side.
Summary metrics including annual returns are also written to the `results`
directory unless `--no-results` is supplied.

This prints the month‑by‑month history. At the end it prints the final
portfolio value, the total amount deposited, the net profit and the final
total return as a percentage.

You can adjust these settings from the command line. For example, to use a 10%
increase threshold, a 15% decrease threshold and a $150 base deposit:

```bash
python src/pad_strategy.py --base 150 --inc-thresh 10 --dec-thresh 15
```

## Running the tests

The project uses `pytest` for testing. Install dependencies and run tests with:

```bash
pip install pandas yfinance pytest
pytest
```
