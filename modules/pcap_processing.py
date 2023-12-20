import pandas as pd
import os
import logging
import json
from modules.commands import run_command
from modules.prerequisites import read_configuration
from modules.tests import get_test_configuration_of_json_file



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
    tcp_handshake_duration = None

    json_objects = read_json_objects_from_file(json_file)
    for packet in json_objects:
        if check_if_packet_contains_protocol(packet, 'tcp'):
            results = search_key_value(
                json_objects, 'tls_tls_handshake_type', '20')
            if results:
                frame_time_relative = float(
                    results[0]['layers']['frame']['frame_frame_time_relative'])
                tcp_handshake_duration = (frame_time_relative)
                break

    return tcp_handshake_duration


def get_tcp_connection_time(json_file):
    tcp_connection_duration = None
    fin_ack_seq = None

    packets = read_json_objects_from_file(json_file)
    for packet in packets:
        if check_if_packet_contains_protocol(packet, 'tcp'):
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
            tcp_connection_duration = (time_relative)
            break

    return tcp_connection_duration


def get_quic_connection_time(json_file):
    quic_connection_duration = None

    json_objects = read_json_objects_from_file(json_file)
    for packet in json_objects:
        if check_if_packet_contains_protocol(packet, 'quic'):
            quic_connection_start = float(
                packet['layers']['frame']['frame_frame_time_relative'])
            break
    for packet in json_objects:
        if check_if_packet_contains_protocol(packet, 'quic'):
            quic_data = packet.get('layers', {}).get('quic', {})
            if quic_data and 'quic_quic_frame_type' in quic_data:
                frame_type = quic_data['quic_quic_frame_type']
                frame_time_relative = float(
                    packet['layers']['frame']['frame_frame_time_relative'])
                if frame_type == '29':
                    quic_connection_end = (frame_time_relative)
                    quic_connection_duration = quic_connection_end - quic_connection_start

    return quic_connection_duration


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
    quic_handshake_duration = None
    quic_handshake_start = None
    quic_handshake_end = None
    json_objects = read_json_objects_from_file(json_file)
    for packet in json_objects:
        if check_if_packet_contains_protocol(packet, 'quic'):
            quic_handshake_start = float(
                packet['layers']['frame']['frame_frame_time_relative'])
            break
    for packet in json_objects:
        if check_if_packet_contains_protocol(packet, 'quic'):
            results = search_key_value(
                json_objects, 'tls_tls_handshake_type', '20')

            if results:
                quic_handshake_end = float(
                    results[0]['layers']['frame']['frame_frame_time_relative'])
                quic_handshake_duration = quic_handshake_end - quic_handshake_start
                break

    return quic_handshake_duration


def get_tcp_rtt_statistics(json_file):
    rtt_values = []

    json_objects = read_json_objects_from_file(json_file)
    for packet in json_objects:
        if check_if_packet_contains_protocol(packet, 'tcp'):
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
    quic_implementation = None
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
                quic_implementation = 'quicgo'
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
    return quic_implementation, min_rtt_values, smoothed_rtt_values


def add_configuration_parameters(json_file):

    data = {}
    config = get_test_configuration_of_json_file(json_file)
    for column in config:
        data[column] = config[column]

    return data


def get_quic_dcid(json_file):
    quic_dcid = None
    quic_dcid_ascii = None
    packets = read_json_objects_from_file(json_file)
    for packet in packets:
        if check_if_packet_contains_protocol(packet, 'quic') and 'quic_quic_dcid' in packet['layers']['quic']:
            quic_dcid_string = packet['layers']['quic']['quic_quic_dcid']
            quic_dcid_ascii = quic_dcid_string.replace(":", "")
            quic_dcid = bytes(quic_dcid_ascii, 'utf-8').hex()
            break
    return quic_dcid, quic_dcid_ascii


def get_statistics():
    def get_pcap_statistics():
        files = traverse_pcap_directory()
        statistics_data = []
        for json_file in files:
            data = add_configuration_parameters(json_file)
            data['tcp_rtt'] = get_tcp_rtt_statistics(json_file)
            data['tcp_hs'] = get_tcp_handshake_time(json_file)
            data['tcp_conn'] = get_tcp_connection_time(json_file)
            data['quic_hs'] = get_quic_handshake_time(json_file)
            data['quic_conn'] = get_quic_connection_time(json_file)
            data['dcid'], data['dcid_hex'] = get_quic_dcid(json_file)
            data['quic_min_rtt'] = None
            data['quic_smoothed_rtt'] = None

            statistics_data.append(data)

        # Creating DataFrame directly from statistics_data
        return pd.DataFrame(statistics_data)

    def get_qlog_statistics(statistics_df):

        files = traverse_qlog_directory()
        min_rtt_values = []
        smoothed_rtt_values = []

        def get_dataframe_index_of_qlog_file(qlog_file):
            for index, row in statistics_df.iterrows():
                if row['dcid'] != None and (row['dcid'] in qlog_file or row['dcid_hex'] in qlog_file):
                    return index

        for qlog_file in files:
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

            index = get_dataframe_index_of_qlog_file(qlog_file)
            statistics_df.at[index, 'quic_min_rtt'] = min_rtt_values
            statistics_df.at[index, 'quic_smoothed_rtt'] = smoothed_rtt_values
        return statistics_df

    def get_medians(df):
        group_columns = ['mode', 'size', 'delay', 'delay_deviation', 'loss',
                         'rate', 'firewall', 'window_scaling', 'rmin', 'rmax', 'rdef', 'migration', 'generic_heatmap']
        # Group by group_columns and calculate median across multiple columns
        median_values = df.groupby(group_columns).agg({
            'quic_hs': 'median',
            'tcp_hs': 'median',
            'quic_conn': 'median',
            'tcp_conn': 'median'
        }).reset_index()
        return median_values

    statistics_df = get_pcap_statistics()
    statistics_df = get_qlog_statistics(statistics_df)
    median_df = pd.DataFrame()
    median_df = get_medians(statistics_df)
    return statistics_df, median_df
