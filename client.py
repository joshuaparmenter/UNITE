import socket

HOST = 'friend_public_ip_here'  # Replace with their public IP
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

client.sendall(b'Hello from client!')
data = client.recv(1024)
print(f"Received: {data.decode()}")

client.close()

