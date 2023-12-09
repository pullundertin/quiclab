import os
import logging
import json
from modules.commands import run_command

PCAP_PATH = "./shared/pcap/"
tcp_connection_durations = []
tcp_handshake_durations = []


def convert_pcap_to_json():
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('.pcap'):
            pcap_file = os.path.join(PCAP_PATH, filename)
            json_output = f'{pcap_file}.json'
            # logging.info(f"writing {json_output}")
            command = f"tshark -r {pcap_file} -T json > {json_output}"
            run_command(command)


def read_json_files(file_path):
    # Open the JSON file in read mode
    with open(file_path, 'r') as file:
        # Load the JSON data into a Python dictionary
        return json.load(file)


def get_tcp_handshake_time():
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('.json'):
            json_file = os.path.join(PCAP_PATH, filename)

            json_data = read_json_files(json_file)
            # Initialize variables to store relevant data
            syn_ack_packet = None
            tcp_handshake_duration = None

            # Loop through each packet in the JSON data
            for packet in json_data:
                tcp_flags = packet["_source"]["layers"]["tcp"]["tcp.flags_tree"]

                # Check if the packet has both SYN and ACK flags set
                if tcp_flags.get("tcp.flags.syn") == "1" and tcp_flags.get("tcp.flags.ack") == "1":
                    syn_ack_packet = packet
                    break  # Exit the loop after finding the SYN+ACK packet

            # If a SYN+ACK packet is found, search for the corresponding packet with matching sequence and acknowledgment numbers
            if syn_ack_packet:
                syn_ack_seq_ack = syn_ack_packet["_source"]["layers"]["tcp"]["tcp.ack_raw"]
                for packet in json_data:
                    seq_ack = packet["_source"]["layers"]["tcp"]["tcp.seq_raw"]

                    # Check if the sequence and acknowledgment numbers match
                    if seq_ack == syn_ack_seq_ack:
                        tcp_handshake_duration = float(
                            packet["_source"]["layers"]["frame"]["frame.time_relative"])
                        break  # Exit the loop after finding the matching packet

            # Print the frame.time_relative of the matching packet (if found)
            if tcp_handshake_duration:
                tcp_handshake_durations.append(tcp_handshake_duration)

    return tcp_handshake_durations


def get_tcp_connection_time():
    for filename in os.listdir(PCAP_PATH):
        if filename.endswith('.json'):
            json_file = os.path.join(PCAP_PATH, filename)

            json_data = read_json_files(json_file)
            # Initialize variables to store relevant data
            fin_packet = None
            tcp_connection_duration = None

            # Loop through each packet in the JSON data to find the server's FIN packet
            for packet in json_data:
                ip = packet["_source"]["layers"]["ip"]
                tcp = packet["_source"]["layers"]["tcp"]
                tcp_flags = tcp["tcp.flags_tree"]

                # Check for a packet sent by the server with IP 172.3.0.5 with FIN flag set
                if ip["ip.src"] == "172.3.0.5" and tcp_flags.get("tcp.flags.fin") == "1":
                    fin_packet = packet
                    fin_ack_seq = tcp["tcp.ack_raw"]
                    break  # Exit loop after finding the server's FIN packet

            # If the server's FIN packet is found, search for the client's packet with matching sequence number
            if fin_packet:
                for packet in json_data:
                    ip = packet["_source"]["layers"]["ip"]
                    tcp = packet["_source"]["layers"]["tcp"]
                    tcp_flags = tcp["tcp.flags_tree"]

                    # Check for a packet sent by the client with IP 172.1.0.101 with matching sequence number
                    if ip["ip.src"] == "172.1.0.101" and tcp.get("tcp.seq_raw") == fin_ack_seq:
                        tcp_connection_duration = float(
                            packet["_source"]["layers"]["frame"]["frame.time_relative"])
                        break  # Exit loop after finding the matching ACK packet

            # Print the frame.time_relative of the matching packet (if found)
            if tcp_connection_duration:
                tcp_connection_durations.append(tcp_connection_duration)

    return tcp_connection_durations


# def get_tcp_rtt_statistics():
#     json_data = read_json_files()
#     # List to store non-empty tcp.analysis.ack_rtt values
#     # Extract non-empty tcp.analysis.ack_rtt values
#     non_empty_ack_rtt_values = [
#         float(packet["_source"]["layers"]["tcp"]
#               ["tcp.analysis"]["tcp.analysis.ack_rtt"])
#         for packet in json_data
#         if "tcp" in packet["_source"]["layers"] and "tcp.analysis" in packet["_source"]["layers"]["tcp"]
#         and "tcp.analysis.ack_rtt" in packet["_source"]["layers"]["tcp"]["tcp.analysis"]
#     ]

#     print('RTT Median', statistics.median(non_empty_ack_rtt_values))
#     print('RTT Min', min(non_empty_ack_rtt_values))
#     print('RTT Max', max(non_empty_ack_rtt_values))
