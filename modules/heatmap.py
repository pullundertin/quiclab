import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statistics


def show_heatmap(statistics_df):
    # Assuming statistics_df is your DataFrame returned from get_statistics()

    # Calculate the ratio of quic_hs median to tcp_hs median
    quic_hs_median = (statistics_df['quic_hs']['median'])
    tcp_hs_median = (statistics_df['tcp_hs']['median'])

    ratio_quic_tcp_hs = (quic_hs_median / tcp_hs_median) * \
        100  # Calculate ratio as a percentage

    # Calculate the ratio of quic_conn median to tcp_conn median
    quic_conn_median = (statistics_df['quic_conn']['median'])
    tcp_conn_median = (statistics_df['tcp_conn']['median'])

    # Calculate ratio as a percentage
    ratio_quic_tcp_conn = (quic_conn_median / tcp_conn_median) * 100

    # Create a DataFrame to hold the ratios with an index
    ratio_df = pd.DataFrame({
        'Aioquic': [ratio_quic_tcp_hs],
    }, index=[0])

    # Plotting the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(ratio_df, annot=True, cmap='YlGnBu', fmt='.2f', cbar=True)
    plt.title('QUIC vs TCP Handshake')
    plt.xlabel('Ratios')
    plt.ylabel('')

    plt.savefig('heatmap_handshake.png', dpi=300, bbox_inches='tight')
