from collections import defaultdict
from datetime import datetime
from typing import Optional

import pandas as pd
import tqdm


def get_performance_after(
        dataframe: pd.DataFrame,
        start_date: datetime,
        performance_horizon: int,
        value_col: str = 'Close',
) -> Optional[pd.DataFrame]:
    # check wether the stock price series starts before the given date
    assert start_date >= dataframe['Date'].iloc[0], \
        f'Cannot use rating with date {start_date}, stock price series start at {dataframe["Date"].iloc[0]}'

    # find the index of the row, in which the `Date` is just before `start_date`
    dataframe['Date'].iloc[0] < start_date
    start_index = dataframe['Date'].searchsorted(start_date, side='left') - 1
    start_value = dataframe.iloc[start_index][value_col]

    result_df = (
        dataframe[start_index:start_index + performance_horizon]
        .assign(
            change_percent=lambda x: ((x[value_col] - start_value) / start_value) * 100
        )
        .reset_index()
        .loc[:, ['change_percent']]
    )

    # Check for data completeness
    assert len(result_df) == performance_horizon, 'The performance dataframe is too short'
    total_days = (dataframe.iloc[start_index + performance_horizon]["Date"] - dataframe.iloc[start_index]["Date"]).days + 1
    row_count = len(result_df)
    is_complete = row_count >= 0.66 * total_days
    if not is_complete:
        print('Many days seem to be missing within the date range')

    return result_df


def get_mean_over_dataframes(dataframes: list[pd.DataFrame]) -> pd.DataFrame:
    # TODO assert that each dataframe has same index and only one column
    concatenated = pd.concat(dataframes, axis=1)
    averaged = concatenated.mean(axis=1)

    return pd.DataFrame(averaged, columns=['mean'])


def compute_performance_after_rating(
        ratings: pd.DataFrame,
        stock_prices: dict[str, pd.DataFrame],
        performance_horizon: int
) -> dict[str, pd.DataFrame]:
    # For each rating, compute the performance (in terms of change in stock price) for the next year
    # The baseline is the stock price of the day before the rating was published
    performances_after_rating = defaultdict(list)

    for _, rating_entry in ratings.iterrows():
        company = rating_entry['Ticker']
        date = rating_entry['Date_datetime']
        rating_text = rating_entry['Rating_text']

        performance = get_performance_after(stock_prices[company], date, performance_horizon)
        if performance is not None:
            performances_after_rating[rating_text].append(performance)

    return performances_after_rating


def compute_performance_any_day(
        ratings: pd.DataFrame,
        stock_prices: dict[str, pd.DataFrame],
        performance_horizon: int
) -> list[pd.DataFrame]:
    # Compute the performance starting from randomly selected days
    # For each ticker, the number of computed performances equals number of existing ratings
    # to consider the distribution of ratings across companies in the mean later
    performances_any_day = []
    ratings_per_company = ratings['Ticker'].value_counts().to_dict()

    for company, num_ratings in ratings_per_company.items():
        start_interval = ratings.loc[ratings['Ticker'] == company, 'Date_datetime'].min()
        end_interval = ratings.loc[ratings['Ticker'] == company, 'Date_datetime'].max()
        prices = stock_prices[company]
        random_dates = (
            prices[(prices["Date"] >= start_interval) & (prices["Date"] <= end_interval)]
            ["Date"].sample(n=num_ratings, random_state=42).to_list()
        )

        for random_date in random_dates:
            performances_any_day.append(
                get_performance_after(stock_prices[company], random_date, performance_horizon)
            )

    return performances_any_day


def compute_mean_performance_after_rating(
        performances_after_rating: dict[str, pd.DataFrame]
) -> dict[str, pd.DataFrame]:
    mean_performance_after_rating = {
        rating_text: get_mean_over_dataframes(performances)
        for rating_text, performances in performances_after_rating.items()
    }

    return mean_performance_after_rating
