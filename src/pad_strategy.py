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


def backtest_pad(
    price_df: pd.DataFrame,
    base_pad: float = 100.0,
    increase_threshold: float = 20.0,
    decrease_threshold: float = 20.0,
    increase_pad: float = 1.2,
    decrease_pad: float = 0.8,
) -> pd.DataFrame:
    """Backtests a percentage allocation strategy on VOO.

    Parameters
    ----------
    price_df : pd.DataFrame
        DataFrame with columns ``Date`` and ``Close`` sorted by ``Date``.
    base_pad : float, default 100.0
        Base monthly purchase amount in dollars.
    increase_threshold : float, default 20.0
        Percentage drop required to increase the purchase amount.
    decrease_threshold : float, default 20.0
        Percentage rise required to decrease the purchase amount.
    increase_pad : float, default 1.2
        Multiplier for the purchase amount when price drops sufficiently.
    decrease_pad : float, default 0.8
        Multiplier for the purchase amount when price rises sufficiently.

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
    inc_threshold_pct = increase_threshold / 100.0
    dec_threshold_pct = decrease_threshold / 100.0

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

        if curr_price <= prev_price * (1 - inc_threshold_pct):
            deposit = base_pad * increase_pad
        elif curr_price >= prev_price * (1 + dec_threshold_pct):
            deposit = base_pad * decrease_pad
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
    increase_threshold: float = 20.0,
    decrease_threshold: float = 20.0,
    increase_pad: float = 1.2,
    decrease_pad: float = 0.8,
) -> pd.DataFrame:
    """Run the backtest using CSV data or by downloading data for ``ticker``."""

    if price_csv:
        price_df = pd.read_csv(price_csv)
    else:
        price_df = fetch_price_data(ticker)
    return backtest_pad(
        price_df,
        base_pad=base_pad,
        increase_threshold=increase_threshold,
        decrease_threshold=decrease_threshold,
        increase_pad=increase_pad,
        decrease_pad=decrease_pad,
    )


def calculate_lump_sum(result_df: pd.DataFrame) -> tuple[float, float]:
    """Return lump sum shares and profit using the backtest result."""

    total_deposit = result_df.iloc[-1]["TotalDeposit"]
    first_price = result_df.iloc[0]["Price"]
    last_price = result_df.iloc[-1]["Price"]
    shares = total_deposit / first_price
    profit = shares * last_price - total_deposit
    return shares, profit


def calculate_annual_return(
    final_value: float, total_deposit: float, duration_days: int
) -> float:
    """Return the annualized return as a decimal."""

    years = duration_days / 365.0 if duration_days else 0.0
    if years == 0.0:
        return 0.0
    return (final_value / total_deposit) ** (1 / years) - 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run PAD backtest on a ticker.")
    parser.add_argument("--csv", help="Optional CSV file with Date and Close columns")
    parser.add_argument("--ticker", default="VOO", help="Ticker symbol to download prices for")
    parser.add_argument("--base", type=float, default=100.0, help="Base PAD amount")
    parser.add_argument(
        "--inc-thresh",
        type=float,
        default=20.0,
        help="Percentage drop required to increase deposits",
    )
    parser.add_argument(
        "--dec-thresh",
        type=float,
        default=20.0,
        help="Percentage rise required to decrease deposits",
    )
    parser.add_argument(
        "--inc-pad",
        type=float,
        default=1.2,
        help="Multiplier for deposit when threshold drop met",
    )
    parser.add_argument(
        "--dec-pad",
        type=float,
        default=0.8,
        help="Multiplier for deposit when threshold rise met",
    )
    parser.add_argument("--log", help="Directory to store log file")
    parser.add_argument(
        "--no-results",
        action="store_true",
        help="Disable writing summary results to the results directory",
    )
    args = parser.parse_args()

    df = run_backtest(
        args.csv,
        ticker=args.ticker,
        base_pad=args.base,
        increase_threshold=args.inc_thresh,
        decrease_threshold=args.dec_thresh,
        increase_pad=args.inc_pad,
        decrease_pad=args.dec_pad,
    )
    pd.set_option("display.max_rows", None)
    print(df)

    final_value = df.iloc[-1]["PortfolioValue"]
    total_deposit = df.iloc[-1]["TotalDeposit"]
    final_return = (final_value / total_deposit - 1) * 100
    net_profit = final_value - total_deposit

    # Use Price column from the backtest result for lump sum calculations
    lumpsum_shares = total_deposit / df.iloc[0]["Price"]
    lumpsum_value = lumpsum_shares * df.iloc[-1]["Price"]
    lumpsum_profit = lumpsum_value - total_deposit
    profit_diff = net_profit - lumpsum_profit
    profit_diff_pct = (profit_diff / lumpsum_profit * 100) if lumpsum_profit != 0 else 0.0
    start_date = df.iloc[0]["Date"].date()
    end_date = df.iloc[-1]["Date"].date()
    duration_days = (df.iloc[-1]["Date"] - df.iloc[0]["Date"]).days

    pad_annual_return = calculate_annual_return(final_value, total_deposit, duration_days)
    lump_annual_return = calculate_annual_return(lumpsum_value, total_deposit, duration_days)
    annual_diff = pad_annual_return - lump_annual_return

    print("\nFinal portfolio value:", f"${final_value:,.2f}")
    print("Total deposited:", f"${total_deposit:,.2f}")
    print("Net profit:", f"${net_profit:,.2f}")
    print(f"Final total return: {final_return:.2f}%")
    print("Lump sum net profit:", f"${lumpsum_profit:,.2f}")
    print(
        f"Difference vs lump sum: ${profit_diff:,.2f} ({profit_diff_pct:.2f}%)"
    )
    print(f"PAD annual return: {pad_annual_return*100:.2f}%")
    print(f"Lump sum annual return: {lump_annual_return*100:.2f}%")
    print(f"Annual return difference: {annual_diff*100:.2f}%")
    print("Start date:", start_date)
    print("End date:", end_date)
    print(f"Duration: {duration_days} days")

    if args.log:
        os.makedirs(args.log, exist_ok=True)
        fname_parts = [
            args.ticker,
            f"base{args.base}",
            f"it{args.inc_thresh}",
            f"dt{args.dec_thresh}",
            f"ip{args.inc_pad}",
            f"dp{args.dec_pad}",
        ]
        log_path = os.path.join(args.log, "_".join(fname_parts) + ".txt")
        with open(log_path, "w") as f:
            f.write(df.to_string(index=False))
            f.write("\n\n")
            f.write(f"Final portfolio value: ${final_value:,.2f}\n")
            f.write(f"Total deposited: ${total_deposit:,.2f}\n")
            f.write(f"Net profit: ${net_profit:,.2f}\n")
            f.write(f"Final total return: {final_return:.2f}%\n")
            f.write(f"Lump sum net profit: ${lumpsum_profit:,.2f}\n")
            f.write(
                f"Difference vs lump sum: ${profit_diff:,.2f} ({profit_diff_pct:.2f}%)\n"
            )
            f.write(f"PAD annual return: {pad_annual_return*100:.2f}%\n")
            f.write(f"Lump sum annual return: {lump_annual_return*100:.2f}%\n")
            f.write(f"Annual return difference: {annual_diff*100:.2f}%\n")
            f.write(f"Start date: {start_date}\n")
            f.write(f"End date: {end_date}\n")
            f.write(f"Duration: {duration_days} days\n")
        print(f"Results written to {log_path}")

    if not args.no_results:
        os.makedirs("results", exist_ok=True)
        fname_parts = [
            args.ticker,
            f"base{args.base}",
            f"it{args.inc_thresh}",
            f"dt{args.dec_thresh}",
            f"ip{args.inc_pad}",
            f"dp{args.dec_pad}",
        ]
        results_path = os.path.join("results", "_".join(fname_parts) + ".txt")
        with open(results_path, "w") as f:
            f.write(f"Final portfolio value: ${final_value:,.2f}\n")
            f.write(f"Total deposited: ${total_deposit:,.2f}\n")
            f.write(f"Net profit: ${net_profit:,.2f}\n")
            f.write(f"Final total return: {final_return:.2f}%\n")
            f.write(f"Lump sum net profit: ${lumpsum_profit:,.2f}\n")
            f.write(
                f"Difference vs lump sum: ${profit_diff:,.2f} ({profit_diff_pct:.2f}%)\n"
            )
            f.write(f"PAD annual return: {pad_annual_return*100:.2f}%\n")
            f.write(f"Lump sum annual return: {lump_annual_return*100:.2f}%\n")
            f.write(f"Annual return difference: {annual_diff*100:.2f}%\n")
            f.write(f"Start date: {start_date}\n")
            f.write(f"End date: {end_date}\n")
            f.write(f"Duration: {duration_days} days\n")
        print(f"Summary written to {results_path}")
