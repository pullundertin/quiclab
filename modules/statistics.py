import pandas as pd
import numpy as np
from modules.progress_bar import update_program_progress_bar


def get_medians(df):
    group_columns = ['mode', 'size', 'delay', 'delay_deviation', 'loss',
                     'rate', 'firewall', 'window_scaling', 'rmin', 'rmax', 'rdef', 'migration', 'generic_heatmap']

    # Define a custom function to calculate median while ignoring NaN values
    def custom_median(series):
        return np.nanmedian(series) if not series.isnull().all() else np.nan

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
