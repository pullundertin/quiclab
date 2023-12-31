
import re


class Test:
    def __init__(self):
        self.iterations = None
        self.test_cases_compressed = None
        self.test_cases_decompressed = TestCases()
        self.control_parameter = None
        self.control_parameter_values = None
        self.total_number_of_test_cases = 0

    def update_total_number_of_test_cases(self, total_number_of_test_cases):
        setattr(self, 'total_number_of_test_cases', total_number_of_test_cases)

    def __str__(self):
        return f"Iterations: {self.iterations}\nControl Parameter: {self.control_parameter}, Control Parameter Values: {self.control_parameter_values}\nNumber of Test Cases: {self.total_number_of_test_cases}\nTest Cases: {self.test_cases_decompressed}"


class TestCases:
    def __init__(self):
        self.test_cases = []

    def add_test_case(self, test_case):
        self.test_cases.append(test_case)

    def __str__(self):
        test_cases = "\n".join(str(test_case) for test_case in self.test_cases)
        return f"\n{test_cases}"

    def map_file_to_test_case(self, json_file):
        matching_test_case = None
        # Extracting Number and Iteration from the JSON file name using regular expressions
        match = re.match(r'.*Case_(\d+)_Iteration_(\d+)_', json_file)
        if match:
            extracted_number = int(match.group(1))
            extracted_iteration = int(match.group(2))

            # Searching for the matching TestCase object
            matching_test_case = next((test_case for test_case in self.test_cases if test_case.number ==
                                      extracted_number and test_case.iteration == extracted_iteration), None)

        return matching_test_case

    def map_qlog_file_to_test_case_by_dcid(self, qlog_file):
        matching_test_case = None
        for test_case in self.test_cases:
            dcid = test_case.dcid
            dcid_hex = test_case.dcid_hex
            if dcid != None and (dcid in qlog_file or dcid_hex in qlog_file):
                matching_test_case = test_case
        return matching_test_case


class TestCase:
    def __init__(self, number, config):
        self.number = number
        self.iteration = config['iteration']
        self.file_name_prefix = f"Case_{self.number}_Iteration_{self.iteration}_"
        self.mode = config['mode']
        self.number_of_streams = config['number_of_streams']
        self.streams = Streams()
        self.size = self.convert_to_bytes(config['size'])
        self.real_size = self.get_real_file_size_based_on_single_or_multi_stream()
        self.delay = config['delay']
        self.delay_deviation = config['delay_deviation']
        self.loss = config['loss']
        self.rate = config['rate']
        self.firewall = config['firewall']
        self.window_scaling = config['window_scaling']
        self.rmin = config['rmin']
        self.rdef = config['rdef']
        self.rmax = config['rmax']
        self.migration = config['migration']
        self.generic_heatmap = config['generic_heatmap']
        self.goodput = None
        self.tcp_rtt = None
        self.tcp_hs = None
        self.tcp_conn = None
        self.quic_min_rtt = None
        self.quic_smoothed_rtt = None
        self.aioquic_hs = None
        self.aioquic_conn = None
        self.quicgo_hs = None
        self.quicgo_conn = None
        self.quic_hs = None
        self.quic_conn = None
        self.dcid = None
        self.dcid_hex = None

    def __str__(self):
        return f"""
        Test Case: {self.number}, 
        Iteration: {self.iteration}, 

        Settings: 
        Mode: {self.mode}
        Size: {self.size}
        Number of Streams: {self.number_of_streams}
        Streams: {self.streams}
        Real Size (Multistream): {self.real_size}
        Delay: {self.delay}
        Delay Deviation: {self.delay_deviation}
        Loss: {self.loss}
        Rate: {self.rate}
        Firewall: {self.firewall}
        Window Scaling: {self.window_scaling}
        Receive Window Min: {self.rmin}
        Receive Window Default: {self.rdef}
        Receive Window Max: {self.rmax}
        Connection Migration: {self.migration}
        Generic: {self.generic_heatmap}

        Test Results:
        Goodput: {self.goodput}

        TCP RTT: {self.tcp_rtt}
        TCP Handshake Time: {self.tcp_hs}
        TCP Connection Time: {self.tcp_conn}

        QUIC DCID: {self.dcid}
        QUIC DCID hex: {self.dcid_hex}
        QUIC Min RTT: {self.quic_min_rtt}
        QUIC Smoothed RTT: {self.quic_smoothed_rtt}
        QUIC Handshake Time: {self.quic_hs}
        QUIC Connection Time: {self.quic_conn}
        # AIOQUIC Handshake Time: {self.aioquic_hs}
        # QUIC-GO Handshake Time: {self.quicgo_hs}
        # AIOQUIC Connection Time: {self.aioquic_conn}
        # QUIC-GO Connection Time: {self.quicgo_conn}
        """

    def convert_to_bytes(self, value):
        units = {'K': 1024, 'M': 1024 ** 2, 'G': 1024 ** 3}
        multiplier = units.get(value[-1].upper(), 1)
        number = float(value[:-1])
        return int(number * multiplier)
    
    def get_real_file_size_based_on_single_or_multi_stream(self):
        if self.number_of_streams > 1:
            return self.number_of_streams * self.size
        else:
            return self.size

    def store_test_results_for(self, test_results):
        for key, value in test_results.items():
            setattr(self, key, value)

    def update_quic_rtt_data_from_qlog(self, min_rtt_values, smoothed_rtt_values):
        self.quic_min_rtt = min_rtt_values
        self.quic_smoothed_rtt = smoothed_rtt_values

    def update_goodput(self, goodput):
        setattr(self, 'goodput', goodput)

    def add_streams(self, streams):
        setattr(self, 'streams', streams)


class Streams:
    def __init__(self):
        self.streams = set()

    def add_stream(self, stream):
        self.streams.add(stream)

    def find_stream_by_id(self, stream_id):
        for stream in self.streams:
            if stream.stream_id == stream_id:
                return stream
        return None


    def __str__(self):
        streams = "\n".join(str(stream) for stream in self.streams)
        return f"\n{streams}"

class Stream:
    def __init__(self, stream_id):
        self.stream_id = stream_id
        self.request_time = None
        self.response_time = None
        self.connection_time = None

    def update_request_time(self, request_time):
        setattr(self, 'request_time', request_time)

    def update_response_time(self, response_time):
        setattr(self, 'response_time', response_time)
        setattr(self, 'connection_time', self.response_time - self.request_time)

    def __str__(self):
        return f"\t\tStream ID: {self.stream_id}, Request Time: {self.request_time}, Response Time: {self.response_time}, Connection Time: {self.connection_time}"

    def __eq__(self, other):
        if isinstance(other, Stream):
            return (self.stream_id == other.stream_id and
                    self.request_time == other.request_time and
                    self.response_time == other.response_time and
                    self.connection_time == other.connection_time)
        return False

    def __hash__(self):
        return hash((self.stream_id, self.request_time, self.response_time, self.connection_time))