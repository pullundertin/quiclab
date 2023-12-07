import pandas as pd
import re
import os


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
    def start_time_with_zero():
        dataframe['time'] = dataframe['time'] - initial_timestamp

    def generate_timestamp_from_unix_timestamp():
        dataframe['time'] = pd.to_datetime(dataframe['time'], unit='s')

    start_time_with_zero()
    generate_timestamp_from_unix_timestamp()
    return dataframe


def create_congestion_window_column(dataframe):
    def copy_cwnd(row):
        if row['src'].startswith(ip_pattern):
            return row['snd_cwnd']
        else:
            return None

    def generate_cwnd_mss_column():
        dataframe['cwnd_mss'] = dataframe.apply(copy_cwnd, axis=1)

    def generate_cwnd_bytes_column():
        dataframe['cwnd_bytes'] = dataframe['cwnd_mss'] * MSS

    generate_cwnd_mss_column()
    generate_cwnd_bytes_column()
    return dataframe


def create_ssthresh_column(dataframe):
    def copy_ssthresh(row):
        if row['src'].startswith(ip_pattern):
            return row['ssthresh']
        else:
            return None

    def generate_ssthresh_mss_column():
        dataframe['ssthresh_mss'] = dataframe.apply(copy_ssthresh, axis=1)

    generate_ssthresh_mss_column()
    return dataframe


def data_sent_by_server(dataframe):
    def copy_data_sent(row):
        if row['dest'].startswith(ip_pattern):
            return row['data_len']
        else:
            return None

    def generate_data_sent_column():
        dataframe['data_sent_bytes'] = dataframe.apply(copy_data_sent, axis=1)

    def generate_cumulated_data_sent_column():
        dataframe['cum_data_sent_bytes'] = dataframe.groupby(['src', 'dest'])[
            'data_sent_bytes'].cumsum()

    generate_data_sent_column()
    generate_cumulated_data_sent_column()
    return dataframe


def acks_sent_by_client(dataframe):
    def create_new_ack_sent_bytes_column_with_all_none():
        dataframe['ack_sent_bytes'] = None

    def get_rows_starting_with_ip_pattern():
        return dataframe[dataframe['src'].str.startswith(ip_pattern)].index.tolist()

    def calculate_acknowledgements(rows):
        for i in range(len(rows) - 1):
            current_index = rows[i]
            next_index = rows[i + 1]

            snd_una_diff = dataframe.loc[next_index, 'snd_una'] - \
                dataframe.loc[current_index, 'snd_una']
            dataframe.at[current_index, 'ack_sent_bytes'] = snd_una_diff

    def calculate_cumulated_acknowledgements():
        dataframe['cum_ack_sent_bytes'] = dataframe['ack_sent_bytes'].cumsum()

    create_new_ack_sent_bytes_column_with_all_none()
    rows = get_rows_starting_with_ip_pattern()
    calculate_acknowledgements(rows)
    calculate_cumulated_acknowledgements()
    return dataframe


def create_client_rcv_wnd_column(dataframe):
    def copy_rcv_wnd(row):
        if row['dest'].startswith(ip_pattern):
            return row['rcv_wnd']
        else:
            return None

    def generate_rcv_wnd_bytes_column():
        dataframe['rcv_wnd_bytes'] = dataframe.apply(copy_rcv_wnd, axis=1)

    def generate_rcv_wnd_mss_column():
        dataframe['rcv_wnd_mss'] = round(dataframe['rcv_wnd_bytes'] / MSS, 1)

    generate_rcv_wnd_bytes_column()
    generate_rcv_wnd_mss_column()
    return dataframe


def create_cum_rcv_wnd_column(dataframe):

    def fill_NaN_values_with_last_known_values():
        columns_to_fill = ['cwnd_mss', 'ssthresh_mss', 'rcv_wnd_mss', 'cwnd_bytes', 'rcv_wnd_bytes',
                           'cum_data_sent_bytes', 'cum_ack_sent_bytes']
        dataframe[columns_to_fill] = dataframe[columns_to_fill].fillna(
            method='ffill')

    def calculate_cum_rcv_wnd_bytes():
        dataframe['cum_rcv_wnd_bytes'] = dataframe['cum_ack_sent_bytes'] + \
            dataframe['rcv_wnd_bytes']

    fill_NaN_values_with_last_known_values()
    calculate_cum_rcv_wnd_bytes()
    return dataframe


def create_minimum_of_cwnd_and_rcv_wnd_column(dataframe):
    def generate_min_wnd_bytes_column():
        dataframe['min_wnd_bytes'] = dataframe[[
            'rcv_wnd_bytes', 'cwnd_bytes']].min(axis=1)

    def generate_min_wnd_mss_column():
        dataframe['min_wnd_mss'] = dataframe[[
            'rcv_wnd_mss', 'cwnd_mss']].min(axis=1)

    generate_min_wnd_bytes_column()
    generate_min_wnd_mss_column()
    return dataframe


def hide_ssthresh_values_greater_than_max_wnd_size(dataframe):
    def maximum_of_cwnd_and_rcv_wnd():
        return dataframe[['rcv_wnd_mss', 'cwnd_mss']].max().max()

    def delete_values_exceeding_threshold(threshold):
        dataframe.loc[dataframe['ssthresh_mss']
                      > threshold, 'ssthresh_mss'] = pd.NA

    threshold = maximum_of_cwnd_and_rcv_wnd()
    delete_values_exceeding_threshold(threshold)
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
    def filter_dataframe_on_selected_columns():
        return dataframe[selected_columns]

    def export_selection(selection):
        selection.to_csv(output_file, index=False)

    selection = filter_dataframe_on_selected_columns()
    export_selection(selection)


def preprocess_data(dataframe):
    dataframe = filter_communication_with_device_under_test(dataframe)
    initial_timestamp = dataframe['time'].iloc[0]
    dataframe = convert_microseconds_to_timestamp(dataframe, initial_timestamp)
    dataframe = create_congestion_window_column(dataframe)
    dataframe = create_ssthresh_column(dataframe)
    dataframe = data_sent_by_server(dataframe)
    dataframe = acks_sent_by_client(dataframe)
    dataframe = create_client_rcv_wnd_column(dataframe)
    dataframe = create_cum_rcv_wnd_column(dataframe)
    dataframe = create_minimum_of_cwnd_and_rcv_wnd_column(dataframe)
    dataframe = hide_ssthresh_values_greater_than_max_wnd_size(dataframe)
    # dataframe = create_rtt_graph(dataframe)
    return dataframe


def process_all_input_files():
    for filename in os.listdir(input_directory):
        if filename.endswith(".log"):
            input_file = os.path.join(input_directory, filename)
            output_file = os.path.join(
                output_directory, f"{os.path.splitext(filename)[0]}.csv")

            dataframe = extract_values_from_log(input_file)
            dataframe = preprocess_data(dataframe)
            export_to_csv(dataframe, output_file, selected_columns)


if __name__ == "__main__":

    pd.options.mode.chained_assignment = None

    input_directory = "/shared/tcpprobe/"
    output_directory = "/shared/tcpprobe/"
    selected_columns = ['time', 'cwnd_bytes', 'rcv_wnd_bytes', 'min_wnd_bytes', 'cwnd_mss', 'rcv_wnd_mss', 'min_wnd_mss', 'ssthresh_mss',  'cum_rcv_wnd_bytes',
                        'data_sent_bytes', 'cum_data_sent_bytes', 'ack_sent_bytes', 'cum_ack_sent_bytes']
    ip_pattern = '172.3.'
    MSS = 1460

    process_all_input_files()
