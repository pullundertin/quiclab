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
        'snd_cwnd': [int(match[6]) for match in matches],
        'ssthresh': [int(match[7]) for match in matches],
        'srtt': [int(match[8]) for match in matches],
        'rcv_wnd': [int(match[9]) for match in matches]
    }

    return pd.DataFrame(extracted_data)


def filter_communication_with_device_under_test(dataframe):
    return dataframe[dataframe['src'].str.contains(ip_pattern) | dataframe['dest'].str.contains(ip_pattern)]


def convert_microseconds_to_timestamp(dataframe, initial_timestamp):
    dataframe['time'] = dataframe['time'] - initial_timestamp
    dataframe['time'] = pd.to_datetime(dataframe['time'], unit='s')
    return dataframe


def create_congestion_window_column(dataframe):
    # Function to copy 'data_len' values to 'data_sent' for rows where 'src' starts with '172.1.'
    def copy_cwnd(row):
        if row['src'].startswith('172.3.'):
            return row['snd_cwnd']
        else:
            return None

    # Apply the function to create 'data_sent' column
    dataframe['cwnd_mss'] = dataframe.apply(copy_cwnd, axis=1)

    return dataframe


def create_ssthresh_column(dataframe):
    def copy_ssthresh(row):
        if row['src'].startswith('172.3.'):
            return row['ssthresh']
        else:
            return None

    # Apply the function to create 'data_sent' column
    dataframe['ssthresh_mss'] = dataframe.apply(copy_ssthresh, axis=1)

    return dataframe


def data_sent_by_server(dataframe):
    # Function to copy 'data_len' values to 'data_sent_bytes' for rows where 'src' starts with '172.1.'
    def copy_data_sent(row):
        if row['src'].startswith('172.1.'):
            return row['data_len']
        else:
            return None

    # Apply the function to create 'data_sent_bytes' column
    dataframe['data_sent_bytes'] = dataframe.apply(copy_data_sent, axis=1)

    # Calculate cumulated data sent
    dataframe['cum_data_sent_bytes'] = dataframe.groupby(['src', 'dest'])[
        'data_sent_bytes'].cumsum()
    return dataframe


def acks_sent_by_client(dataframe):
    # Create a new column 'ack_sent' and fill it with None
    dataframe['ack_sent_bytes'] = None
    # Get indices of rows with src starting with '172.3'
    src_indices = dataframe[dataframe['src'].str.startswith(
        '172.3')].index.tolist()

    for i in range(len(src_indices) - 1):
        current_index = src_indices[i]
        next_index = src_indices[i + 1]

        snd_una_diff = dataframe.loc[next_index, 'snd_una'] - \
            dataframe.loc[current_index, 'snd_una']
        dataframe.at[current_index, 'ack_sent_bytes'] = snd_una_diff

    # Calculate cumulated acknowledgements
    # Convert 'ack_sent_bytes' column to float for calculations
    dataframe['ack_sent_bytes'] = dataframe['ack_sent_bytes'].astype(float)
    dataframe['cum_ack_sent_bytes'] = dataframe['ack_sent_bytes'].astype(
        float).cumsum()  # Create 'cum_ack_sent_bytes' column with cumulative sum

    return dataframe


def create_client_rcv_wnd_column(dataframe):
    def copy_rcv_wnd(row):
        if row['src'].startswith('172.1.'):
            return row['rcv_wnd']
        else:
            return None

    # Apply the function to create 'data_sent' column
    dataframe['rcv_wnd_bytes'] = dataframe.apply(copy_rcv_wnd, axis=1)
    return dataframe


def fill_NaN_values_with_last_known_values(dataframe):
    columns_to_fill = ['cwnd_mss', 'ssthresh_mss', 'rcv_wnd_bytes',
                       'cum_data_sent_bytes', 'cum_ack_sent_bytes']
    dataframe[columns_to_fill] = dataframe[columns_to_fill].fillna(
        method='ffill')
    return dataframe


def create_cum_rcv_wnd_column(dataframe):
    dataframe['cum_rcv_wnd_bytes'] = dataframe['cum_ack_sent_bytes'] + \
        dataframe['rcv_wnd_bytes']

    return dataframe


def create_minimum_of_cwnd_and_rcv_wnd_column(dataframe):
    dataframe['rcv_wnd_mss'] = round(dataframe['rcv_wnd_bytes'] / MSS, 1)
    dataframe['cwnd_bytes'] = dataframe['cwnd_mss'] * MSS
    dataframe['min_wnd_bytes'] = dataframe[[
        'rcv_wnd_bytes', 'cwnd_bytes']].min(axis=1)
    dataframe['min_wnd_mss'] = dataframe[[
        'rcv_wnd_mss', 'cwnd_mss']].min(axis=1)
    return dataframe


def hide_ssthresh_values_greater_than_max_wnd_size(dataframe):
    def maximum_of_cwnd_and_rcv_wnd(dataframe):
        return dataframe[['rcv_wnd_mss', 'cwnd_mss']].max().max()

    def delete_values_exceeding_threshold(dataframe, threshold):
        dataframe.loc[dataframe['ssthresh_mss']
                      > threshold, 'ssthresh_mss'] = pd.NA
        return dataframe

    threshold = maximum_of_cwnd_and_rcv_wnd(dataframe)
    dataframe = delete_values_exceeding_threshold(dataframe, threshold)
    return dataframe

# def create_rtt_graph(dataframe):
#     threshold = pd.Timedelta(milliseconds=10)  # Adjust the threshold as needed
#     round_trip_counter = 0

#     prev_time = None
#     for index, row in dataframe.iterrows():
#         if prev_time is not None:
#             time_diff = row['time'] - prev_time
#             if time_diff > threshold:
#                 round_trip_counter += 1
#         prev_time = row['time']
#         dataframe.at[index, 'rtt'] = int(round_trip_counter)

#     return dataframe


def export_to_csv(dataframe, output_file, selected_columns=None):
    if selected_columns:
        selected_dataframe = dataframe[selected_columns]
        selected_dataframe.to_csv(output_file, index=False)
    else:
        dataframe.to_csv(output_file, index=False)


if __name__ == "__main__":

    pd.options.mode.chained_assignment = None
    input_file = "/shared/tcpprobe/server.log"
    output_file = "/shared/tcpprobe/tcptrace.csv"
    output_directory = "/shared/tcpprobe/"
    ip_pattern = '172.3.'
    # client-side: data_len (data_sent), cum_data_sent, rcv_wnd (client), cum_rcv_wnd
    # server-side: cwnd, ssthresh, ack_sent (nxt - una), cum_ack_sent
    MSS = 1460

    dataframe = extract_values_from_log(input_file)

    dataframe = filter_communication_with_device_under_test(dataframe)

    initial_timestamp = dataframe['time'].iloc[0]
    dataframe = convert_microseconds_to_timestamp(dataframe, initial_timestamp)
    dataframe = create_congestion_window_column(dataframe)
    dataframe = create_ssthresh_column(dataframe)

    dataframe = data_sent_by_server(dataframe)

    dataframe = acks_sent_by_client(dataframe)

    dataframe = create_client_rcv_wnd_column(dataframe)
    dataframe = fill_NaN_values_with_last_known_values(dataframe)
    dataframe = create_cum_rcv_wnd_column(dataframe)
    dataframe = create_minimum_of_cwnd_and_rcv_wnd_column(dataframe)
    dataframe = hide_ssthresh_values_greater_than_max_wnd_size(dataframe)
    # dataframe = create_rtt_graph(dataframe)
    selected_columns = ['time', 'cwnd_bytes', 'rcv_wnd_bytes', 'min_wnd_bytes', 'cwnd_mss', 'rcv_wnd_mss', 'min_wnd_mss', 'ssthresh_mss',  'cum_rcv_wnd_bytes',
                        'data_sent_bytes', 'cum_data_sent_bytes', 'ack_sent_bytes', 'cum_ack_sent_bytes']

    export_to_csv(dataframe, output_file, selected_columns)
