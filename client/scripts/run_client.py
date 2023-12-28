
import time
import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from modules.logs import log_config
from modules.commands import run_command
import logging
import argparse


def arguments():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: tcp, aioquic, quicgo, lsquic')

    parser.add_argument('-w', '--window_scaling', type=str,
                        help='enable/disable receiver window scaling')
    parser.add_argument('--rmin', type=str,
                        help='minimum recieve window in bytes')
    parser.add_argument('--rdef', type=str,
                        help='default recieve window in bytes')
    parser.add_argument('--rmax', type=str,
                        help='maximum recieve window in bytes')
    parser.add_argument('--migration', choices=['True', 'False'],
                        help='enable/disable connection migration simulation')
    parser.add_argument('--parallel', choices=['True', 'False'],
                        help='enable/disable parallel downloads')
    parser.add_argument('--file_name_prefix', type=str,
                        help='prefix for pcap files')

    args = parser.parse_args()

    logging.info(f"{os.getenv('HOST')}: {args.mode} mode enabled")

    return args


def tcp_settings(args):
    command = f"sysctl -w net.ipv4.tcp_window_scaling={args.window_scaling}"
    run_command(command)
    command = f"sysctl -w net.ipv4.tcp_rmem='{args.rmin} {args.rdef} {args.rmax}'"
    run_command(command)


def tcpdump(args):
    command = f"tcpdump -i eth0 -w $PCAP_PATH/{args.file_name_prefix}client_1.pcap -n"
    logging.info(f"{os.getenv('HOST')}: tcpdump started.")
    run_command(command)


def aioquic(args):
    URL = "https://172.3.0.5:4433/data.log"
    max_data = 2000000
    if args.parallel == 'True':
        # TODO how to downlaod multiple files
        command = f"python /aioquic/examples/http3_client.py -k {URL} {URL} --output-dir /shared/downloads --filename {args.file_name_prefix} --secrets-log $KEYS_PATH --quic-log $QLOG_PATH_CLIENT --zero-rtt --session-ticket $TICKET_PATH"
        logging.info(
            f"{os.getenv('HOST')}: sending parallel aioquic request...")
    else:
        command = f"python /aioquic/examples/http3_client.py -k {URL} --output-dir /shared/downloads --filename {args.file_name_prefix} --secrets-log $KEYS_PATH --quic-log $QLOG_PATH_CLIENT --zero-rtt --session-ticket $TICKET_PATH"
        logging.info(f"{os.getenv('HOST')}: sending aioquic request...")
    # command = f"python /aioquic/examples/http3_client.py -k {URL} --max-data {max_data} --secrets-log $KEYS_PATH --quic-log $QLOG_PATH_CLIENT --zero-rtt --session-ticket $TICKET_PATH"
    # command = f"python /aioquic/examples/http3_client.py -k {URL} {URL} --secrets-log $KEYS_PATH --quic-log $QLOG_PATH_CLIENT --zero-rtt --session-ticket $TICKET_PATH"
    # run_command(command)
    run_command(command)


def quicgo(args):
    URL = "https://172.3.0.5:6121/data.log"
    os.chdir("/quic-go/example/client")
    # TODO KEYS_PATH funktioniert nur ohne vorangestelltem Punkt!
    command = f"go run main.go --insecure --output-dir /shared/downloads --filename {args.file_name_prefix} --keylog /shared/files/client.key --qlog {URL}"
    # command = f"go run main.go --insecure --keylog $KEYS_PATH --qlog {URL} {URL}"
    logging.info(f"{os.getenv('HOST')}: sending quic-go request...")
    run_command(command)


def create_folder_in_lsquic_root(lsquic_client_directory):
    if os.path.exists(lsquic_client_directory):
        remove_old_files(lsquic_client_directory)
    else:
        os.makedirs(lsquic_client_directory)


def remove_old_files(lsquic_client_directory):
    for filename in os.listdir(lsquic_client_directory):
        file_path = os.path.join(lsquic_client_directory, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
            logging.info(
                f"{os.getenv('HOST')}: Failed to delete {file_path}. Reason: {e}")


def lsquic(args):
    lsquic_client_directory = '/lsquic/client'
    create_folder_in_lsquic_root(lsquic_client_directory)
    # TODO download filename, qlog
    URL = "172.3.0.5:4444"
    os.chdir("/lsquic/bin")
    # TODO KEYS_PATH funktioniert nur ohne vorangestelltem Punkt!
    command = f"./http_client -H www.example.com -s 172.3.0.5:4444 -p /data.log -l qlog=debug -L crit -7 {lsquic_client_directory} -0 {lsquic_client_directory}/lsquic_ticket.txt -G {lsquic_client_directory}"
    logging.info(f"{os.getenv('HOST')}: sending lsquic request...")
    run_command(command)


def tcp(args):
    tcp_settings(args)
    URL = "https://172.3.0.5:443/data.log"

    os.environ['SSLKEYLOGFILE'] = os.getenv('KEYS_PATH')
    if args.parallel == 'True':
        command = f"curl -k -Z {URL} -o /shared/downloads/{args.file_name_prefix}1 {URL} -o /shared/downloads/{args.file_name_prefix}2 {URL} -o /shared/downloads/{args.file_name_prefix}3"
        logging.info(f"{os.getenv('HOST')}: sending parallel tcp request...")
    else:
        command = f"curl -k {URL} -o /shared/downloads/{args.file_name_prefix}"
        logging.info(f"{os.getenv('HOST')}: sending tcp request...")
    run_command(command)


def client_request(args):

    if args.mode == "tcp":
        tcp(args)
    elif args.mode == "aioquic":
        aioquic(args)
    elif args.mode == "quicgo":
        quicgo(args)
    elif args.mode == "lsquic":
        lsquic(args)


def kill_tcpdump():
    command = f"pkill tcpdump"
    run_command(command)


def change_ip(old_ip, new_ip):
    try:
        command = f"ip addr add {new_ip}/24 dev eth0 && ip addr del {old_ip}/24 dev eth0"
        run_command(command)
        logging.info(f"{os.getenv('HOST')}: IP address changed to {new_ip}")
    except Exception as e:
        logging.info(f"{os.getenv('HOST')}: An error occurred: {e}")


if __name__ == "__main__":

    log_config()
    args = arguments()
    with ThreadPoolExecutor() as executor:

        thread_1 = executor.submit(tcpdump, args)
        time.sleep(3)
        thread_2 = executor.submit(client_request, args)

        wait([thread_2])
        logging.info(f"{os.getenv('HOST')}: request completed.")

        time.sleep(3)
        kill_tcpdump()
        wait([thread_1])
