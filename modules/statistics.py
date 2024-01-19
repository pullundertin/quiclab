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

    # Calculate relationships for each column
    for col in grouped_statistics.columns:
        # Create a new column for each column with the ratio between each value of index control_parameter
        # with different values for index 'mode'
        if not grouped_statistics[col].isnull().any():
            grouped_statistics[f'{col}_tcp_ratio'] = (grouped_statistics[col] /
                                                      grouped_statistics.loc['tcp', col] * 100) - 100 if grouped_statistics.loc['tcp', col].all() != 0 else np.nan

    # Sort the columns
    grouped_statistics = grouped_statistics.sort_index(axis=1).round(2)

    # Drop empty columns
    grouped_statistics_cleaned = grouped_statistics.dropna(axis=1, how='all')

    # Display the resulting DataFrame with calculated relationships
    grouped_statistics_cleaned.to_csv(f'{TEST_RESULTS_DIR}/statistics.csv')


def do_statistics(df, test):
    control_parameter = test.control_parameter
    update_program_progress_bar('Do Statistics')

    get_statistics(df, control_parameter)
    median_df = get_medians(df)

    return median_df
