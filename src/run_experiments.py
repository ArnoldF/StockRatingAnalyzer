
import logging

from src.api.data_loader import load_historic_ratings_and_prices
from src.analytics.t_tests import perform_t_tests
from src.analytics.performance import compute_performance_after_rating, compute_mean_performance_after_rating, \
    compute_performance_any_day
from src.plotting.price_change import plot_mean_performance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FROM_YEAR = 2014
TO_YEAR = 2024
PERFORMANCE_HORIZON = 240


def perform_experiment(ratings, stock_prices):
    # print some statistics about the ratings
    logger.info('Rating overview')
    logger.info(f' Ratings by {len(list(ratings["Ticker"].unique()))} companies')
    logger.info(ratings['Rating_numeric'].value_counts())
    logger.info(ratings['Rater'].value_counts().head(10))

    # computation
    performance_after_rating = compute_performance_after_rating(ratings, stock_prices, PERFORMANCE_HORIZON)
    performance_after_rating['any day'] = compute_performance_any_day(ratings, stock_prices, PERFORMANCE_HORIZON)
    mean_performance_after_rating = compute_mean_performance_after_rating(performance_after_rating)

    # results
    plot_mean_performance(mean_performance_after_rating, 'mean')
    perform_t_tests(performance_after_rating)


# load data: ratings and stock prices
ratings, stock_prices = load_historic_ratings_and_prices(
    from_year=FROM_YEAR,
    to_year=TO_YEAR,
    performance_horizon=PERFORMANCE_HORIZON,
    load_from_cache=True
)

# Experiment 1: ratings as individual signal
perform_experiment(ratings, stock_prices)

# Experiment 2: ratings as individual signal, but only those which suggest a change
change_ratings = ratings[ratings['Change'].isin(['Maintains', 'Upgrade', 'Downgrade'])].copy()
change_ratings["Rating_text"] = change_ratings["Change"]
perform_experiment(change_ratings, stock_prices)

# Experiment 3: ratings as aggregated signal
def assign_rating_text(rolling_mean):
    if rolling_mean > 1.5:
        return "Buy"
    elif 1 <= rolling_mean < 1.5:
        return "Hold"
    else:
        return "Sell"


aggregated_ratings = ratings[ratings['Rolling_mean_count'] >= 5].copy()
aggregated_ratings['rating_text'] = aggregated_ratings['Rolling_mean'].apply(assign_rating_text)
perform_experiment(aggregated_ratings, stock_prices)

# Experiment 4: ratings from specific institutions only
ratings_from_rater = ratings[ratings['Rater'] == "Morgan Stanley"].copy()
perform_experiment(ratings_from_rater, stock_prices)
