import pandas as pd
from src.pad_strategy import backtest_pad, calculate_lump_sum


def sample_price_df():
    return pd.DataFrame(
        {
            "Date": [
                "2021-01-31",
                "2021-02-28",
                "2021-03-31",
                "2021-04-30",
                "2021-05-31",
                "2021-06-30",
                "2021-07-31",
                "2021-08-31",
                "2021-09-30",
                "2021-10-31",
                "2021-11-30",
                "2021-12-31",
            ],
            "Close": [
                100,
                120,
                96,
                96,
                115,
                92,
                92,
                110,
                130,
                150,
                180,
                144,
            ],
        }
    )


def test_deposit_adjustments():
    df = sample_price_df()
    result = backtest_pad(df)

    expected_deposits = [
        100.0,  # first month
        80.0,   # price up 20%
        120.0,  # price down 20%
        100.0,  # no significant change
        100.0,  # less than 20% up
        120.0,  # down ~20%
        100.0,  # no change
        100.0,  # less than 20% up
        100.0,  # less than 20% up
        100.0,  # less than 20% up
        80.0,   # up 20%
        120.0,  # down 20%
    ]
    assert result["Deposit"].tolist() == expected_deposits


def test_portfolio_value_consistency():
    df = sample_price_df()
    result = backtest_pad(df)

    # Verify that portfolio value equals total shares times current price
    assert all(
        abs(result.loc[i, "PortfolioValue"] - result.loc[i, "TotalShares"] * result.loc[i, "Price"]) < 1e-8
        for i in range(len(result))
    )


def test_net_profit_and_return():
    df = sample_price_df()
    result = backtest_pad(df)

    total_deposit = result["TotalDeposit"].iloc[-1]
    final_value = result["PortfolioValue"].iloc[-1]
    expected_return = final_value / total_deposit - 1
    expected_profit = final_value - total_deposit

    # Net profit column should match portfolio value minus total deposit
    assert "NetProfit" in result.columns
    assert abs(result["NetProfit"].iloc[-1] - expected_profit) < 1e-8

    # There should no longer be a FinalTotalReturn column
    assert "FinalTotalReturn" not in result.columns

    # Calculated final return should be correct
    assert abs(expected_return - (final_value / total_deposit - 1)) < 1e-8


def test_lump_sum_calculation():
    df = sample_price_df()
    result = backtest_pad(df)

    shares, profit = calculate_lump_sum(result)
    total_deposit = result["TotalDeposit"].iloc[-1]

    expected_shares = total_deposit / result["Price"].iloc[0]
    expected_profit = expected_shares * result["Price"].iloc[-1] - total_deposit

    assert abs(shares - expected_shares) < 1e-8
    assert abs(profit - expected_profit) < 1e-8
