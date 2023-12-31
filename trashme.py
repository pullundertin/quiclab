import pandas as pd
import os
import json
import pyshark
from modules.commands import run_command
from modules.prerequisites import read_configuration
from modules.progress_bar import update_program_progress_bar
from modules.classes import Stream, Streams


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
    
def get_streams(pcap):
    # streams = test_case.streams
    stream_ids = []
    
    for packet in pcap:
        if 'http2' in packet and hasattr(packet.http2, 'headers.method'):
            stream_id = packet.http2.streamid
            
        elif 'http3' in packet and hasattr(packet.http3, 'frame_type'):
            ip_src = packet.ip.src_host
            if ip_src == '172.1.0.101' and hasattr(packet.quic, 'stream_stream_id'):
                stream_ids.append(int(packet.quic.stream_stream_id))

    my_list = [num for num in range(max(stream_ids)+4) if num % 4 == 0]
    print(my_list)
            # if packet.http3.frame_type == '1':
            #     # print(dir(packet.quic))
            #     print((packet.frame_info))
                # print((packet.http3.pretty_print()))
                # print((packet.quic.stream_stream_id))
            # stream_id = packet.http3.streamid
            # print(stream_id)
            # new_stream = Stream(stream_id)
            # streams.add_stream(new_stream)


pcap = capture_packets('shared/pcap/Case_4_Iteration_2_client_1.pcap')
get_streams(pcap)


