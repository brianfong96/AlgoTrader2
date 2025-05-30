from __future__ import annotations

import pandas as pd
import yfinance as yf
import os


def fetch_price_data(ticker: str) -> pd.DataFrame:
    """Fetch monthly close prices for a ticker using yfinance."""

    ticker_obj = yf.Ticker(ticker)
    hist = ticker_obj.history(period="max", interval="1mo")
    hist = hist.reset_index()
    return hist[["Date", "Close"]]


def backtest_pad(price_df: pd.DataFrame, base_pad: float = 100.0, threshold: float = 20.0) -> pd.DataFrame:
    """Backtests a percentage allocation strategy on VOO.

    Parameters
    ----------
    price_df : pd.DataFrame
        DataFrame with columns ``Date`` and ``Close`` sorted by ``Date``.
    base_pad : float, default 100.0
        Base monthly purchase amount in dollars.
    threshold : float, default 20.0
        Percentage threshold used to increase or decrease the purchase amount.

    Returns
    -------
    pd.DataFrame
        History with columns ``Date``, ``Price``, ``Deposit``, ``Shares``,
        ``TotalShares``, ``PortfolioValue``, ``TotalDeposit`` and ``NetProfit``.
    """

    df = price_df.copy().reset_index(drop=True)
    if not {"Date", "Close"}.issubset(df.columns):
        raise ValueError("price_df must contain 'Date' and 'Close' columns")

    df["Date"] = pd.to_datetime(df["Date"])

    history = []
    total_shares = 0.0
    total_deposit = 0.0
    threshold_pct = threshold / 100.0

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
            "NetProfit": total_shares * first_price - total_deposit,
        }
    )

    # Iterate over remaining months
    for idx in range(1, len(df)):
        prev_price = df.loc[idx - 1, "Close"]
        curr_price = df.loc[idx, "Close"]

        if curr_price <= prev_price * (1 - threshold_pct):
            deposit = base_pad * 1.2
        elif curr_price >= prev_price * (1 + threshold_pct):
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
                "NetProfit": total_shares * curr_price - total_deposit,
            }
        )

    result = pd.DataFrame(history)
    return result


def run_backtest(
    price_csv: str | None = None,
    ticker: str = "VOO",
    base_pad: float = 100.0,
    threshold: float = 20.0,
) -> pd.DataFrame:
    """Run the backtest using CSV data or by downloading data for ``ticker``."""

    if price_csv:
        price_df = pd.read_csv(price_csv)
    else:
        price_df = fetch_price_data(ticker)
    return backtest_pad(price_df, base_pad=base_pad, threshold=threshold)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run PAD backtest on a ticker.")
    parser.add_argument("--csv", help="Optional CSV file with Date and Close columns")
    parser.add_argument("--ticker", default="VOO", help="Ticker symbol to download prices for")
    parser.add_argument("--base", type=float, default=100.0, help="Base PAD amount")
    parser.add_argument(
        "--threshold",
        type=float,
        default=20.0,
        help="Percentage threshold for adjusting the PAD amount",
    )
    parser.add_argument("--log", help="Directory to store log file")
    args = parser.parse_args()

    df = run_backtest(args.csv, ticker=args.ticker, base_pad=args.base, threshold=args.threshold)
    pd.set_option("display.max_rows", None)
    print(df)

    final_value = df.iloc[-1]["PortfolioValue"]
    total_deposit = df.iloc[-1]["TotalDeposit"]
    final_return = (final_value / total_deposit - 1) * 100
    net_profit = final_value - total_deposit
    start_date = df.iloc[0]["Date"].date()
    end_date = df.iloc[-1]["Date"].date()
    duration_days = (df.iloc[-1]["Date"] - df.iloc[0]["Date"]).days

    print("\nFinal portfolio value:", final_value)
    print("Total deposited:", total_deposit)
    print("Net profit:", net_profit)
    print(f"Final total return: {final_return:.2f}%")
    print("Start date:", start_date)
    print("End date:", end_date)
    print(f"Duration: {duration_days} days")

    if args.log:
        os.makedirs(args.log, exist_ok=True)
        log_path = os.path.join(
            args.log,
            f"{args.ticker}_{pd.Timestamp.now().strftime('%Y%m%d')}.txt",
        )
        with open(log_path, "w") as f:
            f.write(df.to_string(index=False))
            f.write("\n\n")
            f.write(f"Final portfolio value: {final_value}\n")
            f.write(f"Total deposited: {total_deposit}\n")
            f.write(f"Net profit: {net_profit}\n")
            f.write(f"Final total return: {final_return:.2f}%\n")
            f.write(f"Start date: {start_date}\n")
            f.write(f"End date: {end_date}\n")
            f.write(f"Duration: {duration_days} days\n")
        print(f"Results written to {log_path}")
