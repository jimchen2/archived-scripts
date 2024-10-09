import socket

def receive_data(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))  # Binds to all available interfaces
    server_socket.listen(1)
    while True:
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")

        data_received = 0
        try:
            while True:
                data = conn.recv(8192)
                if not data:
                    break
                data_received += len(data)
        finally:
            conn.close()

if __name__ == "__main__":
    receive_data(12345)