import os
import logging
import json
import statistics
from collections import Counter, defaultdict
from modules.commands import run_command
from modules.prerequisites import read_configuration

PCAP_PATH = read_configuration().get("PCAP_PATH")
KEYS_PATH = read_configuration().get("KEYS_PATH")
QLOG_PATH = read_configuration().get("QLOG_PATH")
tcp_connection_durations = []
tcp_handshake_durations = []
quic_connection_durations = []
quic_handshake_durations = []


def convert_pcap_to_json():
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('.pcap'):
            pcap_file = os.path.join(PCAP_PATH, filename)
            json_output = f'{pcap_file}.json'
            logging.info(f"writing {json_output}")
            command = f"tshark -o tls.keylog_file:{KEYS_PATH} -r {pcap_file} -T ek > {json_output}"
            run_command(command)


def read_json_files(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def read_json_objects_from_file(file_path):
    with open(file_path) as file:
        lines = file.readlines()

    json_objects = []
    for line in lines:
        json_objects.append(json.loads(line))

    return json_objects


def traverse_pcap_directory():
    json_files = []
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('client_1.pcap.json'):
            json_files.append(os.path.join(PCAP_PATH, filename))
    return json_files


def contains_tcp_key(packet):
    return 'layers' in packet and 'tcp' in packet['layers']


def contains_quic_key(packet):
    return 'layers' in packet and 'quic' in packet['layers']


def get_tcp_handshake_time():
    tcp_handshake_durations = []
    for json_file in traverse_pcap_directory():
        json_objects = read_json_objects_from_file(json_file)
        for packet in json_objects:
            if contains_tcp_key(packet):
                results = search_key_value(
                    json_objects, 'tls_tls_handshake_type', '20')

                frame_time_relative = float(
                    results[0]['layers']['frame']['frame_frame_time_relative'])
                tcp_handshake_durations.append(frame_time_relative)
                break

    return tcp_handshake_durations


def get_tcp_connection_time():
    tcp_connection_durations = []
    for json_file in traverse_pcap_directory():
        for packet in read_json_objects_from_file(json_file):
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

        for packet in read_json_objects_from_file(json_file):
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


def get_quic_connection_time():
    for json_file in traverse_pcap_directory():
        json_objects = read_json_objects_from_file(json_file)
        for packet in json_objects:
            if contains_quic_key(packet):
                if 'layers' in packet and 'quic' in packet['layers'] and 'quic_quic_frame_type' in packet['layers']['quic']:
                    frame_type = packet["layers"]["quic"]["quic_quic_frame_type"]
                    time = float(packet["layers"]
                                 ["frame"]["frame_frame_time_relative"])
                    if frame_type == '29':
                        quic_connection_durations.append(time)

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


def get_quic_handshake_time():
    for json_file in traverse_pcap_directory():
        json_objects = read_json_objects_from_file(json_file)
        for packet in json_objects:
            if contains_quic_key(packet):
                results = search_key_value(
                    json_objects, 'tls_tls_handshake_type', '20')

                frame_time_relative = float(
                    results[0]['layers']['frame']['frame_frame_time_relative'])
                quic_handshake_durations.append(frame_time_relative)
                break

                # if 'layers' in packet and 'quic' in packet['layers'] and 'tls' in packet["layers"]['quic'] and 'tls_tls_handshake_type' in packet['layers']['quic']['tls']:
                #     print(packet["layers"]["quic"]["tls"]
                #           ["tls_tls_handshake_type"])
                #     frame_type = packet["layers"]["quic"]["tls"]["tls_tls_handshake_type"]
                #     frame_time_relative = float(packet["layers"]
                #                                 ["frame"]["frame_frame_time_relative"])
                #     for type in frame_type:
                #         if type == '20':
                #             quic_handshake_durations.append(
                #                 frame_time_relative)

    return quic_handshake_durations


def get_tcp_rtt_statistics():
    rtt_values = []
    for json_file in traverse_pcap_directory():
        json_objects = read_json_objects_from_file(json_file)
        for packet in json_objects:
            if 'layers' in packet:
                if 'ip' in packet['layers'] and packet['layers']['ip']['ip_ip_src'] == '172.3.0.5':
                    if 'tcp' in packet['layers'] and 'tcp_tcp_analysis_ack_rtt' in packet['layers']['tcp']:
                        rtt_values.append(
                            float(packet['layers']['tcp']['tcp_tcp_analysis_ack_rtt']))
    return rtt_values


def get_quic_rtt_statistics():
    min_rtt_values = []
    smoothed_rtt_values = []
    for filename in os.listdir(QLOG_PATH):
        if filename.endswith('.qlog'):
            json_file = os.path.join(QLOG_PATH, filename)
            # json format - aioquic
            try:
                json_data = read_json_files(json_file)
                if isinstance(json_data, dict) and 'traces' in json_data:
                    for packet in json_data["traces"]:
                        for event in packet["events"]:
                            if 'min_rtt' in event["data"]:
                                min_rtt_values.append(
                                    event["data"]["min_rtt"]/1000)
                                smoothed_rtt_values.append(
                                    event["data"]["smoothed_rtt"]/1000)
            # ndjson format - quicgo
            except json.JSONDecodeError:
                with open(json_file, 'r') as f:
                    ndjson_data = f.read()
                    # Split the data into lines and parse each line as JSON
                    for line in ndjson_data.strip().split('\n'):
                        json_data = json.loads(line)
                        if "data" in json_data:
                            if "min_rtt" in json_data["data"]:
                                min_rtt_values.append(
                                    json_data["data"]["min_rtt"]/1000)
                                smoothed_rtt_values.append(
                                    json_data["data"]["smoothed_rtt"]/1000)
    return min_rtt_values, smoothed_rtt_values


def get_statistics():
    tcp_rtt = get_tcp_rtt_statistics()
    tcp_handshake_durations = get_tcp_handshake_time()
    tcp_connection_durations = get_tcp_connection_time()
    quic_min_rtt, quic_smoothed_rtt = get_quic_rtt_statistics()
    quic_handshake_durations = get_quic_handshake_time()
    quic_connection_durations = get_quic_connection_time()

    def calculate_and_log_stats(data, label):
        if not data:
            logging.info(f"No data available for {label}")
            return

        multiplied_data = [x * 1000 for x in data]
        median = round(statistics.median(multiplied_data), 2)
        minimum = round(min(multiplied_data), 2)
        maximum = round(max(multiplied_data), 2)

        logging.info(f"{label}_data: {data}")
        logging.info(f"{label}_median: {median} ms")
        logging.info(f"{label}_minimum: {minimum} ms")
        logging.info(f"{label}_maximum: {maximum} ms")

    calculate_and_log_stats(tcp_rtt, 'tcp_rtt')
    calculate_and_log_stats(tcp_handshake_durations, 'tcp_hs')
    calculate_and_log_stats(tcp_connection_durations, 'tcp_conn')
    calculate_and_log_stats(quic_min_rtt, 'quic_min_rtt')
    calculate_and_log_stats(quic_smoothed_rtt, 'quic_smoothed_rtt')
    calculate_and_log_stats(quic_handshake_durations, 'quic_hs')
    calculate_and_log_stats(quic_connection_durations, 'quic_conn')
