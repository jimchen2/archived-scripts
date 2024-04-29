#!/bin/bash

config_file="./test.yml"

# Function to log messages
log() {
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1" | tee -a logs/script.log
}

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to kill all clash processes
kill_clash() {
    log "Killing all clash processes..."
    pids=$(pgrep clash)
    if [ -n "$pids" ]; then
        sudo kill $pids 2>&1 | tee -a logs/script.log
        log "Clash processes killed."
    else
        log "No clash processes found."
    fi
}

# Function to kill processes on specific ports
kill_ports() {
    # Get the HTTP and SOCKS ports from the configuration file
    http_port=$(awk '/^port:/ {print $2}' "$config_file")
    socks_port=$(awk '/socks-port:/ {print $2}' "$config_file")
    log "Killing processes on ports $http_port and $socks_port..."
    sudo kill $(sudo lsof -t -i:$http_port) 2>&1 | tee -a logs/script.log
    sudo kill $(sudo lsof -t -i:$socks_port) 2>&1 | tee -a logs/script.log
    log "Processes on ports $http_port and $socks_port killed."
}

# Function to initialize the proxy
init_proxy() {
    log "Starting clash..."
    clash -d . -f "$config_file" > logs/clash.log 2>&1 &
    clash_pid=$!

    # Get the HTTP and SOCKS ports from the configuration file
    http_port=$(awk '/^port:/ {print $2}' "$config_file")
    socks_port=$(awk '/socks-port:/ {print $2}' "$config_file")

    # Get the external controller port from the configuration file
    external_controller_port=$(awk -F"'" '/external-controller:/ {print $2}' "$config_file" | awk -F':' '{print $2}')

    log "Proxy initialized."

}

# Function to switch proxy server
switch_proxy() {
    # Get the list of available proxy servers
    servers=$(awk '/^  - name:/{print $3}' "$config_file" | tr -d '"')

    if [ -z "$servers" ]; then
        log "No proxy servers found in $config_file"
        return 1
    fi

    # Get the external controller port from the configuration file
    external_controller_port=$(awk -F"'" '/external-controller:/ {print $2}' "$config_file" | awk -F':' '{print $2}')

    # Display the list of servers and prompt the user to choose one
    select server in $servers; do
        if [[ -n $server ]]; then
            log "Switching proxy to $server..."
            log "API Call: curl -X PUT -H \"Content-Type: application/json\" -d '{\"name\":\"$server\"}' http://localhost:$external_controller_port/proxies/GLOBAL"
            curl -X PUT -H "Content-Type: application/json" -d "{\"name\":\"$server\"}" http://localhost:$external_controller_port/proxies/GLOBAL 2>&1 | tee -a logs/script.log
            if [ $? -eq 0 ]; then
                log "Proxy switched to $server."
            else
                log "Error: Failed to switch proxy to $server."
            fi
            break
        else
            log "Invalid choice. Please try again."
        fi
    done
}

# Function to display help
display_help() {
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  init         Initialize the proxy"
    echo "  switch       Switch the proxy server"
    echo "  killports    Kill processes on the HTTP and SOCKS ports specified in the configuration file"
    echo "  killclash    Kill all clash processes"
    echo "  help         Display this help message"
}

# Main script logic
case $1 in
    init)
        init_proxy
        ;;
    switch)
        switch_proxy
        ;;
    killports)
        kill_ports
        ;;
    killclash)
        kill_clash
        ;;
    help)
        display_help
        ;;
    *)
        display_help
        ;;
esac
