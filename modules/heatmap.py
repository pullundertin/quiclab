
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


def calculate_percentage(df, metric, quic_column, tcp_column, dependend_variable):
    df[metric] = df.apply(lambda row: row[quic_column] / df.loc[(df['mode'] == 'http') & (
        df[dependend_variable] == row[dependend_variable]), tcp_column].values[0] * 100 if row['mode'] in ['aioquic', 'quicgo'] else np.nan, axis=1)
    return df


def exclude_http_mode_from_heatmap(df):
    return df[df['mode'] != 'http']


def generate_heatmap(metric, df, dependend_variable):
    return df.pivot(
        index=dependend_variable, columns='mode', values=metric)


def save_heatmap(z_value, name, metric):
    # Plotting the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(z_value, annot=True, cmap='YlGnBu', fmt='.2f', cbar=True)
    plt.title(f'QUIC vs TCP {name}')
    plt.xlabel('Implementations')
    plt.ylabel(metric)
    plt.show()

    plt.savefig(f"shared/heatmaps/{name}.png", dpi=300, bbox_inches='tight')


def show_heatmaps(df, metric):

    df = calculate_percentage(df, 'percentage_hs', 'quic_hs', 'tcp_hs', metric)
    df = calculate_percentage(df, 'percentage_conn',
                              'quic_conn', 'tcp_conn', metric)
    print(df)
    filtered_df = exclude_http_mode_from_heatmap(df)
    percentage_hs = generate_heatmap('percentage_hs', filtered_df, metric)
    percentage_conn = generate_heatmap('percentage_conn', filtered_df, metric)

    save_heatmap(percentage_hs, 'Handshake', metric)
    save_heatmap(percentage_conn, 'Connection', metric)
