import socket
import threading

clients = {}

lock = threading.Lock()

def handle_client(client_socket, adder):
    print(f"client is connecting: {adder}")

    try:
        username = client_socket.recv(1024).decode()

        with lock:
            clients[username] = client_socket
        
        print(f"{username} conneted from {adder}")
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            message = data.decode()
            to_user, msg = message.split("|", 1)

            print(f"{username} -> {to_user}: {msg}")

            with lock:
                if to_user in clients:
                    clients[to_user].send(
                        f"From {username}: {msg}".encode()
                    )
                else:
                    client_socket.send(
                        f"User {to_user} is not connected".encode()
                    )
    except Exception as e:
        print("Error: ", e)
    
    finally:
        with lock:
            if username in clients:
                del clients[username]
        
        client_socket.close()
        print(f"{username} disconnected")

def main():
    server_ip = "0.0.0.0"
    port = 5566
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_ip, port))
    server.listen(5)
    print("server is running....")

    while True:
        client_socket, adder = server.accept()
        thread = threading.Thread(
            target= handle_client,
            args=(client_socket,adder)
        )
        thread.start()

if __name__ == "__main__":
    main()







