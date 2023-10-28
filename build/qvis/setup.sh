#!/bin/bash

# Log file path
LOG_FILE="/setup.log"

# Function to log messages
log_message() {
    local message="$1"
    echo "$(date +"%Y-%m-%d %T"): $message"
    echo "$(date +"%Y-%m-%d %T"): $message" >> "$LOG_FILE"
}

# Function to run a command and log its output
run_and_log_command() {
    local command="$1"
    log_message "Running command: $command"
    echo "Output of command: $command" >> "$LOG_FILE"
    eval "$command" 2>&1 | tee -a "$LOG_FILE"
}

# Update Ubuntu 
run_and_log_command "apt update && apt upgrade -y"

# Install dependencies 
run_and_log_command "apt install git vim npm -y"

# Clone qvis repository and install npm packages
run_and_log_command "git clone https://github.com/quiclog/qvis.git"
run_and_log_command "cd /qvis/visualizations/ && npm install"

log_message "Script execution complete."
