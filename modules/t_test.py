
from modules.prerequisites import read_configuration
from scipy.stats import ttest_ind
import os

T_TEST_RESULTS = read_configuration().get("T_TEST_RESULTS")


def t_test(df, control_parameter):

    if os.path.exists(T_TEST_RESULTS):
        os.remove(T_TEST_RESULTS)

    for value in df[control_parameter].unique():
        # Filter the DataFrame based on the current unique value
        filtered_df = df[df[control_parameter] == value]
        # hs_df = combine_quic_and_tcp_values_for(filtered_df, 'hs', value)
        tcp_series = filtered_df[filtered_df['mode'] == 'tcp']
        tcp_hs_samples = tcp_series['tcp_hs'].tolist()
        tcp_conn_samples = tcp_series['tcp_conn'].tolist()

        aioquic_series = filtered_df[filtered_df['mode'] == 'aioquic']
        aioquic_quic_hs_samples = aioquic_series['aioquic_hs'].tolist()
        aioquic_quic_conn_samples = aioquic_series['aioquic_conn'].tolist()

        quicgo_series = filtered_df[filtered_df['mode'] == 'quicgo']
        quicgo_quic_hs_samples = quicgo_series['quicgo_hs'].tolist()
        quicgo_quic_conn_samples = quicgo_series['quicgo_conn'].tolist()

        perform_t_test(tcp_hs_samples, aioquic_quic_hs_samples,
                       f'Handshake TCP vs Aioquic | {control_parameter} = {value}')
        perform_t_test(tcp_hs_samples, quicgo_quic_hs_samples,
                       f'Handshake TCP vs Quicgo | {control_parameter} = {value}')
        perform_t_test(tcp_conn_samples, aioquic_quic_conn_samples,
                       f'Connection TCP vs Aioquic | {control_parameter} = {value}')
        perform_t_test(tcp_conn_samples, quicgo_quic_conn_samples,
                       f'Connection TCP vs Quicgo | {control_parameter} = {value}')


def perform_t_test(samples_1, samples_2, name):

    # Perform independent t-test
    t_statistic, p_value = ttest_ind(
        samples_1, samples_2)

    # Set your desired alpha level
    ALPHA = read_configuration().get("ALPHA")

    if p_value < ALPHA:
        evaluation = f"Reject null hypothesis: There is a significant difference between the groups {name}."
    else:
        evaluation = f"Fail to reject null hypothesis: There is no significant difference between the groups {name}."

    output = f"""
    T-statistic: {t_statistic}
    P-value: {p_value}
    Significance: {evaluation}
"""
    with open(T_TEST_RESULTS, 'a') as file:
        file.write(output)
