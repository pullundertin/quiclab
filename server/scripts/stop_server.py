import os
import subprocess
import logging
import argparse
import psutil


# Configure logging
logging.basicConfig(filename='/shared/logs/output.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def arguments():
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: http, aioquic, quicgo')
    parser.add_argument('--iteration', type=str,
                        help='number of iteration')

    args = parser.parse_args()

    return args


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"{os.getenv('HOST')}: {process.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on {os.getenv('HOST')}: {e}")
        logging.info(f"Error {os.getenv('HOST')} output: {e.stderr.decode()}")


def tcpprobe(iteration):
    def cat_trace_file_and_write_to_file():
        with open(output_file_path, "w") as output_file:
            subprocess.run(["cat", trace_file_path],
                           stdout=output_file, stderr=output_file, check=True)
        logging.info(f"{os.getenv('HOST')}: tcpprobe written to file.")

    def process_trace_data():
        command = "python /scripts/converter.py"
        run_command(command)
        logging.info(f"{os.getenv('HOST')}: tcpprobe converted.")

    def disable_tcptrace():
        with open(tcp_probe_enable_path, "w") as enable_file:
            enable_file.write("0")
            logging.info(f"{os.getenv('HOST')}: tcpprobe disabled.")

    trace_file_path = "/sys/kernel/debug/tracing/trace"
    output_file_path = f"/shared/tcpprobe/{iteration}tcptrace.log"
    tcp_probe_enable_path = "/sys/kernel/debug/tracing/events/tcp/enable"
    cat_trace_file_and_write_to_file()
    process_trace_data()
    disable_tcptrace()


def http():
    tcpprobe(args.iteration)
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

    args = arguments()

    if args.mode == "http":
        http()
    elif args.mode == "aioquic":
        aioquic()
    elif args.mode == "quicgo":
        quicgo()
