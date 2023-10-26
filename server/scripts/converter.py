import pandas as pd
import re


pd.options.mode.chained_assignment = None

input_file = "/shared/tcpprobe/server.log"
output_file = "/shared/tcpprobe/results.csv"
output_directory = "/shared/tcpprobe/"
ip_pattern = '172.3.'
MSS = 1460


def extract_values_from_log(input_file):
    with open(input_file, 'r') as file:
        log_data = file.read()

    pattern = r'(\d+\.\d+): tcp_probe: family=AF_INET src=([^ ]+) dest=([^ ]+) .* data_len=([^ ]+) snd_nxt=([^ ]+) snd_una=([^ ]+) snd_cwnd=([^ ]+) ssthresh=([^ ]+) .* srtt=([^ ]+) rcv_wnd=([^ ]+)'

    matches = re.findall(pattern, log_data)

    extracted_data = {
        'time': [float(match[0]) for match in matches],
        'src': [match[1] for match in matches],
        'host': [match[2] for match in matches],
        'data_len': [int(match[3]) for match in matches],
        'snd_nxt': [int(match[4], 16) for match in matches],
        'snd_una': [int(match[5], 16) for match in matches],
        'snd_cwnd': [int(match[6]) for match in matches],
        'ssthresh': [int(match[7]) for match in matches],
        'srtt': [int(match[8]) for match in matches],
        'rcv_wnd': [int(match[9]) for match in matches]
    }

    return pd.DataFrame(extracted_data)


def filter_communication_with_device_under_test(dataframe):
    return dataframe[dataframe['src'].str.contains(ip_pattern) | dataframe['host'].str.contains(ip_pattern)]


def convert_microseconds_to_timestamp(dataframe):
    dataframe['time'] = dataframe['time'] * 2000
    dataframe['time'] = pd.to_datetime(dataframe['time'], unit='s')

    return dataframe


def filter_data_sent_by_client(dataframe):
    return dataframe[dataframe['src'].str.contains(ip_pattern)]


def filter_data_sent_by_server(dataframe):
    return dataframe[dataframe['host'].str.contains(ip_pattern)]


def create_congestion_window_column(dataframe):
    client_cwnd = {ip_pattern: 0}

    def calculate_client_cwnd(row):
        nonlocal client_cwnd
        if ip_pattern in row['src']:
            client_cwnd[ip_pattern] = row['snd_cwnd'] * MSS
            return 0
        else:
            return client_cwnd[ip_pattern]

    dataframe['cwnd'] = dataframe.apply(calculate_client_cwnd, axis=1)

    # Remove temporary columns
    dataframe.drop(
        columns=['snd_cwnd'], inplace=True)

    return dataframe


def update_rcv_wnd_values_for_server(dataframe):

    # Iterate through the DataFrame and update rcv_wnd values for src 172.3.0.5 based on src 172.1.0.101
    last_known_rcv_wnd = None
    for index, row in dataframe.iterrows():
        if ip_pattern not in row['src']:
            last_known_rcv_wnd = row['rcv_wnd']
        elif ip_pattern in row['src'] and last_known_rcv_wnd is not None:
            dataframe.at[index, 'rcv_wnd'] = last_known_rcv_wnd

    return dataframe


def create_cumulated_receive_window_column(client_dataframe):
    # Calculate the difference between 'snd_nxt' and 'snd_una' and add it as a new column
    client_dataframe['cum_rcv_wnd'] = client_dataframe['cum_ack_sent'] + \
        client_dataframe['rcv_wnd']
    return client_dataframe


def create_minimum_of_cwnd_and_rcv_wnd_column(dataframe):
    dataframe['min_wnd'] = dataframe[['rcv_wnd', 'cwnd']].min(axis=1)
    return dataframe


def export_to_csv(dataframe, output_file):
    dataframe.to_csv(output_file, index=False)


def data_sent_by_server(dataframe):
    # Rename 'data_len' column
    dataframe['data_sent'] = dataframe['data_len']
    # Delete rows where 'data_sent' is equal to 0
    dataframe = dataframe[dataframe['data_sent'] != 0]

    # Calculate cumulated data sent
    dataframe['cum_data_sent'] = dataframe.groupby(['src', 'host'])[
        'data_sent'].cumsum()
    return dataframe


def acks_sent_by_client(dataframe):

    # Calculate the acknowledgements as difference between snd_una and the succeeding snd_una value
    dataframe['ack_sent'] = dataframe['snd_una'].shift(
        -1) - dataframe['snd_una']

    # Remove NaN values in the 'ack_sent' column (last row where there is no succeeding row)
    dataframe = dataframe.dropna(subset=['ack_sent'])

    # Delete rows where 'ack_sent' is equal to 0
    dataframe = dataframe[dataframe['ack_sent'] != 0]

    # Calculate cumulated acknowledgements
    dataframe['cum_ack_sent'] = dataframe.groupby(['src', 'host'])[
        'ack_sent'].cumsum()
    return dataframe


if __name__ == "__main__":
    dataframe = extract_values_from_log(input_file)
    dataframe = convert_microseconds_to_timestamp(dataframe)
    dataframe = filter_communication_with_device_under_test(dataframe)
    dataframe = update_rcv_wnd_values_for_server(dataframe)
    dataframe = create_congestion_window_column(dataframe)
    server_dataframe = filter_data_sent_by_server(dataframe)
    client_dataframe = filter_data_sent_by_client(dataframe)
    server_dataframe = data_sent_by_server(server_dataframe)
    client_dataframe = acks_sent_by_client(client_dataframe)
    client_dataframe = create_cumulated_receive_window_column(
        client_dataframe)
    server_dataframe = create_minimum_of_cwnd_and_rcv_wnd_column(
        server_dataframe)

    server_selection = server_dataframe[[
        'time', 'data_sent', 'cum_data_sent', 'cwnd', 'min_wnd']]
    client_selection = client_dataframe[[
        'time', 'ack_sent', 'cum_ack_sent', 'rcv_wnd', 'cum_rcv_wnd']]

    export_to_csv(server_selection, '/shared/tcpprobe/server.csv')
    export_to_csv(client_selection, '/shared/tcpprobe/client.csv')
