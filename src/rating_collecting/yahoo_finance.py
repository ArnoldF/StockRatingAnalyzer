
import csv
import os

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from src.rating_collecting.index_lists import SP_500_2013


def collect_ratings_from_page(page_content, ticker: str) -> list[tuple]:
    # ratings are expected to be in table td objects with id 'yf-12wn017'
    soup = BeautifulSoup(page_content, 'html.parser')
    td_elements = soup.find_all("td", class_="yf-12wn017")
    ratings_list = []

    for i in range(0, len(td_elements), 3):
        classification = td_elements[i].get_text(strip=True)
        text = td_elements[i + 1].get_text(strip=True)
        date = td_elements[i + 2].get_text(strip=True)
        ratings_list.append((ticker, classification, text, date))

    return ratings_list


def write_to_csv(data: list[tuple]):
    output_file = os.path.join('data', 'ratings_SP500_2013.csv')
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Ticker", "Change", "Text", "Date"])
        writer.writerows(data)


def collect_ratings_for_tickers(tickers: str) -> list[tuple]:
    all_ratings = []

    with sync_playwright() as p:
        # Launch a browser and go to main page
        browser = p.chromium.launch(headless=False)  # Set headless=True for no GUI
        page = browser.new_page()
        main_url = f"https://finance.yahoo.com/quote"
        page.goto(main_url)

        # Wait for the cookie banner to appear and click "Reject All" button
        try:
            reject_button_selector = "button.btn.secondary.reject-all"  # Adjust to match the "Reject All" button
            page.wait_for_selector(reject_button_selector, timeout=5000)  # Wait up to 5 seconds
            page.click(reject_button_selector)
            print("Rejected cookies.")

        except Exception as e:
            print("Cookie banner not opened or reject all button not found or timeout:", e)

        # for each ticker, go to the respective analysis page,
        # extend the ratings, and copy the entries in the rating table
        for ticker in tickers:
            ticker_url = f"{main_url}/{ticker}/analysis/"
            page.goto(ticker_url)

            try:
                page.wait_for_load_state("networkidle", timeout=10000)

                button_selector = 'button.tertiary-btn.fin-size-small'
                page.wait_for_selector(button_selector, timeout=10000)
                page.click(button_selector)

                page.wait_for_load_state("networkidle", timeout=10000)
                page_content = page.content()

            except Exception as e:
                print("Load more button not found or timeout:", e)
                continue

            ratings_for_ticker = collect_ratings_from_page(page_content, ticker)
            if isinstance(ratings_for_ticker, list):
                all_ratings.extend(ratings_for_ticker)
                print(f'Found {len(ratings_for_ticker)} ratings for ticker {ticker}')

        browser.close()

    return all_ratings

#old = pd.read_csv('old_SP500.csv')
#old = old[old['t2'] == '2012-12-31']
#print(*old['ticker'].to_list(), sep='",\n"')

all_ratings = collect_ratings_for_tickers(SP_500_2013)
write_to_csv(all_ratings)
