import datetime
import os.path

import matplotlib.pyplot as plt
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
    ax.xaxis.set_major_locator(plt.MultipleLocator(50))  # Tick every 50 points on x-axis
    ax.yaxis.set_major_locator(plt.MultipleLocator(5.0))  # Tick every 5 percentage points on y-axis

    ax.spines['top'].set_visible(False)  # Remove the top spine
    ax.spines['right'].set_visible(False)  # Remove the right spine
    ax.spines['left'].set_linewidth(0.5)  # Slim left axis line
    ax.spines['bottom'].set_linewidth(0.5)  # Slim bottom axis line
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
