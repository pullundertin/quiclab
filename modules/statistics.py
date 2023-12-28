import pandas as pd
import numpy as np
from modules.progress_bar import update_program_progress_bar
from modules.prerequisites import read_configuration

TEST_CONFIG_COLUMNS = read_configuration().get("TEST_CONFIG_COLUMNS")
TEST_RESULT_COLUMNS = read_configuration().get("TEST_RESULT_COLUMNS")

def get_medians(df):
    group_columns = TEST_CONFIG_COLUMNS

    # Define a custom function to calculate median while ignoring NaN values
    def custom_median(series):
        return np.nanmedian(series) if not series.isnull().all() else np.nan

    # Convert relevant columns to numeric, ignoring errors to handle non-convertible values
    numeric_columns = TEST_RESULT_COLUMNS
    
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')


    # Apply the custom median function using agg with skipna parameter
    median_df = df.groupby(group_columns, as_index=False).agg({
        'goodput': lambda x: custom_median(x),
        'aioquic_hs': lambda x: custom_median(x),
        'quicgo_hs': lambda x: custom_median(x),
        'tcp_hs': lambda x: custom_median(x),
        'quic_hs': lambda x: custom_median(x),
        'aioquic_conn': lambda x: custom_median(x),
        'quicgo_conn': lambda x: custom_median(x),
        'quic_conn': lambda x: custom_median(x),
        'tcp_conn': lambda x: custom_median(x)
    })

    return median_df


def do_statistics(df):
    update_program_progress_bar('Do Statistics')

    median_df = get_medians(df)

    return median_df
