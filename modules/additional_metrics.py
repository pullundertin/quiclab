from modules.progress_bar import update_program_progress_bar

def get_total_goodput(test_case):
    download_size_total = test_case.real_size
    if test_case.mode == 'tcp':
        connection_time_total = test_case.tcp_conn
    elif test_case.mode == 'aioquic':
        connection_time_total = test_case.aioquic_conn
    elif test_case.mode == 'quicgo':
        connection_time_total = test_case.quicgo_conn

    goodput_total = float(download_size_total / connection_time_total)
    goodput_total = round(goodput_total, 4)
    test_case.update_property('goodput', goodput_total)  

def get_per_stream_goodput(test_case):
    download_size_per_stream = test_case.size
    streams = test_case.streams.streams
    for stream in streams:
        connection_time_per_stream = stream.connection_time
        goodput_per_stream = float(download_size_per_stream / connection_time_per_stream)
        goodput_per_stream = round(goodput_per_stream, 4)
        stream.update_goodput(goodput_per_stream)   

def get_total_link_utilization(test_case):
    bandwidth_total = test_case.rate * 1024 * 1024 / 8
    goodput_total = test_case.goodput
    link_utilization_total = float(goodput_total / bandwidth_total)
    link_utilization_total = round(link_utilization_total, 4)    
    test_case.update_property('link_utilization', link_utilization_total)     

def get_per_stream_link_utilization(test_case):
    bandwidth_total = test_case.rate * 1024 * 1024 / 8
    streams = test_case.streams.streams
    for stream in streams:
        goodput_per_stream = stream.goodput
        link_utilization_per_stream = float(goodput_per_stream / bandwidth_total)
        link_utilization_per_stream = round(link_utilization_per_stream, 4)
        stream.update_link_utilization(link_utilization_per_stream)   

def calculate_jains_fairness_index(test_case):
    streams = test_case.streams.streams
    sum_of_goodputs_of_all_flows = 0
    sum_of_squared_goodputs_of_each_flow = 0
    for count, stream in enumerate(streams, start=1):
        sum_of_goodputs_of_all_flows += stream.goodput
        sum_of_squared_goodputs_of_each_flow += stream.goodput ** 2
    square_of_sum_of_goodputs_of_all_flows = sum_of_goodputs_of_all_flows ** 2
    jfi = float(square_of_sum_of_goodputs_of_all_flows / (count * sum_of_squared_goodputs_of_each_flow))
    jfi = round(jfi, 4)
    test_case.update_jfi(jfi)

def calculate_additional_metrics(test):
    update_program_progress_bar('Calculate additional Metrics')
    test_cases = test.test_cases_decompressed.test_cases

    for test_case in test_cases:
        get_total_goodput(test_case)
        get_per_stream_goodput(test_case)
        get_total_link_utilization(test_case)
        get_per_stream_link_utilization(test_case)
        calculate_jains_fairness_index(test_case)