import socket


server_ip = "127.0.0.1"
port = 5566
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Trying to connect to 127.0.0.1:5566")
client_socket.connect((server_ip, port))

while True:
    message = input("You: ")
    if message.lower() == "exit":
        break
    client_socket.send(message.encode())
    replay = client_socket.recv(1024)
    print("Server", replay.decode())

client_socket.close()
