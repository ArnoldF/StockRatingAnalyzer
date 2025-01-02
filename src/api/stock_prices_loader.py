from datetime import datetime, timedelta
import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class StockPricesAPI:
    def __init__(self, tickers: str, start_date: datetime):
        self.tickers = tickers
        self.start_date = start_date

        self._stock_prices = self._get_cleaned_prices()

    @property
    def stock_prices(self):
        return self._stock_prices

    def _validate_ticker_data(self, cleaned_prices):

        for ticker, dataframe in cleaned_prices.items():
            # Check for excessive price changes (defined as greater than 50%)
            validation_frame = dataframe.copy()
            validation_frame["pct_change"] = validation_frame["Close"].pct_change()  # Calculate percentage change
            exceeds_change = (validation_frame["pct_change"].abs() > 0.5).any()

            # Check for data completeness
            total_days = (validation_frame["Date"].max() - validation_frame["Date"].min()).days + 1
            row_count = len(validation_frame)
            is_complete = row_count >= 0.66 * total_days

            if exceeds_change:
                logger.info(f'Ticker for {ticker} has large jumps in the stock price by up to '
                             f'{int(validation_frame["pct_change"].abs().max() * 100)}%.')

            if not is_complete:
                logger.info(f'The ticker for {ticker} does seem to miss many days.')

            if validation_frame["Date"].iloc[0] > self.start_date:
                logger.info(f'The ticker for {ticker} is starting later than wanted.')

            if validation_frame["Date"].iloc[-1] < datetime.now() - timedelta(days=10):
                logger.info(f'The ticker for {ticker} is missing recent data.')

    def _download_data_from_yfinance(self) -> dict[str, pd.DataFrame]:
        all_tickers = yf.download(
            tickers=self.tickers,
            start=self.start_date,
            group_by='ticker',
            progress=True,
        )
        ticker_dict = dict()

        for ticker in self.tickers:
            ticker_data = all_tickers[ticker].copy()
            ticker_data['Ticker'] = ticker
            ticker_dict[ticker] = ticker_data

        return ticker_dict

    def _clean_stock_prices(self, raw_prices: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        cleaned_data = dict()

        for ticker, stock_prices in raw_prices.items():
            cleaned_data[ticker] = (
                stock_prices
                .reset_index()  # move date from index to column
                .assign(Date=lambda df: pd.to_datetime(df['Date'], errors='coerce'))
                .loc[:, ['Ticker', 'Close', 'Date']]
                .dropna()
            )

        return cleaned_data

    def _get_cleaned_prices(self) -> dict[str, pd.DataFrame]:
        raw_prices = self._download_data_from_yfinance()
        cleaned_prices = self._clean_stock_prices(raw_prices)

        # validate that downloaded ticker data is consistent
        self._validate_ticker_data(cleaned_prices)

        return cleaned_prices
