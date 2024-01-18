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
    test_results_dataframe_copy[numeric_columns] = test_results_dataframe_copy[numeric_columns].apply(pd.to_numeric, errors='coerce')
    # Get columns starting with 'Stream '
    stream_cols = [col for col in test_results_dataframe_copy.columns if col.startswith('Stream')]

    # Convert columns starting with "Stream " to numeric if needed
    test_results_dataframe_copy[stream_cols] = test_results_dataframe_copy[stream_cols].apply(pd.to_numeric, errors='coerce')

    # Apply the custom median function using agg with skipna parameter
    agg_columns = {
        col: lambda x: custom_median(x) for col in numeric_columns + stream_cols
    }

    median_df = test_results_dataframe_copy.groupby(group_columns, as_index=False).agg(agg_columns)

    return median_df

def get_statistics_for_df(df, control_parameter):
    TEST_RESULTS_DIR = read_configuration().get('TEST_RESULTS_DIR')
    TEST_RESULT_COLUMNS = read_configuration().get('TEST_RESULT_COLUMNS')
    stream_columns = [col for col in df.columns if col.startswith('Stream_ID_') and col.endswith('_goodput')]
    columns_to_print = TEST_RESULT_COLUMNS + stream_columns
    filtered_df = df.copy()
    # Group by 'mode' and calculate statistics
    grouped_statistics = filtered_df.groupby(['mode', control_parameter])
    grouped_statistics = grouped_statistics[columns_to_print].describe()
    grouped_statistics = grouped_statistics.round(4)

    # Save grouped statistics to CSV
    grouped_statistics.to_csv(f'{TEST_RESULTS_DIR}/statistics.csv')


def do_statistics(df, test):
    control_parameter = test.control_parameter
    update_program_progress_bar('Do Statistics')
   
    get_statistics_for_df(df, control_parameter)
    median_df = get_medians(df)

    return median_df
