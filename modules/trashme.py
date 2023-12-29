import pyshark


class Streams:
    def __init__(self):
        self.streams = []

    def add_stream(self, stream):
        self.streams.append(stream)

    def find_stream_by_id(self, stream_id):
        for stream in self.streams:
            if stream.stream_id == stream_id:
                return stream
        return None


    def __str__(self):
        streams = "\n".join(str(stream) for stream in self.streams)
        return f"\n{streams}"

class Stream:
    def __init__(self, stream_id, request_time):
        self.stream_id = stream_id
        self.request_time = request_time
        self.response_time = None
        self.connection_time = None

    def update_response_time(self, response_time):
        setattr(self, 'response_time', response_time)
        setattr(self, 'connection_time', self.response_time - self.request_time)

    def __str__(self):
        return f"Stream ID: {self.stream_id}, Request Time: {self.request_time}, Response Time: {self.response_time}, Connection Time: {self.connection_time}"

def get_request_time_for_each_stream(packet, streams):
    if 'http2' in packet and hasattr(packet.http2, 'headers.method'):
        stream_id = packet.http2.streamid
        request_time = float(packet.frame_info.time_relative)
        new_stream = Stream(stream_id, request_time)
        streams.add_stream(new_stream)
    
def get_response_time_for_each_stream(packet, streams):
     if 'http2' in packet and hasattr(packet.http2, 'body_reassembled_data'):
        stream_id = packet.http2.streamid
        stream = streams.find_stream_by_id(stream_id)
        response_time = float(packet.frame_info.time_relative) 
        stream.update_response_time(response_time)
          

def analyze_pcap(pcap_file):
    capture = pyshark.FileCapture(pcap_file, override_prefs={'tls.keylog_file': 'shared/keys/client.key'})

    streams = Streams()
    for packet in capture:
        get_request_time_for_each_stream(packet, streams)
        get_response_time_for_each_stream(packet, streams)
    print(streams)

if __name__ == "__main__":
    pcap_file_path = "shared/pcap/Case_1_Iteration_2_client_1.pcap"
    analyze_pcap(pcap_file_path)
