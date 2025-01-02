from itertools import combinations
import logging
import statistics

import pandas as pd
from scipy.stats import ttest_ind

logger = logging.getLogger(__name__)


def perform_t_tests(
        performance_after_rating: dict[str, pd.DataFrame],
        time_points: list[int] = [1, 2, 239]
) -> None:
    # Perform two-sample t-test between each pair of ratings categories
    rating_categories = list(performance_after_rating.keys())

    for cat1, cat2 in combinations(rating_categories, 2):
        p_values = []
        mean_diffs = []

        for time_point in time_points:
            # get performances (return wrt day 0 in % ) for both categories
            performances1 = [
                df.loc[time_point, 'change_percent']
                for df in performance_after_rating[cat1]
            ]
            performances2 = [
                df.loc[time_point, 'change_percent']
                for df in performance_after_rating[cat2]
            ]

            # t-test to establish whether the two performance lists stem from two different groups
            # Set equal_var=False for Welch’s t-test, since performances are largely indepdendent
            t_stat, p_value = ttest_ind(performances1, performances2, equal_var=False)
            p_values.append(p_value)
            mean_diffs.append(statistics.mean(performances1) - statistics.mean(performances2))

        logger.info(f't-test for {cat1} / {cat2}: {p_values}, {mean_diffs}')
