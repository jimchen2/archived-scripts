from evdev import InputDevice, categorize, ecodes

# Replace 'X' with the actual event number of your keyboard
device = InputDevice('/dev/input/event4')  

# Create a named pipe for communication
fifo = open("/tmp/touchpad_fifo", "w")

# Loop and handle keyboard events
for event in device.read_loop():
    if event.type == ecodes.EV_KEY:
        if event.value == 1:  # Key press
            key = categorize(event)
            if key.keycode not in ['KEY_LEFTALT', 'KEY_RIGHTALT', 'KEY_LEFTCTRL', 'KEY_RIGHTCTRL',
                                   'KEY_LEFTMETA', 'KEY_RIGHTMETA', 'KEY_TAB', 'KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                fifo.write("key_pressed\n")
                fifo.flush()
