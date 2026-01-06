import socket
import threading
import sys

# הגדרות שרת (זהות ל-GUI)
SERVER_IP = "127.0.0.1"
PORT = 5566

def receive_messages(client_socket):
    """פונקציה שרצה ב-Thread נפרד ומאזינה להודעות מהשרת"""
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                print("\n[!] Disconnected from server.")
                break
            
            # טיפול בעדכון רשימת משתמשים
            if data.startswith("LIST|"):
                users_str = data.split("|")[1]
                print(f"\n[System] Active users: {users_str}")
            
            # טיפול בהודעה נכנסת
            elif data.startswith("MSG|"):
                # הפורמט הוא MSG|sender|content
                parts = data.split("|", 2)
                if len(parts) == 3:
                    sender = parts[1]
                    content = parts[2]
                    print(f"\n[{sender}]: {content}")
                    
        except Exception as e:
            print(f"\n[!] Error receiving data: {e}")
            break
    
    client_socket.close()
    sys.exit()

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((SERVER_IP, PORT))
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        return

    # --- שלב ההתחברות (Login) ---
    while True:
        username = input("Enter your username: ")
        if not username: continue
        
        # שליחת השם לבדיקה
        client_socket.send(username.encode())
        
        # קבלת תשובה (APPROVE / REFUSED)
        try:
            response = client_socket.recv(1024).decode()
            if response == "APPROVE":
                print(f"Successfully logged in as {username}!")
                break
            else:
                print("Username already taken or refused. Try again.\n")
                # צריך להתחבר מחדש כי השרת מנתק בסירוב
                client_socket.close()
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((SERVER_IP, PORT))
        except:
            print("Error during login.")
            return

    # --- הפעלת האזנה במקביל ---
    # מפעילים Thread שיקשיב להודעות נכנסות כדי שלא יתקע את ההקלדה
    listener_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    listener_thread.daemon = True # ייסגר אוטומטית כשהתוכנית הראשית תיסגר
    listener_thread.start()

    # --- לולאת שליחת הודעות ---
    print("-" * 40)
    print("Instructions:")
    print("To send a message, use format: target|message")
    print("Example: user2|hello how are you?")
    print("Type 'exit' to quit.")
    print("-" * 40)

    while True:
        msg = input() # מחכה לקלט מהמשתמש
        
        if msg.lower() == 'exit':
            break
        
        # בדיקה שהפורמט תקין לפני שליחה (אופציונלי, אבל מומלץ)
        if "|" in msg:
            client_socket.send(msg.encode())
        else:
            print("[!] Invalid format. Please use: target|message")

    client_socket.close()
    print("Goodbye!")

if __name__ == "__main__":
    main()