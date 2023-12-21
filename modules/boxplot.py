
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from modules.prerequisites import read_configuration
from scipy.stats import ttest_ind

BOXPLOTS_DIR = read_configuration().get("BOXPLOTS_DIR")
T_TEST_RESULTS = read_configuration().get("T_TEST_RESULTS")


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


def t_test(df, control_parameter):
    for value in df[control_parameter].unique():
        # Filter the DataFrame based on the current unique value
        filtered_df = df[df[control_parameter] == value]
        # hs_df = combine_quic_and_tcp_values_for(filtered_df, 'hs', value)

        tcp_series = filtered_df[filtered_df['mode'] == 'tcp']
        tcp_hs_samples = tcp_series['tcp_hs'].tolist()
        tcp_conn_samples = tcp_series['tcp_conn'].tolist()

        aioquic_series = filtered_df[filtered_df['mode'] == 'aioquic']
        aioquic_quic_hs_samples = aioquic_series['aioquic_hs'].tolist()
        aioquic_quic_conn_samples = aioquic_series['aioquic_conn'].tolist()

        quicgo_series = filtered_df[filtered_df['mode'] == 'quicgo']
        quicgo_quic_hs_samples = quicgo_series['quicgo_hs'].tolist()
        quicgo_quic_conn_samples = quicgo_series['quicgo_conn'].tolist()

        perform_t_test(tcp_hs_samples, aioquic_quic_hs_samples,
                       f'Handshake TCP vs Aioquic | {control_parameter} = {value}')
        perform_t_test(tcp_hs_samples, quicgo_quic_hs_samples,
                       f'Handshake TCP vs Quicgo | {control_parameter} = {value}')
        perform_t_test(tcp_conn_samples, aioquic_quic_conn_samples,
                       f'Connection TCP vs Aioquic | {control_parameter} = {value}')
        perform_t_test(tcp_conn_samples, quicgo_quic_conn_samples,
                       f'Connection TCP vs Quicgo | {control_parameter} = {value}')


def perform_t_test(samples_1, samples_2, name):
    # Perform independent t-test
    t_statistic, p_value = ttest_ind(
        samples_1, samples_2)

    # Set your desired alpha level
    ALPHA = read_configuration().get("ALPHA")

    if p_value < ALPHA:
        evaluation = f"Reject null hypothesis: There is a significant difference between the groups {name}."
    else:
        evaluation = f"Fail to reject null hypothesis: There is no significant difference between the groups {name}."

    output = f"""
    T-statistic: {t_statistic}
    P-value: {p_value}
    Significance: {evaluation}
"""
    with open(T_TEST_RESULTS, 'a') as file:
        file.write(output)


def show_boxplot(df, control_parameter):
    """Create and display separate boxplots for handshake and connection times."""

    create_boxplots_for_each_value_of_independent_variable(
        df, control_parameter)
    # t_test(df, control_parameter)
