import pandas as pd
import re

pd.options.mode.chained_assignment = None

input_file = "/shared/tcpprobe/server.log"
output_file = "/shared/tcpprobe/results.csv"
output_directory = "/shared/tcpprobe/"
MSS = 1460

# Lists to store extracted values
time_values = []
src_values = []
dest_values = []
data_len_values = []
snd_cwnd_values = []
ssthresh_values = []
snd_wnd_values = []
snd_nxt_values = []
snd_una_values = []
srtt_values = []
rcv_wnd_values = []

# Regular expression pattern to match time value, src= and dest=
pattern = r'(\d+\.\d+): tcp_probe: family=AF_INET src=([^ ]+) dest=([^ ]+) .* data_len=([^ ]+) snd_nxt=([^ ]+) snd_una=([^ ]+) snd_cwnd=([^ ]+) ssthresh=([^ ]+) snd_wnd=([^ ]+) srtt=([^ ]+) rcv_wnd=([^ ]+)'

# Read the input file line by line
with open(input_file, 'r') as file:
    for line in file:
        # Use regular expression to find matches in each line
        matches = re.findall(pattern, line)
        for match in matches:
            time_values.append(float(match[0]))
            src_values.append(match[1])
            dest_values.append(match[2])
            data_len_values.append(int(match[3]))
            snd_nxt_values.append(int(match[4], 16))
            snd_una_values.append(int(match[5], 16))
            snd_cwnd_values.append(int(match[6]))
            ssthresh_values.append(int(match[7]))
            snd_wnd_values.append(int(match[8]))
            srtt_values.append(int(match[9]))
            rcv_wnd_values.append(int(match[10]))

# Create a DataFrame from the extracted values
data = {
    'time': time_values,
    'src': src_values,
    'dest': dest_values,
    'data_len': data_len_values,
    'snd_nxt': snd_nxt_values,
    'snd_una': snd_una_values,
    'snd_cwnd': snd_cwnd_values,
    'ssthresh': ssthresh_values,
    'snd_wnd': snd_wnd_values,
    'srtt': srtt_values,
    'rcv_wnd': rcv_wnd_values
}
df = pd.DataFrame(data)


# Filter communication to server 172.3.0.0/24 only
combined_df = df[df['src'].str.contains(
    '172.3.') | df['dest'].str.contains('172.3.')]

# copy send congestion window from server to client dataframe for analysis


def get_cwnd():

    client_cwnd_values = []
    client_cwnd = 0

    for host, server_cwnd in zip(combined_df['src'], combined_df['snd_cwnd']):
        if '172.3.0.5' in host:
            client_cwnd = server_cwnd * MSS
            client_cwnd_values.append(0)
        elif '172.1.0.101' in host:
            client_cwnd_values.append(client_cwnd)

    # Add 'cwnd' column to the DataFrame
    combined_df['cwnd'] = client_cwnd_values
    # combined_df['cwnd'] = combined_df['cwnd'].astype(int)
    # print(combined_df)


def convert_timestamp():
    # Convert the 'timestamp' column to pandas datetime object
    combined_df['time'] = pd.to_datetime(combined_df['time'], unit='s')

    # Extract milliseconds part from the timestamp
    combined_df['milliseconds'] = combined_df['time'].apply(
        lambda x: int((x.microsecond / 1000)))

    # Create a timedelta object with milliseconds
    combined_df['milliseconds_delta'] = combined_df['milliseconds'].apply(
        lambda x: pd.Timedelta(milliseconds=x))

    # Get the current time
    current_time = pd.to_datetime('now')

    # Add milliseconds to the current time
    combined_df['timestamp'] = current_time + combined_df['milliseconds_delta']


get_cwnd()
convert_timestamp()

client_df = combined_df[combined_df['dest'].str.contains('172.3.')]
server_df = combined_df[combined_df['src'].str.contains('172.3.')]


# data acknowledged by the client can be found in 'data_len'
client_df['ackd_data'] = client_df['data_len']

# Group by 'src' and 'dest', then calculate cumulative sum of 'ackd_data'
client_df['cum_ackd_data'] = client_df.groupby(['src', 'dest'])[
    'ackd_data'].cumsum()


# Calculate the difference between 'snd_nxt' and 'snd_una' and add it as a new column
client_df['cum_rcv'] = client_df['cum_ackd_data'] + client_df['rcv_wnd']


# Group by 'src' and 'dest', then calculate cumulative sum of 'data_len'
client_df['cum_data_len'] = client_df.groupby(['src', 'dest'])[
    'data_len'].cumsum()

# get minimum of rcv_wnd and cwnd
client_df['min_wnd'] = client_df[['rcv_wnd', 'cwnd']].min(axis=1)

# export dataframe to csv
client_df.to_csv(output_file, index=False)
