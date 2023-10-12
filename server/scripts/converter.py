import pandas as pd
import re

pd.options.mode.chained_assignment = None

input_file = "/shared/tcpprobe/server.log"
output_file = "/shared/tcpprobe/results.csv"
output_directory = "/shared/tcpprobe/"

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
            snd_nxt_values.append(int(match[4],16))  
            snd_una_values.append(int(match[5],16))  
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
filtered_df = df[df['src'].str.contains('172.3.') | df['dest'].str.contains('172.3.')]

# Normalize the 'time' column to zero
min_time = min(filtered_df['time'])
filtered_df['time'] -= min_time

# TODO: combine the right value pairs from client and server
# Calculate the difference between 'snd_nxt' and 'snd_una' and add it as a new column
filtered_df['ackd_data'] = filtered_df['snd_nxt'] - filtered_df['snd_una'] 

# Calculate the difference between 'snd_nxt' and 'snd_una' and add it as a new column
filtered_df['cum_rcv'] = filtered_df['ackd_data'] + filtered_df['rcv_wnd'] 

# Group by 'src' and 'dest', then calculate cumulative sum of 'ackd_data'
filtered_df['cum_ackd_data'] = filtered_df.groupby(['src', 'dest'])['ackd_data'].cumsum()

# Group by 'src' and 'dest', then calculate cumulative sum of 'data_len'
filtered_df['cum_data_len'] = filtered_df.groupby(['src', 'dest'])['data_len'].cumsum()


# Save filtered and normalized DataFrame to CSV files with ascending numbers
file_counter = 1
for _, group_df in filtered_df.groupby(['src', 'dest']):
    src_output_file = f"{output_directory}results_{file_counter}.csv"
    group_df.to_csv(src_output_file, index=False)
    file_counter += 1

# # Save the filtered and normalized DataFrame to a CSV file
# filtered_df.to_csv(output_file, index=False)

# # Print the DataFrame
# print(filtered_df)
