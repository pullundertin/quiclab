import pandas as pd
import numpy as np
from modules.progress_bar import update_program_progress_bar
from modules.prerequisites import read_configuration

TEST_CONFIG_COLUMNS = read_configuration().get("TEST_CONFIG_COLUMNS")
TEST_RESULT_COLUMNS = read_configuration().get("TEST_RESULT_COLUMNS")


def get_medians(test_results_dataframe):
    group_columns = TEST_CONFIG_COLUMNS

    # Define a custom function to calculate median while ignoring NaN values
    def custom_median(series):
        return np.nanmedian(series) if not series.isnull().all() else np.nan

    # Convert relevant columns to numeric, ignoring errors to handle non-convertible values
    numeric_columns = TEST_RESULT_COLUMNS

    test_results_dataframe_copy = test_results_dataframe.copy()
    test_results_dataframe_copy[numeric_columns] = test_results_dataframe_copy[numeric_columns].apply(
        pd.to_numeric, errors='coerce')
    # Get columns starting with 'Stream '
    stream_cols = [
        col for col in test_results_dataframe_copy.columns if col.startswith('Stream')]

    # Convert columns starting with "Stream " to numeric if needed
    test_results_dataframe_copy[stream_cols] = test_results_dataframe_copy[stream_cols].apply(
        pd.to_numeric, errors='coerce')

    # Apply the custom median function using agg with skipna parameter
    agg_columns = {
        col: lambda x: custom_median(x) for col in numeric_columns + stream_cols
    }

    median_df = test_results_dataframe_copy.groupby(
        group_columns, as_index=False).agg(agg_columns)

    return median_df


def sort_statistics(df):
    metrics_order = ['goodput', 'aioquic_hs', 'aioquic_conn',
                     'quicgo_hs', 'quicgo_conn', 'tcp_hs', 'tcp_conn']

    statistics_order = ['mean', 'mean_tcp_ratio',
                        'std', 'min', '25%', '50%', '75%', 'max']

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


def sort_merged_df(df):
    # Get the columns ending with '_tcp_ratio'
    tcp_ratio_columns = [
        col for col in df.columns if col.endswith('_tcp_ratio')]

    # Create a list of tuples where each tuple contains the column without '_tcp_ratio' and its corresponding column with '_tcp_ratio'
    sorted_columns = [(col.replace('_tcp_ratio', ''), col)
                      for col in tcp_ratio_columns]

    # Flatten the list of tuples
    sorted_columns_flat = [col for pair in sorted_columns for col in pair]

    # Select the sorted columns and other remaining columns
    sorted_df = df[sorted_columns_flat +
                   [col for col in df.columns if col not in sorted_columns_flat]]

    return sorted_df


def merge_columns_with_the_same_stat(df):
    modes = ['aioquic_', 'quicgo_', 'tcp_']

    # Get column names starting with elements from the list
    filtered_columns = [col for col in df.columns if any(
        col.startswith(mode) for mode in modes)]

    # Initialize an empty dictionary to store results
    result_dict = {}

    # Iterate through each mode
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

    # Drop the specified columns
    df = df.drop(columns=columns_to_drop_flat)
    return df


def get_statistics(df, control_parameter):

    TEST_RESULTS_DIR = read_configuration().get('TEST_RESULTS_DIR')

    # Exclude 'mode' and control_parameter columns from statistics
    columns_to_exclude = ['mode', control_parameter]
    columns_to_calculate_statistics_on = [
        col for col in df.columns if col not in columns_to_exclude]

    # Group by 'mode' and control_parameter, then describe the selected columns
    grouped_statistics = df.groupby(['mode', control_parameter])[
        columns_to_calculate_statistics_on].describe()

    # Flatten multi-level columns to a single level
    grouped_statistics.columns = [
        '_'.join(col).strip() for col in grouped_statistics.columns.values]

    grouped_statistics = sort_statistics(grouped_statistics).round(4)

    merged_df = merge_columns_with_the_same_stat(grouped_statistics)
    # Calculate relationships for each column
    for col in merged_df.columns:
        # Create a new column for each column with the ratio between each value of index control_parameter
        # with different values for index 'mode'
        merged_df[f'{col}_tcp_ratio'] = (merged_df[col] /
                                         merged_df.loc['tcp', col] * 100) - 100
    sorted_merged_df = sort_merged_df(merged_df)
    sorted_merged_df.to_csv(f'{TEST_RESULTS_DIR}/statistics.csv')


def do_statistics(df, test):
    control_parameter = test.control_parameter
    update_program_progress_bar('Do Statistics')

    get_statistics(df, control_parameter)
    median_df = get_medians(df)

    return median_df
