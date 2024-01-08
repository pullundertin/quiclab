from modules.prerequisites import read_configuration
from modules.progress_bar import update_program_progress_bar


def calculate_jains_fairness_index(test):
    update_program_progress_bar('Calculate JFI')
    test_cases = test.test_cases_decompressed.test_cases
    for test_case in test_cases:
        streams = test_case.streams
        sum_of_goodputs_of_all_flows = 0
        sum_of_squared_goodputs_of_each_flow = 0
        for count, stream in enumerate(streams.streams, start=1):
            sum_of_goodputs_of_all_flows += stream.goodput
            sum_of_squared_goodputs_of_each_flow += stream.goodput ** 2
        square_of_sum_of_goodputs_of_all_flows = sum_of_goodputs_of_all_flows ** 2
        jfi = square_of_sum_of_goodputs_of_all_flows / (count * sum_of_squared_goodputs_of_each_flow)
        test_case.update_jfi(jfi)