import socket
import time

def send_data(server_ip, server_port, duration):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    start_time = time.time()

    while time.time() - start_time < duration:
        client_socket.send(b'X' * 1460)

    client_socket.close()

if __name__ == "__main__":
    send_data('SERVER_IP', 12345, 10)  