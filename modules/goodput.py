import os
from modules.prerequisites import read_configuration
from modules.progress_bar import update_program_progress_bar

DOWNLOADS_DIR = read_configuration().get("DOWNLOADS_DIR")


def get_associated_test_case(file_path, test):
    return test.test_cases_decompressed.map_file_to_test_case(file_path)


def get_download_size_of_file(file_path):
    return os.path.getsize(file_path)


def get_connection_time(test_case):
    possible_connection_time_fields = ['tcp_conn', 'quic_conn']
    for field in possible_connection_time_fields:

        value = getattr(test_case, field, None)
        if value is not None:
            return value
    return None


def calculate_goodput(test):
    update_program_progress_bar('Calculate Goodput')

    for file in os.listdir(DOWNLOADS_DIR):
        file_path = os.path.join(DOWNLOADS_DIR, file)
        if os.path.isfile(file_path):
            test_case = get_associated_test_case(file_path, test)
            download_size = get_download_size_of_file(file_path)
            connection_time = get_connection_time(test_case)
            goodput = download_size / connection_time
            test_case.update_goodput(goodput)
