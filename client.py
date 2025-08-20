import socket

HOST = '127.0.0.1'  # Connect to local server
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

client.sendall(b'Hello local server!')
data = client.recv(1024)
print(f"Received: {data.decode()}")

client.close()

