import time
import os
import subprocess

pid=os.getpid()


def run_command(command):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Error output: {e.stderr.decode()}")

def kill():

    # Command to run
    command = [
        "kill",
        "-s",
        "SIGUSR1",
        f"{pid}",
    ]
    run_command(command)

print(pid)

time.sleep(5)
kill()
