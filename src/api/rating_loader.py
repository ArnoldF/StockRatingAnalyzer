
from datetime import datetime
import os.path
import pandas as pd

from .rating_mapping import rating_mapping


class RatingAPI:
    def __init__(self, from_time: datetime, to_time: datetime):
        self.from_time = from_time
        self.to_time = to_time

        self._ratings = self._get_cleaned_ratings()

    @property
    def ratings(self):
        return self._ratings[
            ['Ticker', 'Rater', 'Change', 'Rating_text', 'Rating_numeric', 'Date_datetime', 'Rolling_mean', 'Rolling_mean_count']
        ]

    def _load_ratings_from_file(self) -> pd.DataFrame:
        file_path = os.path.join('data', 'ratings_SP500_2013.csv')
        assert os.path.exists(file_path), 'File with raw ratings could not be found.'

        ratings = pd.read_csv(file_path)

        return ratings

    def _clean_ratings(self, raw_ratings: pd.DataFrame) -> pd.DataFrame:

        if 'Date' not in raw_ratings.columns or 'Text' not in raw_ratings.columns:
            raise ValueError("Input DataFrame must contain columns 'Date' and 'Text'.")

        _rating_to_value = {
            'Sell': 0,
            'Hold': 1,
            'Buy': 2
        }

        cleaned_ratings = (
            raw_ratings
            # Convert 'Date' to datetime and filter to selected time range
            .assign(Date_datetime=lambda x: pd.to_datetime(x['Date'], errors='coerce'))
            .loc[lambda df: (df['Date_datetime'] >= self.from_time) &
                            (df['Date_datetime'] <= self.to_time)]
            # Split 'Text' column into 'Rater' and 'Rating'
            .assign(
                Rater=lambda x: x['Text'].apply(
                    lambda s: s.split(':')[0].strip() if ':' in s else None
                ),
                Original_Rating_text=lambda x: x['Text'].apply(
                    lambda s: s.split(':')[1].split(' to ')[1].strip() if ' to ' in s else s.split(':')[1].strip()
                )
            )
            # Map rating text into a numeric value and map each rating to 'SELL', 'HOLD' and 'BUY'
            .assign(
                Rating_text=lambda x: x['Original_Rating_text'].map(rating_mapping),
                Rating_numeric=lambda x: x['Rating_text'].map(_rating_to_value)
            )
            .dropna(subset=['Ticker', 'Rater', 'Rating_text', 'Date_datetime'])
            .sort_values(by=["Ticker", "Date_datetime"])
        )

        return cleaned_ratings

    def _compute_rolling_mean(self, cleaned_ratings: pd.DataFrame):
        cleaned_ratings['Rolling_mean'] = cleaned_ratings.groupby("Ticker", group_keys=False).apply(
            lambda x: x[["Rating_numeric", "Date_datetime"]].rolling("90D", min_periods=1, on='Date_datetime').mean()
        )["Rating_numeric"]

        cleaned_ratings['Rolling_mean_count'] = cleaned_ratings.groupby("Ticker", group_keys=False).apply(
            lambda x: x[["Rating_numeric", "Date_datetime"]].rolling("90D", min_periods=1, on='Date_datetime').count()
        )["Rating_numeric"]

    def _get_cleaned_ratings(self) -> pd.DataFrame:
        raw_ratings = self._load_ratings_from_file()
        cleaned_ratings = self._clean_ratings(raw_ratings)
        self._compute_rolling_mean(cleaned_ratings)

        return cleaned_ratings
