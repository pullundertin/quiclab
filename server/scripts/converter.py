import pandas as pd
import re


def extract_values_from_log(input_file):
    with open(input_file, 'r') as file:
        log_data = file.read()

    pattern = re.compile(
        r'(\d+\.\d+): tcp_probe: family=AF_INET src=([^ ]+) dest=([^ ]+) .* data_len=([^ ]+) snd_nxt=([^ ]+) snd_una=([^ ]+) snd_cwnd=([^ ]+) ssthresh=([^ ]+) .* srtt=([^ ]+) rcv_wnd=([^ ]+)')
    matches = pattern.findall(log_data)

    extracted_data = {
        'time': [float(match[0]) for match in matches],
        'src': [match[1] for match in matches],
        'dest': [match[2] for match in matches],
        'data_len': [int(match[3]) for match in matches],
        'snd_nxt': [int(match[4], 16) for match in matches],
        'snd_una': [int(match[5], 16) for match in matches],
        'cwnd': [int(match[6]) for match in matches],
        'ssthresh': [int(match[7]) for match in matches],
        'srtt': [int(match[8]) for match in matches],
        'rcv_wnd': [int(match[9]) for match in matches]
    }

    return pd.DataFrame(extracted_data)


def filter_communication_with_device_under_test(dataframe):
    return dataframe[dataframe['src'].str.contains(ip_pattern) | dataframe['dest'].str.contains(ip_pattern)]


def convert_microseconds_to_timestamp(dataframe, initial_timestamp):
    print(initial_timestamp)
    dataframe['time'] = dataframe['time'] * 1000
    dataframe['time'] = pd.to_datetime(dataframe['time'], unit='s')
    # dataframe['time'] = dataframe['time'] - dataframe['time'].min()
    return dataframe


def filter_data_sent_by_client(dataframe):
    return dataframe[dataframe['src'].str.contains(ip_pattern)]


def filter_data_sent_by_server(dataframe):
    return dataframe[dataframe['dest'].str.contains(ip_pattern)]


def create_congestion_window_column(dataframe):
    client_cwnd = {ip_pattern: 0}
    for index, row in dataframe.iterrows():
        if ip_pattern in row['src']:
            client_cwnd[ip_pattern] = row['snd_cwnd'] * MSS
            dataframe.at[index, 'cwnd'] = 0
        else:
            dataframe.at[index, 'cwnd'] = client_cwnd[ip_pattern]

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


def create_cumulated_receive_window_column(dataframe):
    # Calculate the difference between 'snd_nxt' and 'snd_una' and add it as a new column
    dataframe['cum_rcv_wnd'] = dataframe['cum_ack_sent'] + \
        dataframe['rcv_wnd']
    return dataframe


def create_minimum_of_cwnd_and_rcv_wnd_column(dataframe):
    dataframe['min_wnd'] = dataframe[['rcv_wnd', 'cwnd']].min(axis=1)
    return dataframe


def export_to_csv(dataframe, output_file):
    dataframe.to_csv(output_file, index=False)


def data_sent_by_server(dataframe):
    # Function to copy 'data_len' values to 'data_sent' for rows where 'src' starts with '172.1.'
    def copy_data_sent(row):
        if row['src'].startswith('172.1.'):
            return row['data_len']
        else:
            return None

    # Apply the function to create 'data_sent' column
    dataframe['data_sent'] = dataframe.apply(copy_data_sent, axis=1)
    # # Rename 'data_len' column
    # dataframe['data_sent'] = dataframe['data_len']
    # # Delete rows where 'data_sent' is equal to 0
    # dataframe = dataframe[dataframe['data_sent'] != 0]

    # Calculate cumulated data sent
    dataframe['cum_data_sent'] = dataframe.groupby(['src', 'dest'])[
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
    dataframe['cum_ack_sent'] = dataframe.groupby(['src', 'dest'])[
        'ack_sent'].cumsum()
    return dataframe


def calculate_ack_sent(dataframe):
    # Create a new column 'ack_sent' and fill it with None
    dataframe['ack_sent'] = None
    # Get indices of rows with src starting with '172.3'
    src_indices = dataframe[dataframe['src'].str.startswith(
        '172.3')].index.tolist()

    for i in range(len(src_indices) - 1):
        current_index = src_indices[i]
        next_index = src_indices[i + 1]

        snd_una_diff = dataframe.loc[next_index, 'snd_una'] - \
            dataframe.loc[current_index, 'snd_una']
        dataframe.at[current_index, 'ack_sent'] = snd_una_diff

    return dataframe


def add_mss_based_window_values(dataframe, column):
    mss_column_name = f'{column}_mss'
    dataframe[mss_column_name] = dataframe[column] / MSS
    return dataframe


if __name__ == "__main__":

    pd.options.mode.chained_assignment = None
    input_file = "/shared/tcpprobe/server.log"
    output_file = "/shared/tcpprobe/results.csv"
    output_directory = "/shared/tcpprobe/"
    ip_pattern = '172.3.'
    MSS = 1460

    dataframe = extract_values_from_log(input_file)
    dataframe = filter_communication_with_device_under_test(dataframe)

    initial_timestamp = dataframe['time'].min()
    dataframe = convert_microseconds_to_timestamp(dataframe, initial_timestamp)
    # dataframe = update_rcv_wnd_values_for_server(dataframe)
    # dataframe = create_congestion_window_column(dataframe)

    # server_dataframe = filter_data_sent_by_server(dataframe)
    # data_len (data_sent), cum_data_sent, rcv_wnd (client)
    dataframe = data_sent_by_server(dataframe)
    # export_to_csv(server_dataframe, '/shared/tcpprobe/server.csv')

    # client_dataframe = filter_data_sent_by_client(dataframe)
    # cwnd, ssthresh, ack_sent (nxt - una), cum_ack_sent
    # dataframe = acks_sent_by_client(dataframe)
    dataframe = calculate_ack_sent(dataframe)
    export_to_csv(dataframe, '/shared/tcpprobe/shared.csv')

    # client_dataframe = create_cumulated_receive_window_column(
    #     client_dataframe)
    # export_to_csv(client_dataframe, '/shared/tcpprobe/client.csv')
    # server_dataframe = create_minimum_of_cwnd_and_rcv_wnd_column(
    #     server_dataframe)
    # client_dataframe = add_mss_based_window_values(client_dataframe, 'rcv_wnd')
    # server_dataframe = add_mss_based_window_values(server_dataframe, 'cwnd')
    # server_dataframe = add_mss_based_window_values(server_dataframe, 'min_wnd')
    # server_selection = server_dataframe[[
    #     'time', 'data_sent', 'cum_data_sent', 'cwnd', 'min_wnd', 'cwnd_mss', 'min_wnd_mss']]

    # client_selection = client_dataframe[[
    #     'time', 'ack_sent', 'cum_ack_sent', 'cwnd', 'rcv_wnd', 'cum_rcv_wnd', 'rcv_wnd_mss', 'ssthresh']]

    # export_to_csv(server_selection, '/shared/tcpprobe/server.csv')
    # export_to_csv(client_selection, '/shared/tcpprobe/client.csv')
