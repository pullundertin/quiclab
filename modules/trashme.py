# Code omitted for brevity




def get_tcp_handshake_time(pcap):
    for packet in pcap:
        if 'TCP' in packet and 'IP' in packet:
            if hasattr(packet, 'tls') and hasattr(packet.tls, 'handshake_type'):
                if packet.tls.handshake_type == '20':
                    return float(packet.frame_info.time_relative)
    return None


def get_tcp_connection_time(pcap):
    # Modify as per your logic
    pass


def get_tcp_rtt_data(pcap):
    # Modify as per your logic
    pass


def get_quic_handshake_time(pcap):
    # Modify as per your logic
    pass


def get_quic_connection_time(pcap):
    # Modify as per your logic
    pass


def get_quic_dcid(pcap):
    # Modify as per your logic
    pass


def get_test_results(test):
    def populate_test_case_with_test_results_from_json(pcap, test_case):
        data = {
            'tcp_rtt': get_tcp_rtt_data(pcap),
            'tcp_hs': get_tcp_handshake_time(pcap),
            'tcp_conn': get_tcp_connection_time(pcap),
            # ... Other data fields
        }
        test_case.store_test_results_for(data)

    # Refactor other functions similarly...

    update_program_progress_bar('Get Test Results')

    pcap_files = traverse_pcap_directory()
    qlog_files = traverse_qlog_directory()

    for pcap_file in pcap_files:
        pcap = capture_packets(pcap_file)
        test_case = test.test_cases_decompressed.map_file_to_test_case(pcap_file)
        populate_test_case_with_test_results_from_json(pcap, test_case)

    # Process qlog files similarly...

# Call get_test_results function
get_test_results(your_test_object)
