import pandas as pd
import os
import pyshark
from modules.prerequisites import read_configuration
from modules.progress_bar import update_program_progress_bar
from modules.classes import Stream
import logging


def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AttributeError as e:
            logging.error(
                f"An error occurred in {func.__name__} with arguments {str(args)} and keyword arguments {kwargs}: {e}")
        except TypeError as e:
            logging.error(f"An error occurred: {e}")
    return wrapper


PCAP_PATH = read_configuration().get("PCAP_PATH")
KEYS_PATH = read_configuration().get("KEYS_PATH")
SERVER_IP = read_configuration().get("SERVER_IP")
CLIENT_1_IP = read_configuration().get("CLIENT_1_IP")

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)


def traverse_pcap_directory():
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('client_1.pcap'):
            yield os.path.join(PCAP_PATH, filename)


def capture_packets(pcap_file):
    with pyshark.FileCapture(pcap_file, display_filter="tcp.flags.fin == 1 || tls.handshake.type == 20 || http2.headers.method == GET || http2.flags.end_stream == 1 || tls.handshake.type == 1 || tls.handshake.type == 20 || quic.frame_type == 29", override_prefs={'tcp.analyze_sequence_numbers': 'TRUE', 'transum.reassembly': 'TRUE', 'tls.keylog_file': 'shared/keys/client.key', 'tcp.reassemble_out_of_order': 'TRUE', 'tcp.desegment_tcp_streams': 'TRUE',  'tls.desegment_ssl_application_data': 'TRUE', 'tls.desegment_ssl_records': 'TRUE'}) as pcap:
        for packet in pcap:
            yield packet


def get_tcp_handshake_time(packet, test_case):
    if hasattr(packet, 'tls') and hasattr(packet.tls, 'handshake_type'):
        if packet.tls.handshake_type == '20':
            tcp_handshake_time = float(packet.frame_info.time_relative)
            tcp_handshake_time = round(tcp_handshake_time, 4)
            test_case.update_property('tcp_hs', tcp_handshake_time)


def get_tcp_connection_time(packet, test_case):
    if packet.tcp.flags_fin in ['1', 'True']:
        time_relative = float(packet.frame_info.time_relative)
        time_relative = round(time_relative, 4)
        if time_relative > 0:
            test_case.update_property('tcp_conn', time_relative)


def get_tcp_rtt_data(packet, test_case):
    if hasattr(packet.tcp, 'analysis_ack_rtt'):
        ack_rtt = float(packet.tcp.analysis_ack_rtt)
        ack_rtt = round(ack_rtt, 4)
        ip_src = packet.ip.src
        if (ip_src == SERVER_IP):
            rtt_values = test_case.tcp_rtt
            rtt_values.append(ack_rtt)
            test_case.update_property('tcp_rtt', rtt_values)


def check_all_fields(packet, layer):
    if packet.__contains__(layer):
        fields = packet.get_multiple_layers(layer)
        return fields


def get_http2_streams(packet, test_case):
    streams = test_case.streams
    fields = check_all_fields(packet, 'http2')
    if fields:
        for field in fields:
            if hasattr(field, 'headers.method'):
                stream_id = field.streamid
                new_stream = Stream(stream_id)
                streams.add_stream(new_stream)


def get_tcp_single_stream_connection_time(packet, test_case):
    streams = test_case.streams
    fields = check_all_fields(packet, 'http2')
    if fields:
        for field in fields:
            if hasattr(field, 'headers.method'):
                stream_id = field.streamid
                stream = streams.find_stream_by_id(stream_id)
                request_time = float(packet.frame_info.time_relative)
                request_time = round(request_time, 4)
                stream.update_request_time(request_time)

            elif hasattr(field, 'flags_end_stream') and field.flags_end_stream in ['1', 'True']:
                stream_id = field.streamid
                stream = streams.find_stream_by_id(stream_id)
                response_time = float(packet.frame_info.time_relative)
                response_time = round(response_time, 4)
                stream.update_response_time(response_time)
                connection_time = round(response_time - stream.request_time, 4)
                stream.update_connection_time(connection_time)


def get_quic_handshake_time(packet, test_case):
    if hasattr(packet, 'quic') and hasattr(packet.quic, 'tls_handshake_type'):
        if packet.quic.tls_handshake_type == '20':
            quic_handshake_duration = float(packet.frame_info.time_relative)
            quic_handshake_duration = round(quic_handshake_duration, 4)
            test_case.update_property('quic_hs', quic_handshake_duration)
            if test_case.mode == 'aioquic':
                test_case.update_property(
                    'aioquic_hs', quic_handshake_duration)
            elif test_case.mode == 'quicgo':
                test_case.update_property('quicgo_hs', quic_handshake_duration)


def get_quic_connection_time(packet, test_case):
    if hasattr(packet.quic, 'frame_type') and packet.quic.frame_type == '29':
        quic_connection_duration = float(packet.frame_info.time_relative)
        quic_connection_duration = round(quic_connection_duration, 4)
        test_case.update_property('quic_conn', quic_connection_duration)
        if test_case.mode == 'aioquic':
            test_case.update_property('aioquic_conn', quic_connection_duration)
        elif test_case.mode == 'quicgo':
            test_case.update_property('quicgo_conn', quic_connection_duration)


@handle_exceptions
def get_quic_dcid(packet, test_case):
    if packet.ip.src == CLIENT_1_IP and packet.quic.packet_number == '0':
        quic_dcid_string = packet.quic.dcid
        quic_dcid_ascii = quic_dcid_string.replace(":", "")
        quic_dcid = bytes(quic_dcid_ascii, 'utf-8').hex()
        if test_case.dcid is None:
            test_case.update_property('dcid', quic_dcid_ascii)
            test_case.update_property('dcid_hex', quic_dcid)


def extract_data_from_pcap(packet_generator, test_case):
    for packet in packet_generator:
        if 'TCP' in packet and 'IP' in packet:
            get_tcp_rtt_data(packet, test_case)
            get_tcp_handshake_time(packet, test_case)
            get_tcp_connection_time(packet, test_case)
        if 'HTTP2' in packet:
            get_http2_streams(packet, test_case)
            get_tcp_single_stream_connection_time(packet, test_case)
        if 'QUIC' in packet:
            get_quic_dcid(packet, test_case)
            get_quic_handshake_time(packet, test_case)
            get_quic_connection_time(packet, test_case)


def get_pcap_data(test):
    update_program_progress_bar('Get Pcap Data')
    pcap_files = traverse_pcap_directory()

    for pcap_file in pcap_files:
        packet_generator = capture_packets(pcap_file)
        test_case = test.test_cases_decompressed.map_file_to_test_case(
            pcap_file)
        extract_data_from_pcap(
            packet_generator, test_case)
