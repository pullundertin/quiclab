
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from modules.prerequisites import read_configuration
import re

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


def create_boxplot(df, ax, x_data, y_data, title, xlabel, ylabel):
    """Create a single boxplot for the specified axes."""
    sns.boxplot(ax=ax, x=x_data, y=y_data, data=df.dropna())
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def create_boxplots_for_each_single_stream(df, test):

    def extend_y_axis_margin(y_value):
        margin = 0.2
        y_values_min = y_value.min()
        y_values_max = y_value.max()
        y_values_range = y_values_max - y_values_min
        y_axis_min = y_values_min - (y_values_range * margin)
        if y_axis_min < 0:
            y_axis_min = 1000
        y_axis_max = y_values_max + (y_values_range * margin)

        return y_axis_min, y_axis_max

    # Find columns that match the pattern 'Stream_ID_<number>_goodput'
    stream_columns = [col for col in df.columns if col.startswith(
        'Stream_ID_') and col.endswith('_goodput')]

    # Get unique combinations of 'mode' and 'control_parameter' from the 'test' object
    modes = df['mode'].unique()
    control_parameter = test.control_parameter
    if not control_parameter:
        return
    control_parameters = df[control_parameter].unique()

    # Set up the figure for subplots based on the number of modes and control parameters
    for control_param in control_parameters:
        fig, axs = plt.subplots(1, len(modes), figsize=(12, 8), sharey=False)

        for i, mode in enumerate(modes):
            mode_control_df = df[(df['mode'] == mode) & (
                df[control_parameter] == control_param)]
            non_nan_columns = [
                col for col in stream_columns if mode_control_df[col].notnull().any()]

            if non_nan_columns:
                stream_ids = [int(re.search(
                    r'Stream_ID_(\d+)_goodput', col).group(1)) for col in non_nan_columns]
                sorted_cols = [col for _, col in sorted(
                    zip(stream_ids, non_nan_columns))]

                mode_control_df_melted = mode_control_df.melt(
                    id_vars=['mode', control_parameter], value_vars=non_nan_columns, var_name='Stream_ID')
                mode_control_df_melted['value'] = mode_control_df_melted['value'].astype(
                    float)
                mode_control_df_melted = mode_control_df_melted.sort_values(
                    'value')
                y_axis_min, y_axis_max = extend_y_axis_margin(
                    mode_control_df_melted['value'])

                x_labels = [col.replace('_goodput', '') for col in sorted_cols]

                sns.boxplot(data=mode_control_df_melted.dropna(),
                            x='Stream_ID', y='value', palette='Set3', ax=axs[i])
                axs[i].set_title(
                    f'Mode: {mode}, Control Parameter: {control_param}')
                axs[i].set_xlabel('Streams')
                axs[i].set_ylabel('Goodput')
                axs[i].set_yscale('log')
                axs[i].set_xticks(range(len(non_nan_columns)))
                axs[i].set_xticklabels(x_labels, rotation=90)
                axs[i].legend().set_visible(False)
                axs[i].set_ylim(y_axis_min, y_axis_max)

            plt.tight_layout()
            plt.savefig(f"{BOXPLOTS_DIR}/streams_{control_param}.png",
                        dpi=300, bbox_inches='tight')


def create_link_utilization_boxplots_for_each_single_stream(df, test):

    def extend_y_axis_margin(y_value):
        margin = 0.2
        y_values_min = y_value.min()
        y_values_max = y_value.max()
        y_values_range = y_values_max - y_values_min
        y_axis_min = y_values_min - (y_values_range * margin)
        if y_axis_min < 0:
            y_axis_min = 1000
        y_axis_max = y_values_max + (y_values_range * margin)

        return y_axis_min, y_axis_max

    # Find columns that match the pattern 'Stream_ID_<number>_goodput'
    stream_columns = [col for col in df.columns if col.startswith(
        'Stream_ID_') and col.endswith('_link_utilization')]

    # Get unique combinations of 'mode' and 'control_parameter' from the 'test' object
    modes = df['mode'].unique()
    control_parameter = test.control_parameter
    if not control_parameter:
        return

    control_parameters = df[control_parameter].unique()

    # Set up the figure for subplots based on the number of modes and control parameters
    for control_param in control_parameters:
        fig, axs = plt.subplots(1, len(modes), figsize=(12, 8), sharey=False)

        for i, mode in enumerate(modes):
            mode_control_df = df[(df['mode'] == mode) & (
                df[control_parameter] == control_param)]
            non_nan_columns = [
                col for col in stream_columns if mode_control_df[col].notnull().any()]

            if non_nan_columns:
                stream_ids = [int(re.search(
                    r'Stream_ID_(\d+)_link_utilization', col).group(1)) for col in non_nan_columns]
                sorted_cols = [col for _, col in sorted(
                    zip(stream_ids, non_nan_columns))]

                mode_control_df_melted = mode_control_df.melt(
                    id_vars=['mode', control_parameter], value_vars=non_nan_columns, var_name='Stream_ID')
                mode_control_df_melted['value'] = mode_control_df_melted['value'].astype(
                    float)
                mode_control_df_melted = mode_control_df_melted.sort_values(
                    'value')
                y_axis_min, y_axis_max = extend_y_axis_margin(
                    mode_control_df_melted['value'])

                x_labels = [col.replace('_link_utilization', '')
                            for col in sorted_cols]

                sns.boxplot(data=mode_control_df_melted.dropna(),
                            x='Stream_ID', y='value', palette='Set3', ax=axs[i])
                axs[i].set_title(
                    f'Mode: {mode}, Control Parameter: {control_param}')
                axs[i].set_xlabel('Streams')
                axs[i].set_ylabel('Link Utilization')
                axs[i].set_xticks(range(len(non_nan_columns)))
                axs[i].set_xticklabels(x_labels, rotation=90)
                axs[i].legend().set_visible(False)
                axs[i].set_ylim(y_axis_min, y_axis_max)

            plt.tight_layout()
            plt.savefig(
                f"{BOXPLOTS_DIR}/streams_link_utilization_{control_param}.png", dpi=300, bbox_inches='tight')


def create_boxplots_for_each_value_of_independent_variable(df, test):

    def check_if_test_performs_on_a_series_of_control_parameter(control_parameter_values):
        if isinstance(control_parameter_values, list) and len(control_parameter_values) > 1:
            return True
        else:
            return False

    def check_if_tests_have_one_mode_only_and_return_that_mode(df):
        unique_modes = df['mode'].unique()

        if len(unique_modes) == 1:
            return unique_modes[0]
        else:
            return None

    def filter_dataframe_based_on_mode_and_control_parameter(df, mode, control_parameter):
        filtered_df = df[df['mode'] == mode]
        filtered_df = (
            filtered_df[[control_parameter, f'{mode}_hs', f'{mode}_conn', 'goodput']])
        return filtered_df

    def create_boxplot_for_single_mode(filtered_df, mode, control_parameter):
        fig, axes = plt.subplots(3, 1, figsize=(8, 10))

        create_boxplot(filtered_df, axes[0], control_parameter, f'{mode}_hs',
                       f'{mode} handshake with different values for {control_parameter}', control_parameter, 'time')

        create_boxplot(filtered_df, axes[1], control_parameter, f'{mode}_conn',
                       f'{mode} connection with different values for {control_parameter}', control_parameter, 'time')

        create_boxplot(filtered_df, axes[2], control_parameter, 'goodput',
                       f'{mode} goodput with different values for {control_parameter}', control_parameter, 'B/s')

        plt.tight_layout()
        plt.savefig(f"{BOXPLOTS_DIR}/boxplot_{mode}_{control_parameter}.png",
                    dpi=300, bbox_inches='tight')

    control_parameter = test.control_parameter
    control_parameter_values = test.control_parameter_values
    single_mode_test = check_if_tests_have_one_mode_only_and_return_that_mode(
        df)

    if single_mode_test:
        if check_if_test_performs_on_a_series_of_control_parameter(control_parameter_values):
            filtered_df = filter_dataframe_based_on_mode_and_control_parameter(
                df, single_mode_test, control_parameter)
            create_boxplot_for_single_mode(
                filtered_df, single_mode_test, control_parameter)
        else:
            print("no boxplot")

    elif control_parameter is not None:
        for value in df[control_parameter].unique():
            filtered_df = df[df[control_parameter] == value]

            hs_df = combine_quic_and_tcp_values_for(filtered_df, 'hs', value)
            conn_df = combine_quic_and_tcp_values_for(
                filtered_df, 'conn', value)

            fig, axes = plt.subplots(2, 1, figsize=(8, 10))
            plot_boxplot(hs_df, axes[0], 'mode', f'time_{value}',
                         f'QUIC vs TCP Handshake | {control_parameter} = {value}', 'Implementations', 'Time')
            plot_boxplot(conn_df, axes[1], 'mode', f'time_{value}',
                         f'QUIC vs TCP Connection | {control_parameter} = {value}', 'Implementations', 'Time')

            plt.tight_layout()
            plt.savefig(f"{BOXPLOTS_DIR}/boxplots_{value}.png",
                        dpi=300, bbox_inches='tight')


def create_jfi_boxplots(df, test):
    control_parameter = test.control_parameter
    if control_parameter:
        for value in df[control_parameter].unique():
            filtered_df = df[df[control_parameter] == value]
            plt.figure(figsize=(10, 6))
            sns.boxplot(x='mode', y='jfi', data=filtered_df)
            plt.tight_layout()
            plt.savefig(f"{BOXPLOTS_DIR}/jfi_boxplots_{value}.png",
                        dpi=300, bbox_inches='tight')
    else:
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='mode', y='jfi', data=df)
        plt.tight_layout()
        plt.savefig(f"{BOXPLOTS_DIR}/jfi_boxplots.png",
                    dpi=300, bbox_inches='tight')


def show_boxplot(test_results_dataframe, test):
    create_boxplots_for_each_value_of_independent_variable(
        test_results_dataframe, test)
    create_jfi_boxplots(test_results_dataframe, test)
    create_link_utilization_boxplots_for_each_single_stream(
        test_results_dataframe, test)
    create_boxplots_for_each_single_stream(test_results_dataframe, test)
