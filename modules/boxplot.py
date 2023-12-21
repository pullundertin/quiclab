
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from modules.prerequisites import read_configuration

BOXPLOTS_DIR = read_configuration().get("BOXPLOTS_DIR")


def combine_quic_and_tcp_values_for(df, column_postfix, value):
    """Combine QUIC and TCP values into a single column."""
    melted_df = pd.melt(df, id_vars=['mode'], value_vars=[
                        f'quic_{column_postfix}', f'tcp_{column_postfix}'], value_name=f'time_{value}')
    return melted_df


def plot_boxplot(df, ax, x_data, y_data, title, xlabel, ylabel):
    """Plot a boxplot on the specified axes."""
    sns.boxplot(ax=ax, x=x_data, y=y_data, data=df.dropna())
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def create_boxplots_for_each_value_of_independent_variable(df, control_parameter):
    for value in df[control_parameter].unique():
        # Filter the DataFrame based on the current unique value
        filtered_df = df[df[control_parameter] == value]

        hs_df = combine_quic_and_tcp_values_for(filtered_df, 'hs', value)
        conn_df = combine_quic_and_tcp_values_for(filtered_df, 'conn', value)

        fig, axes = plt.subplots(2, 1, figsize=(8, 10))

        plot_boxplot(hs_df, axes[0], 'mode', f'time_{value}',
                     f'QUIC vs TCP Handshake | {control_parameter} = {value}', 'Implementations', 'Time')
        plot_boxplot(conn_df, axes[1], 'mode', f'time_{value}',
                     f'QUIC vs TCP Connection | {control_parameter} = {value}', 'Implementations', 'Time')

        plt.tight_layout()
        plt.savefig(f"{BOXPLOTS_DIR}/boxplots_{value}.png",
                    dpi=300, bbox_inches='tight')
        plt.show()


def show_boxplot(test_results_dataframe, control_parameter):
    create_boxplots_for_each_value_of_independent_variable(
        test_results_dataframe, control_parameter)
