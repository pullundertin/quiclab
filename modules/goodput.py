import os
import pandas as pd
import matplotlib.pyplot as plt
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


def show_goodput_graph(df, control_parameter):
    GOODPUT_RESULTS = read_configuration().get("GOODPUT_RESULTS")
    # Group the DataFrame by 'mode'
    grouped_by_mode = df.groupby('mode')
    # TODO sort results?
    # Create a scatterplot for each mode
    control_parameters = ['rmin', 'rdef', 'rmax']
    for mode, group_data in grouped_by_mode:
        for control_parameter in control_parameters:
            for second_variable in control_parameters:
                unique_values_of_second_variable = None
                if second_variable != control_parameter:
                    unique_values_of_second_variable = group_data[second_variable].unique()
                    print(control_parameter, second_variable, unique_values_of_second_variable)
                    fig, axes = plt.subplots(nrows=1, ncols=len(unique_values_of_second_variable), figsize=(15, 5))
                    for index, value in enumerate(unique_values_of_second_variable):
                        dataframe_filtered_by_value_of_second_variable = group_data[(group_data[second_variable] == value)]

                        axes[index].scatter(dataframe_filtered_by_value_of_second_variable[control_parameter], dataframe_filtered_by_value_of_second_variable['goodput'], label=f"{second_variable} = {value}")
                        axes[index].set_title(f'{control_parameter} vs Goodput for {second_variable} = {value} grouped by Mode')
                        axes[index].legend()
                        axes[index].grid(True)
                        axes[index].set_xlabel(control_parameter)
                        axes[index].set_ylabel('Goodput')

                    plt.tight_layout()
                    plt.savefig(f"{GOODPUT_RESULTS}/{second_variable}_{control_parameter}.png", dpi=300, bbox_inches='tight')
                    plt.show()  # Show each plot separately


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
