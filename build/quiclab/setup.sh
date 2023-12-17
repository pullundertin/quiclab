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
run_and_log_command "apt update"
log_message "Ubuntu update complete."

# Upgrade packages
run_and_log_command "apt upgrade -y"
log_message "Package upgrade complete."

# Install dependencies
run_and_log_command "apt install git vim python-is-python3 pip curl iputils-ping net-tools bc iproute2 ethtool libssl-dev python3-dev nginx tcpdump wget python3-psutil iptables -y"
log_message "Dependency installation complete."

# Install aioquic
run_and_log_command "git clone https://github.com/aiortc/aioquic.git"
run_and_log_command "pip install aioquic"
run_and_log_command "cd /aioquic"
run_and_log_command "pip install --upgrade pip setuptools"
run_and_log_command "pip install -e ."
run_and_log_command "pip install asgiref dnslib jinja2 'flask<2.2' httpbin starlette 'werkzeug<2.1' wsproto"
log_message "aioquic installation complete."

# Prepare nginx
run_and_log_command "openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /example.key -out /example.crt -subj \"/C=DE/ST=Berlin/L=GERMANY/O=Dis/CN=www.example.com\""
run_and_log_command "ln -s /data/data.log /var/www/html/data.log"
log_message "Nginx preparation complete."

# Install quic-go
run_and_log_command "cd / && git clone https://github.com/quic-go/quic-go.git"
architecture=$(uname -m)
if [ "$architecture" == "x86_64" ]; then
    run_and_log_command "cd / && wget https://go.dev/dl/go1.21.3.linux-amd64.tar.gz"
    run_and_log_command "rm -rf /usr/local/go && tar -C /usr/local -xzf go1.21.3.linux-amd64.tar.gz"
elif [ "$architecture" == "aarch64" ]; then
    run_and_log_command "cd / && wget https://go.dev/dl/go1.21.3.linux-arm64.tar.gz"
    run_and_log_command "rm -rf /usr/local/go && tar -C /usr/local -xzf go1.21.3.linux-arm64.tar.gz"
else
    log_message "The architecture is not recognized: $architecture"
fi
run_and_log_command "ln -s /usr/local/go/bin/go /usr/bin/go"
run_and_log_command "cd /quic-go && go get -d ./..."
log_message "quic-go installation complete."

# Install pandas
run_and_log_command "pip install pandas"
log_message "Pandas installation complete."

# Install Docker
run_and_log_command "pip install docker"
log_message "Docker installation complete."

log_message "Script execution complete."


