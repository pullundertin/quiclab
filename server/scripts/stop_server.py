import os
import subprocess
import logging
import argparse
import psutil
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

HOST = os.getenv("HOST")
mode = 'http'
args = None

# Configure logging
logging.basicConfig(filename='/shared/logs/output.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def arguments():

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: http, aioquic, quicgo')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the flag value in your script
    if args.mode:
        global mode
        mode = args.mode


def map_function():
    # Create a dictionary that maps string keys to functions
    function_mapping = {
        "http": http,
        "aioquic": aioquic,
        "quicgo": quicgo
    }

    # Call the chosen function based on the string variable
    if mode in function_mapping:
        function_call = function_mapping[mode]
        function_call()
    else:
        logging.info("Function not found.")


def initialize():
    arguments()


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"{os.getenv('HOST')}: {process.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on {os.getenv('HOST')}: {e}")
        logging.info(f"Error {os.getenv('HOST')} output: {e.stderr.decode()}")


def tcpprobe():
    # Save tcpprobe to file
    trace_file_path = "/sys/kernel/debug/tracing/trace"
    output_file_path = "/shared/tcpprobe/server.log"

    with open(output_file_path, "w") as output_file:
        # Use subprocess to run cat command and redirect its output to the file
        subprocess.run(["cat", trace_file_path],
                       stdout=output_file, stderr=output_file, check=True)
    logging.info(f"{HOST}: tcpprobe written to file.")

    # Run the converter.py script
    command = "python /scripts/converter.py"
    run_command(command)
    logging.info(f"{HOST}: tcpprobe converted.")

    # Disable tcp events in tcpprobe
    tcp_probe_enable_path = "/sys/kernel/debug/tracing/events/tcp/enable"
    with open(tcp_probe_enable_path, "w") as enable_file:
        enable_file.write("0")
        logging.info(f"{HOST}: tcpprobe disabled.")


def http():

    tcpprobe()
    kill('nginx')
    kill('tcpdump')


def aioquic():

    kill('tcpdump')
    kill('python')


def quicgo():

    kill('tcpdump')
    kill('go')
    kill('/tmp/go-build')


def kill(process_name):

    for process in psutil.process_iter(attrs=['pid', 'ppid', 'name', 'cmdline']):
        # also check by pattern
        if process.info['name'] == process_name or process_name in process.info['cmdline'][0]:

            try:
                pid = process.info['pid']
                p = psutil.Process(pid)
                p.terminate()
                logging.info(f"{os.getenv('HOST')}: {process_name} stopped.")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                logging.info(f"{os.getenv('HOST')} Error: {process_name}")
                pass


if __name__ == "__main__":
    initialize()
    map_function()
