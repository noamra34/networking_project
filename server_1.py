import socket
import threading

clients = {} # format: {username: client_socket}
lock = threading.Lock()

def broadcast_user_list():
    """שולח לכל המשתמשים את רשימת המחוברים העדכנית"""
    with lock:
        # יוצר רשימה של שמות מופרדים בפסיקים
        user_list = ",".join(clients.keys())
        message = f"LIST|{user_list}"
        
        for user, sock in clients.items():
            try:
                sock.send(message.encode())
            except:
                pass # נטפל בניתוקים בלולאה הראשית

def handle_client(client_socket, addr):
    print(f"Connection attempt from: {addr}")
    username = ""
    
    try:
        # שלב ההתחברות
        username = client_socket.recv(1024).decode()
        
        with lock:
            if username in clients:
                client_socket.send("REFUSED".encode())
                client_socket.close()
                return
            else:
                client_socket.send("APPROVE".encode())
                clients[username] = client_socket
        
        print(f"User connected: {username}")
        broadcast_user_list() # עדכון רשימה לכולם

        # לולאת קבלת הודעות
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            message = data.decode()
            
            # בדיקה אם ההודעה היא בפורמט הנכון
            if "|" in message:
                target_user, msg_content = message.split("|", 1)
                
                # שליחת ההודעה ליעד (דרך השרת)
                # אנו שולחים ליעד: "MSG|מי_שלח|התוכן"
                with lock:
                    if target_user in clients:
                        outgoing_format = f"MSG|{username}|{msg_content}"
                        clients[target_user].send(outgoing_format.encode())
                    else:
                        # אופציונלי: הודעת שגיאה לשולח
                        pass

    except Exception as e:
        print(f"Error with user {username}: {e}")
    
    finally:
        with lock:
            if username in clients:
                del clients[username]
        
        client_socket.close()
        print(f"{username} disconnected")
        broadcast_user_list() # עדכון רשימה אחרי יציאה

def main():
    server_ip = "0.0.0.0"
    port = 5566
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_ip, port))
    server.listen(5)
    print(f"Server running on {server_ip}:{port}...")

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, addr)
        )
        thread.start()

if __name__ == "__main__":
    main()