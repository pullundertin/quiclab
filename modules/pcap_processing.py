import os
import logging
import json
import statistics
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
            command = f"tshark -o tls.keylog_file:{KEYS_PATH} -r {pcap_file} -T json > {json_output}"
            run_command(command)


def read_json_files(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def get_tcp_handshake_time():
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('client_1.pcap.json'):
            json_file = os.path.join(PCAP_PATH, filename)

            json_data = read_json_files(json_file)
            for packet in json_data:
                if 'tls' in packet["_source"]["layers"] and 'tls.record' in packet["_source"]["layers"]["tls"] and 'tls.handshake' in packet["_source"]["layers"]["tls"]["tls.record"]:
                    tls_handshake = packet["_source"]["layers"]["tls"]["tls.record"]["tls.handshake"]
                    ip_source = packet["_source"]["layers"]["ip"]["ip.src"]
                    if 'tls.handshake.type' in tls_handshake:
                        handshake_type = tls_handshake['tls.handshake.type']
                        time = float(packet["_source"]["layers"]
                                     ["frame"]["frame.time_relative"])
                        if handshake_type == '20' and ip_source == "172.3.0.5":
                            tcp_handshake_durations.append(time)
    return tcp_handshake_durations


def get_tcp_connection_time():
    tcp_connection_durations = []

    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('client_1.pcap.json'):
            json_file = os.path.join(PCAP_PATH, filename)

            json_data = read_json_files(json_file)
            fin_ack_seq = None

            # Find the server's FIN packet
            for packet in json_data:
                if 'tcp' in packet.get('_source', {}).get('layers', {}):
                    ip = packet["_source"]["layers"]["ip"]
                    tcp = packet["_source"]["layers"]["tcp"]
                    tcp_flags = tcp["tcp.flags_tree"]

                    if ip["ip.src"] == "172.3.0.5" and tcp_flags.get("tcp.flags.fin") == "1":
                        fin_ack_seq = tcp["tcp.ack_raw"]
                        break

            # Find the client's packet with the matching sequence number
            if fin_ack_seq:
                for packet in json_data:
                    if 'ip' in packet["_source"]["layers"]:
                        ip = packet["_source"]["layers"]["ip"]
                        tcp = packet["_source"]["layers"]["tcp"]

                        if ip["ip.src"] == "172.1.0.101" and tcp.get("tcp.seq_raw") == fin_ack_seq:
                            tcp_connection_duration = float(
                                packet["_source"]["layers"]["frame"]["frame.time_relative"])
                            tcp_connection_durations.append(
                                tcp_connection_duration)
                            break

    return tcp_connection_durations


def get_quic_connection_time():
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('client_1.pcap.json'):
            json_file = os.path.join(PCAP_PATH, filename)

            json_data = read_json_files(json_file)
            quic_connection_duration = None
            for packet in json_data:
                if 'quic' in packet.get('_source', {}).get('layers', {}):
                    frame_type = packet["_source"]["layers"]["quic"]["quic.frame"]["quic.frame_type"]
                    time = float(packet["_source"]["layers"]
                                 ["frame"]["frame.time_relative"])
                    if frame_type == '29':
                        quic_connection_duration = time
                if quic_connection_duration:
                    quic_connection_durations.append(quic_connection_duration)
    return quic_connection_durations


def get_quic_handshake_time():
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('client_1.pcap.json'):
            json_file = os.path.join(PCAP_PATH, filename)

            json_data = read_json_files(json_file)
            for packet in json_data:
                if 'quic' in packet["_source"]["layers"]:
                    quic_frame = packet["_source"]["layers"]["quic"].get(
                        "quic.frame", {})
                    tls_handshake = quic_frame.get(
                        "tls", {}).get("tls.handshake", {})
                    if 'tls.handshake.type' in tls_handshake:
                        handshake_type = tls_handshake['tls.handshake.type']
                        time = float(packet["_source"]["layers"]
                                     ["frame"]["frame.time_relative"])
                        if handshake_type == '20':
                            quic_handshake_durations.append(time)
    return quic_handshake_durations


def get_tcp_rtt_statistics():
    rtt_values = []
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('client_1.pcap.json'):
            json_file = os.path.join(PCAP_PATH, filename)
            json_data = read_json_files(json_file)
            # Extract non-empty tcp.analysis.ack_rtt values for packets with IP '172.3.0.5'
            rtt_values.extend([
                float(packet["_source"]["layers"]["tcp"]
                      ["tcp.analysis"]["tcp.analysis.ack_rtt"])
                for packet in json_data
                if "tcp" in packet["_source"]["layers"]
                and "ip" in packet["_source"]["layers"]
                and packet["_source"]["layers"]["ip"]["ip.src"] == "172.3.0.5"
                and "tcp.analysis" in packet["_source"]["layers"]["tcp"]
                and "tcp.analysis.ack_rtt" in packet["_source"]["layers"]["tcp"]["tcp.analysis"]
            ])
    return rtt_values


def get_quic_rtt_statistics():
    min_rtt_values = []
    smoothed_rtt_values = []
    for filename in os.listdir(QLOG_PATH):
        if filename.endswith('.qlog'):
            json_file = os.path.join(QLOG_PATH, filename)
            json_data = read_json_files(json_file)
            for packet in json_data["traces"]:
                for event in packet["events"]:
                    if 'min_rtt' in event["data"]:
                        min_rtt_values.append(event["data"]["min_rtt"]/1000)
                        smoothed_rtt_values.append(
                            event["data"]["smoothed_rtt"]/1000)
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
    for i in tcp_handshake_durations:
        print('hs', i)
    for i in tcp_connection_durations:
        print('conn', i)
    for i in quic_handshake_durations:
        print(i)
    for i in quic_connection_durations:
        print(i)
