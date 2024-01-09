import pandas as pd
import os
import json
import pyshark
from modules.prerequisites import read_configuration
from modules.progress_bar import update_program_progress_bar
from modules.classes import Stream
from collections import defaultdict
import time


PCAP_PATH = read_configuration().get("PCAP_PATH")
KEYS_PATH = read_configuration().get("KEYS_PATH")
QLOG_PATH_CLIENT = read_configuration().get("QLOG_PATH_CLIENT")
SERVER_IP = read_configuration().get("SERVER_IP")
CLIENT_1_IP = read_configuration().get("CLIENT_1_IP")

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)


def traverse_pcap_directory():
    # return [os.path.join(PCAP_PATH, filename) for filename in os.listdir(PCAP_PATH) if filename.endswith('client_1.pcap')]
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('client_1.pcap'):
            yield os.path.join(PCAP_PATH, filename)


def traverse_qlog_directory():
    return [os.path.join(QLOG_PATH_CLIENT, filename) for filename in os.listdir(QLOG_PATH_CLIENT) if filename.endswith('.qlog')]


def capture_packets(pcap_file):
    with pyshark.FileCapture(pcap_file, override_prefs={'tcp.analyze_sequence_numbers': 'TRUE', 'transum.reassembly': 'TRUE', 'tls.keylog_file': 'shared/keys/client.key', 'tcp.reassemble_out_of_order': 'TRUE', 'tcp.desegment_tcp_streams': 'TRUE',  'tls.desegment_ssl_application_data': 'TRUE', 'tls.desegment_ssl_records': 'TRUE'}) as pcap:
        for packet in pcap:
            yield packet


def get_tcp_handshake_time(pcap):
    for packet in pcap:
        if 'TCP' in packet and 'IP' in packet:
            if hasattr(packet, 'tls') and hasattr(packet.tls, 'handshake_type'):
                if packet.tls.handshake_type == '20':
                    tcp_handshake_time = float(packet.frame_info.time_relative)
                    tcp_handshake_time = round(tcp_handshake_time, 3)
                    return tcp_handshake_time


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
                    time_relative = round(time_relative, 3)
                    if time_relative > 0:
                        tcp_connection_duration = time_relative

                        return tcp_connection_duration

    fin_ack_seq = find_ack_of_server_fin_packet(pcap)
    tcp_connection_duration = find_packet_matching_this_ack(fin_ack_seq, pcap)
    return tcp_connection_duration


def check_all_fields(packet, layer):
    if packet.__contains__(layer):
        fields = packet.get_multiple_layers(layer)
        return fields


def get_tcp_single_stream_connection_time(pcap, test_case):
    def get_request_time_for_each_stream(packet, streams):
        fields = check_all_fields(packet, 'http2')
        if fields:
            for field in fields:
                if hasattr(field, 'headers.method'):
                    stream_id = field.streamid
                    stream = streams.find_stream_by_id(stream_id)
                    request_time = float(packet.frame_info.time_relative)
                    stream.update_request_time(request_time)

    def get_response_time_for_each_stream(packet, streams):
        fields = check_all_fields(packet, 'http2')
        if fields:
            for field in fields:
                # and field.flags_end_stream == '1':
                if hasattr(field, 'body_reassembled_data'):
                    stream_id = packet.http2.streamid
                    stream = streams.find_stream_by_id(stream_id)
                    response_time = float(packet.frame_info.time_relative)
                    stream.update_response_time(response_time)
                    connection_time = response_time - stream.request_time
                    stream.update_connection_time(connection_time)

    streams = test_case.streams

    for packet in pcap:
        get_request_time_for_each_stream(packet, streams)
        get_response_time_for_each_stream(packet, streams)


def get_tcp_rtt_data(pcap):
    rtt_values = []
    for packet in pcap:
        if 'TCP' in packet and 'IP' in packet:
            if hasattr(packet.tcp, 'analysis_ack_rtt'):
                ack_rtt = float(packet.tcp.analysis_ack_rtt)
                ack_rtt = round(ack_rtt, 3)

                ip_src = packet.ip.src
                if (ip_src == SERVER_IP):

                    rtt_values.append(ack_rtt)

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
                    quic_handshake_duration = round(quic_handshake_duration, 3)

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
                    quic_connection_end = float(
                        packet.frame_info.time_relative)
                    quic_connection_duration = quic_connection_end - quic_connection_start
                    quic_connection_duration = round(
                        quic_connection_duration, 3)

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


def get_http2_streams(pcap, test_case):
    streams = test_case.streams
    for packet in pcap:
        fields = check_all_fields(packet, 'http2')
        if fields:
            for field in fields:
                if hasattr(field, 'headers.method'):
                    stream_id = field.streamid
                    new_stream = Stream(stream_id)
                    streams.add_stream(new_stream)

    return streams


def get_test_results(test):

    def populate_test_case_with_test_results_from_json(pcap, test_case):

        data = {
            'streams': get_http2_streams(pcap, test_case),
            'tcp_rtt': get_tcp_rtt_data(pcap),
            'tcp_hs': get_tcp_handshake_time(pcap),
            'tcp_conn': get_tcp_connection_time(pcap),
            'quic_hs': get_quic_handshake_time(pcap),
            'quic_conn': get_quic_connection_time(pcap),
            'dcid': get_quic_dcid(pcap)[0],
            'dcid_hex': get_quic_dcid(pcap)[1],
        }

        if test_case.mode in ('aioquic', 'quicgo'):
            mode = test_case.mode
            data[f'{mode}_hs'] = get_quic_handshake_time(pcap)
            data[f'{mode}_conn'] = get_quic_connection_time(pcap)

        test_case.store_test_results_for(data)
        get_tcp_single_stream_connection_time(pcap, test_case)

    def get_pcap_data():
        update_program_progress_bar('Get PCAP Data')
        pcap_files = traverse_pcap_directory()

        for pcap_file in pcap_files:
            pcap = capture_packets(pcap_file)
            test_case = test.test_cases_decompressed.map_file_to_test_case(
                pcap_file)
            populate_test_case_with_test_results_from_json(
                pcap, test_case)

    def get_qlog_data():
        update_program_progress_bar('Get QLOG Data')
        qlog_files = traverse_qlog_directory()

        def get_qlog_stream_data_from_aioquic(qlog_data):
            timestamps_by_stream_id = defaultdict(list)
            if isinstance(qlog_data, dict) and 'traces' in qlog_data:
                for packet in qlog_data['traces']:
                    for qlog_event in packet.get('events', []):
                        timestamps_by_stream_id = get_timestamps_in_qlog_event(
                            qlog_event, timestamps_by_stream_id)
            return timestamps_by_stream_id

        def get_qlog_stream_data_from_quicgo(ndqlog_data):
            timestamps_by_stream_id = defaultdict(list)
            for line in ndqlog_data.strip().split('\n'):
                qlog_event = json.loads(line)
                timestamps_by_stream_id = get_timestamps_in_qlog_event(
                    qlog_event, timestamps_by_stream_id)
            return timestamps_by_stream_id

        def get_timestamps_in_qlog_event(qlog_event, timestamps_by_stream_id):
            if "data" in qlog_event and 'frames' in qlog_event['data']:
                for frame in qlog_event['data']['frames']:
                    if 'fin' in frame and frame['fin'] == True:
                        stream_id = frame['stream_id']
                        timestamp = qlog_event['time']
                        timestamps_by_stream_id[stream_id].append(timestamp)
            return timestamps_by_stream_id

        def populate_qlog_data(timestamps_by_stream_id, min_rtt_values, smoothed_rtt_values, test_case):
            # bandwidth = test_case.rate * 1024 * 1024 / 8
            streams = test_case.streams
            for stream_id, timestamps in timestamps_by_stream_id.items():
                stream = Stream(stream_id)
                streams.add_stream(stream)
                request_time = float(timestamps[0])/1000
                response_time = float(timestamps[1])/1000
                connection_time = float(timestamps[1]-timestamps[0])/1000
                # link_utilization = float(connection_time / bandwidth)
                stream.update_request_time(request_time)
                stream.update_response_time(response_time)
                stream.update_connection_time(connection_time)
                # stream.update_link_utilization(link_utilization)
            if test_case:
                data = {
                    'quic_min_rtt': min_rtt_values,
                    'quic_smoothed_rtt': smoothed_rtt_values,
                }
                test_case.store_test_results_for(data)

        def get_dataframe_index_of_qlog_file(qlog_file):
            test_case = test.test_cases_decompressed.map_qlog_file_to_test_case_by_dcid(
                qlog_file)
            return test_case

        def collect_min_and_smoothed_rtt_data(qlog_event, min_rtt_values, smoothed_rtt_values):
            min_rtt = float(qlog_event["data"]["min_rtt"]/1000)
            min_rtt = round(min_rtt, 3)
            min_rtt_values.append(min_rtt)
            smoothed_rtt = float(qlog_event["data"]["smoothed_rtt"]/1000)
            smoothed_rtt = round(smoothed_rtt, 3)
            smoothed_rtt_values.append(smoothed_rtt)
            return min_rtt_values, smoothed_rtt_values

        def get_rtt_values_from_json_format_qlog(qlog_data):
            min_rtt_values = []
            smoothed_rtt_values = []
            if isinstance(qlog_data, dict) and 'traces' in qlog_data:
                for packet in qlog_data['traces']:
                    for qlog_event in packet.get('events', []):
                        if "min_rtt" in qlog_event["data"]:
                            min_rtt_values, smoothed_rtt_values = collect_min_and_smoothed_rtt_data(
                                qlog_event, min_rtt_values, smoothed_rtt_values)
            return min_rtt_values, smoothed_rtt_values

        def get_rtt_values_from_ndjson_format_qlog(ndqlog_data):
            min_rtt_values = []
            smoothed_rtt_values = []
            for line in ndqlog_data.strip().split('\n'):
                qlog_event = json.loads(line)
                if "data" in qlog_event:
                    if "min_rtt" in qlog_event["data"]:
                        min_rtt_values, smoothed_rtt_values = collect_min_and_smoothed_rtt_data(
                            qlog_event, min_rtt_values, smoothed_rtt_values)
            return min_rtt_values, smoothed_rtt_values

        for qlog_file in qlog_files:
            with open(qlog_file, 'r') as file:
                try:
                    file_content = file.read()
                    test_case = get_dataframe_index_of_qlog_file(qlog_file)
                    qlog_data = json.loads(file_content)
                    min_rtt_values, smoothed_rtt_values = get_rtt_values_from_json_format_qlog(
                        qlog_data)
                    timestamps_by_stream_id = get_qlog_stream_data_from_aioquic(
                        qlog_data)
                except json.JSONDecodeError:
                    ndqlog_data = file_content
                    min_rtt_values, smoothed_rtt_values = get_rtt_values_from_ndjson_format_qlog(
                        ndqlog_data)
                    timestamps_by_stream_id = get_qlog_stream_data_from_quicgo(
                        ndqlog_data)
                finally:
                    populate_qlog_data(
                        timestamps_by_stream_id, min_rtt_values, smoothed_rtt_values, test_case)

    update_program_progress_bar('Get Test Results')

    get_pcap_data()
    get_qlog_data()
