from datetime import datetime, timedelta
import logging
import os
import pickle

import pandas as pd

from src.api.stock_prices_loader import StockPricesAPI
from src.api.rating_loader import RatingAPI

logger = logging.getLogger(__name__)


def filter_ratings_without_stock_prices(ratings, stock_prices, horizon) -> pd.DataFrame:
    # remove ratings at which time no stock prices could be found
    earliest_known_price = {
        ticker: stock_prices[ticker]['Date'].min()
        for ticker in stock_prices
    }
    filtered_ratings = ratings.copy()[
        ratings.apply(
            lambda row: row['Date_datetime'] >= earliest_known_price.get(row['Ticker']), axis=1
        )
    ]

    # remove ratings for which the not sufficient future stock prices are known
    latest_known_price = {
        ticker: stock_prices[ticker]['Date'].max()
        for ticker in stock_prices
    }
    filtered_ratings = filtered_ratings[
        ratings.apply(
            lambda row: row['Date_datetime'] + timedelta(days=horizon*1.3) <= latest_known_price.get(row['Ticker']), axis=1
        )
    ]
    logger.info(f'Removed {len(ratings) - len(filtered_ratings)} '
                f'ratings because stock prices are missing for the same time horizon.')

    return filtered_ratings


def load_historic_ratings_and_prices(
        from_year: int,
        to_year: int,
        performance_horizon: int,
        load_from_cache: bool = False
):
    if load_from_cache and os.path.exists(os.path.join('data', 'cache')):
        logger.info('Loading cleaned ratings and stock prices from cache')
        with open(os.path.join('data', 'cache'), 'rb') as file:
            ratings, stock_prices = pickle.load(file)

    else:
        logger.info('Computing cleaned ratings and stock prices')
        ratings_from = datetime(year=from_year, month=1, day=1)
        ratings_to = datetime(year=to_year, month=1, day=1)

        ratings = RatingAPI(
            from_time=ratings_from,
            to_time=ratings_to
        ).ratings

        # Load historic stock prices for each company with a rating
        companies = list(ratings['Ticker'].unique())
        prices_from = ratings_from - timedelta(days=30)
        stock_prices = StockPricesAPI(tickers=companies, start_date=prices_from).stock_prices

        ratings = filter_ratings_without_stock_prices(ratings, stock_prices, performance_horizon)

        with open(os.path.join('data', 'cache'), 'wb') as file:
            pickle.dump((ratings, stock_prices), file)

    logger.info(f"Loaded {len(ratings)} ratings for which the performance can be computed.")

    return ratings, stock_prices
