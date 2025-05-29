from __future__ import annotations

import pandas as pd
import yfinance as yf


def fetch_voo_data() -> pd.DataFrame:
    """Fetches the historical VOO price data for the maximum available period."""

    ticker = yf.Ticker("VOO")
    hist = ticker.history(period="max")
    hist = hist.reset_index()
    return hist[["Date", "Close"]]


def backtest_pad(price_df: pd.DataFrame, base_pad: float = 100.0, threshold: float = 0.2) -> pd.DataFrame:
    """Backtests a percentage allocation strategy on VOO.

    Parameters
    ----------
    price_df : pd.DataFrame
        DataFrame with columns ``Date`` and ``Close`` sorted by ``Date``.
    base_pad : float, default 100.0
        Base monthly purchase amount in dollars.
    threshold : float, default 0.2
        Percentage threshold used to increase or decrease the purchase amount.

    Returns
    -------
    pd.DataFrame
        History with columns ``Date``, ``Price``, ``Deposit``, ``Shares``,
        ``TotalShares``, ``PortfolioValue``, ``TotalDeposit`` and
        ``FinalTotalReturn``.
    """

    df = price_df.copy().reset_index(drop=True)
    if not {"Date", "Close"}.issubset(df.columns):
        raise ValueError("price_df must contain 'Date' and 'Close' columns")

    df["Date"] = pd.to_datetime(df["Date"])

    history = []
    total_shares = 0.0
    total_deposit = 0.0

    # Deposit for first month
    first_price = df.loc[0, "Close"]
    deposit = base_pad
    total_deposit += deposit
    total_shares += deposit / first_price
    history.append(
        {
            "Date": df.loc[0, "Date"],
            "Price": first_price,
            "Deposit": deposit,
            "Shares": deposit / first_price,
            "TotalShares": total_shares,
            "PortfolioValue": total_shares * first_price,
            "TotalDeposit": total_deposit,
        }
    )

    # Iterate over remaining months
    for idx in range(1, len(df)):
        prev_price = df.loc[idx - 1, "Close"]
        curr_price = df.loc[idx, "Close"]

        if curr_price <= prev_price * (1 - threshold):
            deposit = base_pad * 1.2
        elif curr_price >= prev_price * (1 + threshold):
            deposit = base_pad * 0.8
        else:
            deposit = base_pad

        shares = deposit / curr_price
        total_deposit += deposit
        total_shares += shares
        history.append(
            {
                "Date": df.loc[idx, "Date"],
                "Price": curr_price,
                "Deposit": deposit,
                "Shares": shares,
                "TotalShares": total_shares,
                "PortfolioValue": total_shares * curr_price,
                "TotalDeposit": total_deposit,
            }
        )

    result = pd.DataFrame(history)
    final_return = result.iloc[-1]["PortfolioValue"] / result.iloc[-1]["TotalDeposit"] - 1
    result["FinalTotalReturn"] = final_return
    return result


def run_backtest(price_csv: str | None = None, base_pad: float = 100.0, threshold: float = 0.2) -> pd.DataFrame:
    """Runs the backtest from a CSV file or by downloading data."""

    if price_csv:
        price_df = pd.read_csv(price_csv)
    else:
        price_df = fetch_voo_data()
    return backtest_pad(price_df, base_pad=base_pad, threshold=threshold)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run PAD backtest on VOO.")
    parser.add_argument("--csv", help="Optional CSV file with Date and Close columns")
    parser.add_argument("--base", type=float, default=100.0, help="Base PAD amount")
    args = parser.parse_args()

    df = run_backtest(args.csv, base_pad=args.base)
    pd.set_option("display.max_rows", None)
    print(df)
    print("\nFinal portfolio value:", df.iloc[-1]["PortfolioValue"])
    print("Final total return:", df.iloc[-1]["FinalTotalReturn"])
