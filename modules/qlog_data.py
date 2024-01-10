import os
import json
from modules.prerequisites import read_configuration
from modules.progress_bar import update_program_progress_bar
from modules.classes import Stream
from collections import defaultdict

QLOG_PATH_CLIENT = read_configuration().get("QLOG_PATH_CLIENT")

def traverse_qlog_directory():
    return [os.path.join(QLOG_PATH_CLIENT, filename) for filename in os.listdir(QLOG_PATH_CLIENT) if filename.endswith('.qlog')]

def get_qlog_data(test):
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
        streams = test_case.streams
        for stream_id, timestamps in timestamps_by_stream_id.items():
            stream = Stream(stream_id)
            streams.add_stream(stream)
            request_time = float(timestamps[0])/1000
            request_time = round(request_time, 4)
            response_time = float(timestamps[1])/1000
            response_time = round(response_time, 4)
            connection_time = float(timestamps[1]-timestamps[0])/1000
            connection_time = round(connection_time, 4)
            stream.update_request_time(request_time)
            stream.update_response_time(response_time)
            stream.update_connection_time(connection_time)
            test_case.update_min_rtt(min_rtt_values)
            test_case.update_smoothed_rtt(smoothed_rtt_values)


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