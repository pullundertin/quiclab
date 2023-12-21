import pandas as pd


def get_medians(df):
    median_df = pd.DataFrame()
    group_columns = ['mode', 'size', 'delay', 'delay_deviation', 'loss',
                     'rate', 'firewall', 'window_scaling', 'rmin', 'rmax', 'rdef', 'migration', 'generic_heatmap']
    # Group by group_columns and calculate median across multiple columns
    median_df = df.groupby(group_columns).agg({
        'aioquic_hs': 'median',
        'quicgo_hs': 'median',
        'tcp_hs': 'median',
        'quic_hs': 'median',
        'aioquic_conn': 'median',
        'quicgo_conn': 'median',
        'quic_conn': 'median',
        'tcp_conn': 'median'
    }).reset_index()
    return median_df


def do_statistics(df):
    median_df = get_medians(df)

    return median_df
