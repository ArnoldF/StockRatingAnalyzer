import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_mean_performance(dataframes: dict[str, pd.DataFrame], col_to_plot: str):

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = {
        'Buy': 'limegreen',
        'Sell': 'crimson',
        'Hold': 'gold',
        'any day': 'grey',
        'Upgrade': 'limegreen',
        'Downgrade': 'crimson',
        'Maintains': 'gold',
    }

    for (key, dataframe) in dataframes.items():
        ax.plot(dataframe.index, dataframe[col_to_plot], label=key, color=colors[key], linewidth=1.0)

    # Formatting
    ax.xaxis.set_major_locator(plt.MultipleLocator(50))  # Tick every 50 days on x-axis
    ax.yaxis.set_major_locator(plt.MultipleLocator(5.0))  # Tick every 5 percentage points on y-axis

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)
    ax.grid(False)

    # Add labels next to the lines
    for title, values in dataframes.items():
        ax.annotate(
            title,
            xy=(len(values) - 1, values[col_to_plot].iloc[-1]),
            color=colors[title],
            fontsize=10
        )

    ax.set_xlabel('Trading Days', fontsize=12)
    ax.set_ylabel('Price Change in %', fontsize=12)

    fig_name = f'{datetime.datetime.now().strftime("%H_%M_%S")}.png'
    plt.savefig(fig_name)

    plt.show()


def plot_rating_distribution(ratings):
    fig, ax = plt.subplots(figsize=(10, 6))
    ratings = ratings.sort_values("Date_datetime")

    ratings_buy = ratings[ratings['Rating_text'] == 'Buy']["Date_datetime"].dt.year.value_counts()
    ax.bar(
        list(ratings["Date_datetime"].dt.year.value_counts().index),
        ratings_buy,
        color='limegreen'
    )

    ratings_hold = ratings[ratings['Rating_text'] == 'Hold']["Date_datetime"].dt.year.value_counts()
    ax.bar(
        list(ratings["Date_datetime"].dt.year.value_counts().index),
        ratings_hold,
        bottom=ratings_buy,
        color='grey'
    )
    ax.bar(
        list(ratings["Date_datetime"].dt.year.value_counts().index),
        ratings[ratings['Rating_text'] == 'Sell']["Date_datetime"].dt.year.value_counts(),
        bottom=np.array(ratings_buy) + np.array(ratings_hold),
        color='crimson'
    )

    # Formatting
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(False)
    ax.spines['bottom'].set_linewidth(0.5)
    ax.grid(False)

    plt.show()
