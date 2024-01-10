
import time
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
import logging
import argparse


# Configure logging
logging.basicConfig(filename=os.getenv('LOG_PATH'), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def arguments():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: tcp, aioquic, quicgo')

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
    parser.add_argument('--number_of_streams', type=int,
                        help='set number of parallel streams')
    parser.add_argument('--file_name_prefix', type=str,
                        help='prefix for pcap files')

    args = parser.parse_args()

    logging.info(f"{os.getenv('HOST')}: {args.mode} mode enabled")

    return args


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"{os.getenv('HOST')}: {process.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on {os.getenv('HOST')}: {e}")
        logging.info(f"Error {os.getenv('HOST')} output: {e.stderr.decode()}")


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
    request = (URL + ' ') * args.number_of_streams
    command = f"python /aioquic/examples/http3_client.py -k {request} --secrets-log $KEYS_PATH --quic-log $QLOG_PATH_CLIENT" #--zero-rtt --session-ticket $TICKET_PATH"
    # command = f"python /aioquic/examples/http3_client.py -k {URL} --max-data {max_data} --secrets-log $KEYS_PATH --quic-log $QLOG_PATH_CLIENT --zero-rtt --session-ticket $TICKET_PATH"
    # command = f"python /aioquic/examples/http3_client.py -k {URL} {URL} --secrets-log $KEYS_PATH --quic-log $QLOG_PATH_CLIENT --zero-rtt --session-ticket $TICKET_PATH"
    logging.info(f"{os.getenv('HOST')}: sending aioquic request...")
    # run_command(command)
    run_command(command)


def quicgo(args):
    URL = "https://172.3.0.5:6121/data.log"
    os.chdir("/quic-go/example/client")

    request = (URL + ' ') * args.number_of_streams

    # TODO KEYS_PATH funktioniert nur ohne vorangestelltem Punkt!
    command = f"go run main.go --insecure --keylog /shared/keys/client.key --qlog {request}"
    # command = f"go run main.go --insecure --keylog $KEYS_PATH --qlog {URL} {URL}"
    logging.info(f"{os.getenv('HOST')}: sending quic-go request...")
    run_command(command)


def tcp(args):
    tcp_settings(args)
    URL = "https://172.3.0.5:443/data.log"
    os.environ['SSLKEYLOGFILE'] = os.getenv('KEYS_PATH')

    if args.number_of_streams > 1:
        sum_of_requests = ''
        for index in range(args.number_of_streams):
            sum_of_requests += f"{URL} "
        command = f"curl -k -Z -o /dev/null {sum_of_requests}"
    else:
        command = f"curl -k -o /dev/null {URL}"
    logging.info(f"{os.getenv('HOST')}: sending tcp request...")
    run_command(command)



def client_request(args):

    if args.mode == "tcp":
        tcp(args)
    elif args.mode == "aioquic":
        aioquic(args)
    elif args.mode == "quicgo":
        quicgo(args)


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
