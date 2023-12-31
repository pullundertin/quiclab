import os
import pandas as pd
import matplotlib.pyplot as plt
from modules.prerequisites import read_configuration
from modules.progress_bar import update_program_progress_bar
import re

DOWNLOADS_DIR = read_configuration().get("DOWNLOADS_DIR")


def get_associated_test_case(file_path, test):
    return test.test_cases_decompressed.map_file_to_test_case(file_path)

def get_connection_time(test_case):
    possible_connection_time_fields = ['tcp_conn', 'quic_conn']
    for field in possible_connection_time_fields:

        value = getattr(test_case, field, None)
        if value is not None:
            return value
    return None


def show_goodput_graph(df, control_parameter):
    GOODPUT_RESULTS = read_configuration().get("GOODPUT_RESULTS")
    # Group the DataFrame by 'mode'
    grouped_by_mode = df.groupby('mode')

    # Create a scatterplot for each mode
    plt.figure(figsize=(10, 6))

    for mode, group_data in grouped_by_mode:
        plt.scatter(group_data[control_parameter],
                    group_data['goodput'], label=mode, alpha=0.7)
        plt.plot(group_data[control_parameter], group_data['goodput'],
                 marker='o', linestyle='-', alpha=0.5)

    plt.xlabel(control_parameter)
    plt.ylabel('Goodput')
    plt.title(f'Scatterplot of {control_parameter} vs Goodput grouped by Mode')
    plt.legend()
    plt.grid(True)
    plt.savefig(GOODPUT_RESULTS, dpi=300, bbox_inches='tight')


def calculate_goodput(test):
    update_program_progress_bar('Calculate Goodput')

    def calculate_goodput_per_stream(test_case, download_size):
        streams = test_case.streams
        for stream in streams.streams:
            stream_id = stream.stream_id
            stream = streams.find_stream_by_id(stream_id)
            connection_time = stream.connection_time
            goodput = download_size/connection_time
            stream.update_goodput(goodput)

    def calculate_and_update_goodput(test_case, download_size):
        connection_time = get_connection_time(test_case)
        goodput = download_size / connection_time
        test_case.update_goodput(goodput)

    def get_total_size_of_multi_stream_download(test_case, download_sizes):
        if test_case in download_sizes:
            download_sizes[test_case] += download_size
        else:
            download_sizes[test_case] = download_size
        return download_sizes

    download_sizes = {}  

    for file in os.listdir(DOWNLOADS_DIR):
        file_path = os.path.join(DOWNLOADS_DIR, file)
        if os.path.isfile(file_path):
            test_case = get_associated_test_case(file_path, test)
            download_size = os.path.getsize(file_path)         
            if test_case:
                download_sizes = get_total_size_of_multi_stream_download(test_case, download_sizes)
                calculate_goodput_per_stream(test_case, download_size)


    for test_case, download_size in download_sizes.items():
        calculate_and_update_goodput(test_case, download_size)

