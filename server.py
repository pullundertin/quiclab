import os
import time

# Path to the file to monitor
file_path = "file.txt"

# String to wait for in the file
target_string = "start_command"


# Function to check if the target string is in the file
def check_file_for_string(file_path, target_string):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            return target_string in content
    except FileNotFoundError:
        return False

# Wait for the target string to appear in the file
print("Waiting for the target string in the file...")
while not check_file_for_string(file_path, target_string):
    time.sleep(1)  # Sleep for 1 second before checking again

# Target string found, execute the command
print("Target string found! Executing the command.")

