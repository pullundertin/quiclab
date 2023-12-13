
import time
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
import logging
import argparse


# Configure logging
logging.basicConfig(filename='/shared/logs/output.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def arguments():
    # python /scripts/run_client.py --mode http --window_scaling 1 --rmin 4096 --rdef 131072 --rmax 6291456
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: http, aioquic, quicgo')

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
    parser.add_argument('--pcap', type=str,
                        help='pcap_path')
    parser.add_argument('--qlog', type=str,
                        help='qlog_path')
    parser.add_argument('--iteration', type=str,
                        help='number of iteration')

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
    command = f"tcpdump -i eth0 -w {args.pcap}/{args.iteration}client_1.pcap -n"
    logging.info(f"{os.getenv('HOST')}: tcpdump started.")
    run_command(command)


def aioquic():
    URL = "https://172.3.0.5:4433/data.log"
    max_data = 2000000
    request = (URL + ' ') * 1
    command = f"python /aioquic/examples/http3_client.py -k {request} --secrets-log {keys_path} --quic-log $QLOG_PATH_CLIENT --zero-rtt --session-ticket $TICKET_PATH"
    # command = f"python /aioquic/examples/http3_client.py -k {URL} --max-data {max_data} --secrets-log $KEYS_PATH --quic-log $QLOG_PATH_CLIENT --zero-rtt --session-ticket $TICKET_PATH"
    # command = f"python /aioquic/examples/http3_client.py -k {URL} {URL} --secrets-log $KEYS_PATH --quic-log $QLOG_PATH_CLIENT --zero-rtt --session-ticket $TICKET_PATH"
    logging.info(f"{os.getenv('HOST')}: sending aioquic request...")
    # run_command(command)
    run_command(command)


def quicgo():
    URL = "https://172.3.0.5:6121/data.log"
    os.chdir("/quic-go/example/client")
    command = f"go run main.go --insecure --keylog '{keys_path}' --qlog {URL}"
    # command = f"go run main.go --insecure --keylog $KEYS_PATH --qlog {URL} {URL}"
    logging.info(f"{os.getenv('HOST')}: sending quic-go request...")
    run_command(command)


def http(args):
    tcp_settings(args)
    URL = "https://172.3.0.5:443/data.log"
    request = (URL + ' ') * 1
    os.environ['SSLKEYLOGFILE'] = keys_path
    # {URL} -o /dev/null {URL} -o /dev/null"
    command = f"curl -k {URL} -o /dev/null"
    logging.info(f"{os.getenv('HOST')}: sending http request...")
    run_command(command)


def client_request(args):

    if args.mode == "http":
        http(args)
    elif args.mode == "aioquic":
        aioquic()
    elif args.mode == "quicgo":
        quicgo()


def kill_tcpdump():
    command = f"pkill tcpdump"
    run_command(command)

# def kill(process_name):

#     for process in psutil.process_iter(attrs=['pid', 'name']):
#         if process.info['name'] == process_name:

#             try:
#                 pid = process.info['pid']
#                 p = psutil.Process(pid)
#                 p.terminate()
#                 logging.info(f"{os.getenv('HOST')}: {process_name} stopped.")
#             except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
#                 logging.info(f"{os.getenv('HOST')} Error: {process_name}")
#                 pass


def change_ip(old_ip, new_ip):
    try:
        command = f"ip addr add {new_ip}/24 dev eth0 && ip addr del {old_ip}/24 dev eth0"
        run_command(command)
        logging.info(f"{os.getenv('HOST')}: IP address changed to {new_ip}")
    except Exception as e:
        logging.info(f"{os.getenv('HOST')}: An error occurred: {e}")


if __name__ == "__main__":

    args = arguments()
    keys_path = f"/shared/keys/client.key"

    with ThreadPoolExecutor() as executor:

        thread_1 = executor.submit(tcpdump, args)
        time.sleep(3)
        thread_2 = executor.submit(client_request, args)

        if (args.migration == 'True'):
            time.sleep(1)
            thread_3 = executor.submit(change_ip, '172.1.0.101', '172.1.0.102')
            wait([thread_3])
            time.sleep(2)
            change_ip('172.1.0.102', '172.1.0.101')
        wait([thread_2])
        logging.info(f"{os.getenv('HOST')}: request completed.")

        time.sleep(3)
        kill_tcpdump()
        # kill("tcpdump")
        wait([thread_1])
