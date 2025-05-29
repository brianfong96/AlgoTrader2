import pandas as pd
from src.pad_strategy import backtest_pad


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


def test_final_total_return_column():
    df = sample_price_df()
    result = backtest_pad(df)

    total_deposit = result["TotalDeposit"].iloc[-1]
    expected_return = result["PortfolioValue"].iloc[-1] / total_deposit - 1
    assert "FinalTotalReturn" in result.columns
    assert abs(result["FinalTotalReturn"].iloc[-1] - expected_return) < 1e-8
