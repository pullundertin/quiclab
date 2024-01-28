import pandas as pd
import numpy as np
from modules.progress_bar import update_program_progress_bar
from modules.prerequisites import read_configuration

TEST_CONFIG_COLUMNS = read_configuration().get("TEST_CONFIG_COLUMNS")
TEST_RESULT_COLUMNS = read_configuration().get("TEST_RESULT_COLUMNS")
TEST_RESULTS_DIR = read_configuration().get("TEST_RESULTS_DIR")


def filter_columns_to_calculate_statistics_on(df, control_parameter):
    quic_columns = [col for col in df.columns if col.startswith('quic_')]
    # Exclude 'mode' and control_parameter columns from statistics
    columns_to_exclude = TEST_CONFIG_COLUMNS + \
        [control_parameter] + quic_columns
    columns_to_calculate_statistics_on = [
        col for col in df.columns if col not in columns_to_exclude]

    return columns_to_calculate_statistics_on


def generate_statistics_on_test_results(df, control_parameter):

    columns_to_calculate_statistics_on = filter_columns_to_calculate_statistics_on(
        df, control_parameter)

    # Group by 'mode' and control_parameter, then describe the selected columns
    grouped_statistics = df.groupby(['mode', control_parameter])[
        columns_to_calculate_statistics_on].describe()

    # Flatten multi-level columns to a single level
    grouped_statistics.columns = [
        '_'.join(col).strip() for col in grouped_statistics.columns.values]

    return grouped_statistics


def merge_columns_with_the_same_metric(df):
    modes = ['aioquic_', 'quicgo_', 'tcp_']
    result_dict = {}

    for mode in modes:
        # Get column names starting with the current mode
        filtered_columns = [col for col in df.columns if col.startswith(mode)]

        # Extract the part of the column names that comes after the mode
        result_dict[mode] = [col[len(mode):] for col in filtered_columns]

    # Flatten the lists in result_dict.values() and convert to a set to get unique values
    unique_values = set(val for sublist in result_dict.values()
                        for val in sublist)
    columns_to_drop = []
    for value in unique_values:
        columns_to_combine = []
        for key in result_dict.keys():
            columns_to_combine.append(f'{key}{value}')
        df[f'{value}'] = df[columns_to_combine].replace(
            'None', '').sum(1)
        columns_to_drop.append(columns_to_combine)

    # Flatten the list of lists
    columns_to_drop_flat = [
        col for sublist in columns_to_drop for col in sublist]

    # Drop the original columns
    df = df.drop(columns=columns_to_drop_flat)
    return df


def calculate_relationships_for_each_column(merged_df):
    for col in merged_df.columns:
        # Create a new column for each column with the ratio between each value of index control_parameter
        # with different values for index 'mode'
        merged_df[f'{col}_tcp_ratio'] = (merged_df[col] /
                                         merged_df.loc['tcp', col] * 100) - 100
    return merged_df


def sort_statistics(df):
    # Get columns starting with 'Stream '
    stream_cols = [
        col for col in df.columns if col.startswith('Stream')]

    # Convert columns starting with "Stream " to numeric if needed
    df[stream_cols] = df[stream_cols].apply(
        pd.to_numeric, errors='coerce')

    metrics_order = ['goodput', 'hs', 'conn',
                     'link_utilization', 'jfi'] + stream_cols

    statistics_order = ['mean',
                        'std', 'min', '25%',  '50%', '50%_tcp_ratio', '75%', 'max']

    sorted_list_of_columns = []

    for metric in metrics_order:
        # Filter columns by both metrics_order and statistics_order
        columns_filtered_by_metric_and_stat = [
            col for col in df.columns if col.startswith(metric) and any(sub in col for sub in statistics_order)
        ]

        # Sort columns based on the order of metrics_order and within each group by statistics_order
        sorted_columns = sorted(columns_filtered_by_metric_and_stat, key=lambda col: (
            metrics_order.index(metric), [statistics_order.index(sub) for sub in statistics_order if col.endswith(sub)])
        )

        # Append only columns ending with the specified strings from statistics_order
        sorted_list_of_columns.extend(
            col for col in sorted_columns if col.endswith(tuple(statistics_order)))

    sorted_df = df[sorted_list_of_columns]

    return sorted_df

def convert_indicies_back_to_columns(df, control_parameter):
    df.reset_index(inplace=True)

    # convert indicies 'mode' and control_parameter to columns
    df = df.rename(columns={'mode': 'mode', control_parameter: control_parameter})
    return df


def get_statistics(df, control_parameter):

    statistics = generate_statistics_on_test_results(df, control_parameter)
    merged_df = merge_columns_with_the_same_metric(statistics)
    relationships_df = calculate_relationships_for_each_column(merged_df)
    sorted_df = sort_statistics(relationships_df)
    results_df = sorted_df.round(4)
    results_df = convert_indicies_back_to_columns(results_df, control_parameter)
    results_df.to_csv(f'{TEST_RESULTS_DIR}/statistics.csv')
    return results_df


def do_statistics(df, test):
    control_parameter = test.control_parameter
    update_program_progress_bar('Do Statistics')
    tmp_df = df.copy()
    median_df = get_statistics(tmp_df, control_parameter)

    return median_df
