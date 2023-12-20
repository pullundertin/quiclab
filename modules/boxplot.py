
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from modules.tests import find_keys_with_list_values
from modules.prerequisites import read_test_cases
from modules.prerequisites import read_configuration

BOXPLOTS_DIR = read_configuration().get("BOXPLOTS_DIR")

def combine_quic_and_tcp_values_for(df, column_postfix):
    """Combine QUIC and TCP values into a single column."""
    melted_df = pd.melt(df, id_vars=['mode'], value_vars=[f'quic_{column_postfix}', f'tcp_{column_postfix}'], var_name='Protocol', value_name=f'time_{column_postfix}')
    return melted_df

def plot_boxplot(df, ax, x_data, y_data, title, xlabel, ylabel):
    """Plot a boxplot on the specified axes."""
    sns.boxplot(ax=ax, x=x_data, y=y_data, data=df.dropna())
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

def show_boxplot(df):
    """Create and display separate boxplots for handshake and connection times."""
    hs_df = combine_quic_and_tcp_values_for(df, 'hs')
    conn_df = combine_quic_and_tcp_values_for(df, 'conn')

    fig, axes = plt.subplots(2, 1, figsize=(8, 10))

    plot_boxplot(hs_df, axes[0], 'mode', 'time_hs', 'QUIC vs TCP Handshake', 'Implementations', 'Time')
    plot_boxplot(conn_df, axes[1], 'mode', 'time_conn', 'QUIC vs TCP Connection', 'Implementations', 'Time')

    plt.tight_layout()
    plt.savefig(f"{BOXPLOTS_DIR}/boxplots.png", dpi=300, bbox_inches='tight')
    plt.show()


