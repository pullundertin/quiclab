import time
import os
import psutil


def kill_process_and_children(process_name):
    time.Sleep(3)
    print(f"{os.getenv('HOST')}: stopping quic-go server..")
    for process in psutil.process_iter(attrs=['pid', 'ppid', 'name']):
        if process.info['name'] == process_name:
            parent_pid = process.info['ppid']
            child_pid = process.info['pid']

            # Kill child processes
            try:
                parent = psutil.Process(child_pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                psutil.wait_procs(
                    [child for child in parent.children(recursive=True)], timeout=5)

                # Kill the parent process
                parent.terminate()
                parent.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                pass


process_name = "go"
kill_process_and_children(process_name)
