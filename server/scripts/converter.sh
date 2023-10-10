#!/bin/bash

WORKDIR="/shared/tcpprobe"
echo "$HOST: converting tcp_probe file to csv..."

# Input file containing lines with src and dest values
input_file="$WORKDIR/server.log"

# Output CSV file name
tmp1="$WORKDIR/tmp_1.csv"
tmp2="$WORKDIR/tmp_2.csv"
output_file="$WORKDIR/results.csv"

line_count=0

# Create or overwrite the CSV file with headers

# Read each line from the input file, extract src and dest values, and append to the CSV file
while IFS= read -r line; do #&& [ "$line_count" -lt 1000 ]; do
    # timestamp=$(echo "$line" | awk '{print $4}' | awk -F':' '{print $1}')
    # echo $timestamp
    src=$(echo "$line" | grep -o 'src=[^ ]*' | awk -F'=' '{print $2}')
    dest=$(echo "$line" | grep -o 'dest=[^ ]*' | awk -F'=' '{print $2}')
    data_len=$(echo "$line" | grep -o 'data_len=[^ ]*' | awk -F'=' '{print $2}')
    snd_cwnd=$(echo "$line" | grep -o 'snd_cwnd=[^ ]*' | awk -F'=' '{print $2}')
    ssthresh=$(echo "$line" | grep -o 'ssthresh=[^ ]*' | awk -F'=' '{print $2}')
    snd_wnd=$(echo "$line" | grep -o 'snd_wnd=[^ ]*' | awk -F'=' '{print $2}')
    srtt=$(echo "$line" | grep -o 'srtt=[^ ]*' | awk -F'=' '{print $2}')
    rcv_wnd=$(echo "$line" | grep -o 'rcv_wnd=[^ ]*' | awk -F'=' '{print $2}')
    echo "$src,$dest,$data_len,$snd_cwnd,$ssthresh,$snd_wnd,$srtt,$rcv_wnd" >> "$tmp1"
    ((line_count++))
done < "$input_file"

grep -v '^[,]*$' "$tmp1" > "$tmp2"
rm -r $tmp1

echo "id,src,dest,data_len,snd_cwnd,ssthresh,snd_wnd,srtt,rcv_wnd" > "$output_file"
awk -F',' 'BEGIN {OFS=","} {print counter++,$0}' "$tmp2" >> "$output_file"
rm -r $tmp2

echo "$HOST: CSV file generated: $output_file" 


