import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def show_heatmap(df, column_1, column_2, title, filename):
    median_values = {}
    if 'http' in df['mode'].values:
        if 'aioquic' in df['mode'].values:
            median_values['Aioquic'] = df.loc[df['mode'] == 'aioquic',
                                              column_1].values[0] / df.loc[df['mode'] == 'http', column_2].values[0] * 100
        if 'quicgo' in df['mode'].values:
            median_values['Quic-Go'] = df.loc[df['mode'] == 'quicgo',
                                              column_1].values[0] / df.loc[df['mode'] == 'http', column_2].values[0] * 100

    if len(median_values) > 0:  # Check if there are valid values to create the DataFrame
        ratio_df = pd.DataFrame(median_values, index=[0])

        plt.figure(figsize=(8, 6))
        sns.heatmap(ratio_df, annot=True, cmap='YlGnBu', fmt='.2f', cbar=True)
        plt.title(title)
        plt.xlabel('Ratios')
        plt.ylabel('')

        plt.savefig(filename, dpi=300, bbox_inches='tight')
    else:
        print("No data available for the specified modes.")


def show_handshake_heatmap(df):
    show_heatmap(df, 'quic_hs', 'tcp_hs', 'QUIC vs TCP Handshake',
                 'shared/heatmaps/heatmap_handshake.png')


def show_connection_heatmap(df):
    show_heatmap(df, 'quic_conn', 'tcp_conn',
                 'QUIC vs TCP Connection', 'shared/heatmaps/heatmap_connection.png')
