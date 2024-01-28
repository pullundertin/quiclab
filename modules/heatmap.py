
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from modules.prerequisites import read_configuration

HEATMAPS_DIR = read_configuration().get("HEATMAPS_DIR")


def save_heatmap(df, control_parameter, column_to_compare, name):
    # Pivot the DataFrame
    pivoted_df = df.pivot(index=control_parameter, columns='mode',
                          values=column_to_compare)

    # Plotting the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(pivoted_df, annot=True, cmap='YlGnBu', fmt='.2f', cbar=True)
    plt.title(f'QUIC vs TCP {name}')
    plt.xlabel('Implementations')
    plt.ylabel(control_parameter)

    plt.savefig(f"{HEATMAPS_DIR}/{name}.png", dpi=300, bbox_inches='tight')


def show_heatmaps(df, control_parameter):
    save_heatmap(df[df['mode'].isin(['aioquic', 'quicgo'])],
                 control_parameter, 'hs_50%_tcp_ratio', 'Handshake')
    save_heatmap(df[df['mode'].isin(['aioquic', 'quicgo'])],
                 control_parameter, 'conn_50%_tcp_ratio', 'Connection')
