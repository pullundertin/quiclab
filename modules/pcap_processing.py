import pandas as pd
import os
import logging
import json
from modules.commands import run_command
from modules.prerequisites import read_configuration
from modules.mapping import get_mode_of_file
import numpy as np


PCAP_PATH = read_configuration().get("PCAP_PATH")
KEYS_PATH = read_configuration().get("KEYS_PATH")
QLOG_PATH_CLIENT = read_configuration().get("QLOG_PATH_CLIENT")
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)


def convert_pcap_to_json():
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('.pcap'):
            pcap_file = os.path.join(PCAP_PATH, filename)
            json_output = f'{pcap_file}.json'
            logging.info(f"writing {json_output}")
            command = f"tshark -o tls.keylog_file:{KEYS_PATH} -r {pcap_file} -T ek > {json_output}"
            run_command(command)


def read_json_objects_from_file(file_path):
    with open(file_path) as file:
        lines = file.readlines()

    json_objects = []
    for line in lines:
        json_objects.append(json.loads(line))

    return json_objects


def traverse_pcap_directory():
    return [os.path.join(PCAP_PATH, filename) for filename in os.listdir(PCAP_PATH) if filename.endswith('client_1.pcap.json')]


def traverse_qlog_directory():
    return [os.path.join(QLOG_PATH_CLIENT, filename) for filename in os.listdir(QLOG_PATH_CLIENT) if filename.endswith('.qlog')]


def check_if_packet_contains_protocol(packet, key):
    return 'layers' in packet and key in packet['layers']


def get_tcp_handshake_time(json_file):
    tcp_handshake_durations = []

    json_objects = read_json_objects_from_file(json_file)
    for packet in json_objects:
        if check_if_packet_contains_protocol(packet, 'tcp'):
            results = search_key_value(
                json_objects, 'tls_tls_handshake_type', '20')
            if results:
                frame_time_relative = float(
                    results[0]['layers']['frame']['frame_frame_time_relative'])
                tcp_handshake_durations.append(frame_time_relative)
                break

    return tcp_handshake_durations


def get_tcp_connection_time(json_file):
    tcp_connection_durations = []
    fin_ack_seq = None

    packets = read_json_objects_from_file(json_file)
    for packet in packets:
        layers = packet.get('layers', {})
        ip_layer = layers.get('ip', {})
        tcp_layer = layers.get('tcp', {})

        src_ip = ip_layer.get('ip_ip_src')
        flags_fin = tcp_layer.get('tcp_tcp_flags_fin')
        seq_raw = tcp_layer.get('tcp_tcp_seq_raw')
        ack_raw = tcp_layer.get('tcp_tcp_ack_raw')

        if src_ip == '172.3.0.5' and flags_fin:
            fin_ack_seq = ack_raw
            break
        else:
            continue  # No FIN packet found

    for packet in packets:
        layers = packet.get('layers', {})
        ip_layer = layers.get('ip', {})
        tcp_layer = layers.get('tcp', {})

        src_ip = ip_layer.get('ip_ip_src')
        seq_raw_packet = tcp_layer.get('tcp_tcp_seq_raw')

        if src_ip == '172.1.0.101' and seq_raw_packet == fin_ack_seq:
            time_relative = float(
                packet['layers']['frame']['frame_frame_time_relative'])
            tcp_connection_durations.append(time_relative)
            break

    return tcp_connection_durations


def get_quic_connection_time(json_file):
    quic_connection_durations = []

    json_objects = read_json_objects_from_file(json_file)
    for packet in json_objects:
        if check_if_packet_contains_protocol(packet, 'quic'):
            quic_data = packet.get('layers', {}).get('quic', {})
            if quic_data and 'quic_quic_frame_type' in quic_data:
                frame_type = quic_data['quic_quic_frame_type']
                frame_time_relative = float(
                    packet['layers']['frame']['frame_frame_time_relative'])
                if frame_type == '29':
                    quic_connection_durations.append(frame_time_relative)

    return quic_connection_durations


def search_key_value(json_objects, search_key, search_value):
    results = []

    for obj in json_objects:
        result, root = search_key_value_recursive(
            obj, search_key, search_value, obj)
        if result is not None:
            results.append(root)

    return results


def search_key_value_recursive(obj, search_key, search_value, root):
    if isinstance(obj, dict):
        if search_key in obj and obj[search_key] == search_value:
            return obj, root
        else:
            for value in obj.values():
                result, root_element = search_key_value_recursive(
                    value, search_key, search_value, root)
                if result is not None:
                    return result, root_element
    elif isinstance(obj, list):
        for item in obj:
            result, root_element = search_key_value_recursive(
                item, search_key, search_value, root)
            if result is not None:
                return result, root_element
    return None, None


def get_quic_handshake_time(json_file):
    quic_handshake_durations = []

    json_objects = read_json_objects_from_file(json_file)
    for packet in json_objects:
        if check_if_packet_contains_protocol(packet, 'quic'):
            results = search_key_value(
                json_objects, 'tls_tls_handshake_type', '20')

            if results:
                frame_time_relative = float(
                    results[0]['layers']['frame']['frame_frame_time_relative'])
                quic_handshake_durations.append(frame_time_relative)
                break

    return quic_handshake_durations


def get_tcp_rtt_statistics(json_file):
    rtt_values = []

    
    json_objects = read_json_objects_from_file(json_file)
    for packet in json_objects:
        layers = packet.get('layers', {})
        ip_layer = layers.get('ip', {})
        tcp_layer = layers.get('tcp', {})

        if (
            'ip' in layers and
            ip_layer.get('ip_ip_src') == '172.3.0.5' and
            'tcp' in layers and
            'tcp_tcp_analysis_ack_rtt' in tcp_layer
        ):
            rtt_values.append(float(tcp_layer['tcp_tcp_analysis_ack_rtt']))

    return rtt_values


def get_quic_rtt_statistics():
    min_rtt_values = []
    smoothed_rtt_values = []
    for qlog_file in traverse_qlog_directory():
        try:
            with open(qlog_file, 'r') as f:
                data = f.read()
                qlog_data = json.loads(data)

            if isinstance(qlog_data, dict) and 'traces' in qlog_data:
                for packet in qlog_data['traces']:
                    for event in packet.get('events', []):
                        data = event.get('data', {})
                        min_rtt = data.get('min_rtt')
                        smoothed_rtt = data.get('smoothed_rtt')

                        if min_rtt is not None:
                            min_rtt_values.append(min_rtt / 1000)
                        if smoothed_rtt is not None:
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
    return min_rtt_values, smoothed_rtt_values


def get_statistics():
    files = traverse_pcap_directory()
    statistics_data = []

    for json_file in files:
        data = {}
        data['mode'] = get_mode_of_file(json_file)

        data['tcp_rtt'] = get_tcp_rtt_statistics(json_file)
        data['tcp_hs'] = get_tcp_handshake_time(json_file)
        data['tcp_conn'] = get_tcp_connection_time(json_file)
        data['quic_min_rtt'], data['quic_smoothed_rtt'] = get_quic_rtt_statistics()
        data['quic_hs'] = get_quic_handshake_time(json_file)
        data['quic_conn'] = get_quic_connection_time(json_file)

        statistics_data.append(data)

    statistics_df = pd.DataFrame(statistics_data)

    # Convert lists with multiple values to NaN for numeric calculations
    df = statistics_df.applymap(lambda x: np.nan if isinstance(x, list) and len(x) > 1 else x)

    # Group by 'mode' column and calculate median for specified columns
    median_values = df.groupby('mode').agg(lambda x: np.nanmedian([v for v in x if not np.isnan(v)])).reset_index()

    
    return statistics_df, median_values

