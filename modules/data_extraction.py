import pandas as pd
import os
import logging
import json
import pyshark
from modules.commands import run_command
from modules.prerequisites import read_configuration
from modules.progress_bar import update_program_progress_bar


PCAP_PATH = read_configuration().get("PCAP_PATH")
KEYS_PATH = read_configuration().get("KEYS_PATH")
QLOG_PATH_CLIENT = read_configuration().get("QLOG_PATH_CLIENT")
SERVER_IP = read_configuration().get("SERVER_IP")
CLIENT_1_IP = read_configuration().get("CLIENT_1_IP")

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)



def traverse_pcap_directory():
    return [os.path.join(PCAP_PATH, filename) for filename in os.listdir(PCAP_PATH) if filename.endswith('client_1.pcap')]


def traverse_qlog_directory():
    return [os.path.join(QLOG_PATH_CLIENT, filename) for filename in os.listdir(QLOG_PATH_CLIENT) if filename.endswith('.qlog')]

def capture_packets(pcap_file):
    with pyshark.FileCapture(pcap_file, override_prefs={'tls.keylog_file': KEYS_PATH}) as pcap:
        return list(pcap)
    
def get_tcp_handshake_time(pcap):
    for packet in pcap:
        if 'TCP' in packet and 'IP' in packet:
            if hasattr(packet, 'tls') and hasattr(packet.tls, 'handshake_type'):
                if packet.tls.handshake_type == '20':
                    return packet.frame_info.time_relative


def get_tcp_connection_time(pcap):
    tcp_connection_duration = None
    fin_ack_seq = None


    def check_if_fin_flag_is_set(hex_value):
        # Perform bitwise AND with 0x01 to check the last bit
        if int(hex_value, 16) & 0x01:
            return True
        else:
            return False

    def find_ack_of_server_fin_packet(pcap):
        for packet in pcap:
            if 'TCP' in packet and 'IP' in packet:
                ip_src = packet.ip.src
                tcp_flags = packet.tcp.flags
                tcp_fin_flag = check_if_fin_flag_is_set(tcp_flags)
                ack_raw = packet.tcp.ack_raw

                if ip_src == SERVER_IP and tcp_fin_flag:
                    fin_ack_seq = ack_raw
                    return fin_ack_seq

    def find_packet_matching_this_ack(fin_ack_seq, pcap):
        for packet in pcap:
            if 'TCP' in packet and 'IP' in packet:
                ip_src = packet.ip.src
                seq_raw_packet = (packet.tcp.seq_raw)
                if ip_src == CLIENT_1_IP and seq_raw_packet == fin_ack_seq:
                    time_relative = float(packet.frame_info.time_relative)
                    if time_relative > 0:
                        tcp_connection_duration = time_relative
                        
                        return tcp_connection_duration

    fin_ack_seq = find_ack_of_server_fin_packet(pcap)
    tcp_connection_duration = find_packet_matching_this_ack(fin_ack_seq, pcap)
    return tcp_connection_duration
    

def get_tcp_single_stream_connection_time(json_file):
    pass


def get_tcp_rtt_data(pcap):
    rtt_values = []
    for packet in pcap:
        if 'TCP' in packet and 'IP' in packet:
            if hasattr(packet.tcp, 'analysis_ack_rtt'):
                ack_rtt = packet.tcp.analysis_ack_rtt
                ip_src = packet.ip.src
                if (ip_src == SERVER_IP):
                    rtt_values.append(float(ack_rtt))

    return rtt_values



def get_quic_handshake_time(pcap):
    quic_handshake_start = None
    quic_handshake_end = None
    quic_handshake_duration = None
    for packet in pcap:
        if 'QUIC' in packet:
            quic_handshake_start = float(packet.frame_info.time_relative)
            break
    for packet in pcap:
        if 'QUIC' in packet:
            if hasattr(packet, 'quic') and hasattr(packet.quic, 'tls_handshake_type'):
                if packet.quic.tls_handshake_type == '20':
                    quic_handshake_end = float(packet.frame_info.time_relative)
                    quic_handshake_duration = quic_handshake_end - quic_handshake_start
                    break
    return quic_handshake_duration


def get_quic_connection_time(pcap):
    quic_connection_start = None
    quic_connection_end = None
    quic_connection_duration = None

    for packet in pcap:
        if 'QUIC' in packet:
            quic_connection_start = float(packet.frame_info.time_relative)
            break
    for packet in pcap:
        if 'QUIC' in packet:
            if hasattr(packet, 'quic') and hasattr(packet.quic, 'frame_type'):
                if packet.quic.frame_type == '29':
                    quic_connection_end = float(packet.frame_info.time_relative)
                    quic_connection_duration = quic_connection_end - quic_connection_start
                    break
      
    return quic_connection_duration



def get_quic_dcid(pcap):
    quic_dcid = None
    quic_dcid_ascii = None
    for packet in pcap:
        if 'QUIC' in packet and hasattr(packet.quic, 'dcid'):
            quic_dcid_string = packet.quic.dcid
            quic_dcid_ascii = quic_dcid_string.replace(":", "")
            quic_dcid = bytes(quic_dcid_ascii, 'utf-8').hex()
            break
    return quic_dcid, quic_dcid_ascii


def get_test_results(test):

    def populate_test_case_with_test_results_from_json(pcap, test_case):
        
        data = {
            'tcp_rtt': get_tcp_rtt_data(pcap),
            'tcp_hs': get_tcp_handshake_time(pcap),
            'tcp_conn': get_tcp_connection_time(pcap),
            'quic_hs': get_quic_handshake_time(pcap),
            'quic_conn': get_quic_connection_time(pcap),
            'dcid': get_quic_dcid(pcap)[0],
            'dcid_hex': get_quic_dcid(pcap)[1]
        }



        if test_case.mode == 'aioquic':
            data['aioquic_hs'] = get_quic_handshake_time(pcap)
            data['aioquic_conn'] = get_quic_connection_time(pcap)
        elif test_case.mode == 'quicgo':
            data['quicgo_hs'] = get_quic_handshake_time(pcap)
            data['quicgo_conn'] = get_quic_connection_time(pcap)

        test_case.store_test_results_for(data)


    def iterate_over_pcap_files_and_get_associated_test_case(files):
        for pcap_file in files:
            test_case = test.test_cases_decompressed.map_file_to_test_case(
                pcap_file)
            populate_test_case_with_test_results_from_json(
                pcap_file, test_case)

    def get_pcap_data():
        files = traverse_pcap_directory()
        iterate_over_pcap_files_and_get_associated_test_case(files)

    def get_qlog_data():

        qlog_files = traverse_qlog_directory()
        min_rtt_values = []
        smoothed_rtt_values = []

        def get_dataframe_index_of_qlog_file(qlog_file):
            test_case = test.test_cases_decompressed.map_qlog_file_to_test_case_by_dcid(
                qlog_file)
            return test_case

        for qlog_file in qlog_files:
            min_rtt_values = []
            smoothed_rtt_values = []
            try:
                with open(qlog_file, 'r') as f:
                    data = f.read()
                    qlog_data = json.loads(data)

                if isinstance(qlog_data, dict) and 'traces' in qlog_data:
                    for packet in qlog_data['traces']:
                        for event in packet.get('events', []):
                            data = event.get('data', {})
                            if 'min_rtt' in data:
                                min_rtt = data.get('min_rtt')
                                min_rtt_values.append(min_rtt / 1000)
                                smoothed_rtt = data.get('smoothed_rtt')
                                smoothed_rtt_values.append(smoothed_rtt / 1000)

            # ndjson format - quicgo
            except json.JSONDecodeError:
                with open(qlog_file, 'r') as f:
                    ndqlog_data = f.read()
                    # Split the data into lines and parse each line as JSON
                    for line in ndqlog_data.strip().split('\n'):
                        qlog_data = json.loads(line)
                        if "data" in qlog_data:
                            if "min_rtt" in qlog_data["data"]:
                                min_rtt_values.append(
                                    qlog_data["data"]["min_rtt"]/1000)
                                smoothed_rtt_values.append(
                                    qlog_data["data"]["smoothed_rtt"]/1000)

            test_case = get_dataframe_index_of_qlog_file(qlog_file)
            test_case.update_quic_rtt_data_from_qlog(
                min_rtt_values, smoothed_rtt_values)

    update_program_progress_bar('Get Test Results')

    pcap_files = traverse_pcap_directory()

    for pcap_file in pcap_files:
        pcap = capture_packets(pcap_file)
        test_case = test.test_cases_decompressed.map_file_to_test_case(pcap_file)
        populate_test_case_with_test_results_from_json(pcap, test_case)

    get_qlog_data()