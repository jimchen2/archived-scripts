#!/bin/bash

# Initial state
state="enabled"
echo "Initial state: $state"  # Debugging output
timer_pid=0  # Variable to store the timer's PID
state_file="/tmp/touchpad_state"  # Temporary file to store the state

# Function to disable touchpad
disable_touchpad() {
    echo "Disabling touchpad"  # Debugging output
    gsettings set org.gnome.desktop.peripherals.touchpad send-events "disabled"
    echo "Touchpad disabled"  # Debugging output
}

# Function to enable touchpad
enable_touchpad() {
    echo "Enabling touchpad"  # Debugging output
    gsettings set org.gnome.desktop.peripherals.touchpad send-events "enabled"
    echo "Touchpad enabled"  # Debugging output
}

# Timer function (using `sleep`)
timer() {
    echo "Timer started with PID: $$"  # Debugging output
    sleep 0.5
    if [[ "$state" == "disabled" ]]; then
        enable_touchpad
        echo "enabled" > "$state_file"  # Write the updated state to the temporary file
        echo "Timer (PID: $$) expired, touchpad enabled"  # Debugging output
    else
        echo "Timer (PID: $$) expired, but touchpad state is not disabled ($state)"  # Debugging output
    fi
}

# Read from the named pipe continuously
while read -r line; do
    echo "Received line: $line"  # Debugging output
    echo "Current touchpad state: $state"  # Debugging output before processing the line
    if [[ "$line" == "key_pressed" ]]; then
        echo "Key pressed event received"  # Debugging output
        if [[ "$state" == "enabled" ]]; then
            echo "Touchpad is enabled, disabling it"  # Debugging output
            disable_touchpad
            state="disabled"  # Update the state variable here
            echo "Touchpad state updated to: $state"  # Debugging output
            # Check if a timer is already running
            if [[ $timer_pid -ne 0 ]]; then
                echo "Stopping previous timer with PID: $timer_pid"  # Debugging output
                kill $timer_pid  # Stop the previous timer
                echo "Previous timer stopped"  # Debugging output
            fi
            timer &  # Start a new timer
            timer_pid=$!  # Store the PID of the new timer
            echo "Started new timer with PID: $timer_pid"  # Debugging output
        else
            echo "Touchpad is already disabled, ignoring key press event"  # Debugging output
        fi
    else
        echo "Unknown event received: $line"  # Debugging output
    fi
    # Read the updated state from the temporary file
    if [[ -f "$state_file" ]]; then
        state=$(cat "$state_file")
        echo "Updated touchpad state from file: $state"  # Debugging output
    fi
    echo "Processing complete for line: $line"  # Debugging output
    echo "Updated touchpad state: $state"  # Debugging output after processing the line
done < <(tail -f /tmp/touchpad_fifo)  # Use process substitution
