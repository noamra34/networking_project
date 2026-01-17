import socket
import threading
import sys
from datetime import datetime

# --- הגדרות חיבור (זהות לקובץ ה-GUI) ---
SERVER_IP = "127.0.0.1" # כתובת השרת
PORT = 5566             # הפורט להתקשרות

# --- משתנים גלובליים ---
client = None
username = ""

# --- פונקציות עזר ---

def get_time():
    """מחזיר את השעה הנוכחית כסטרינג (לשימוש בהודעות)"""
    return datetime.now().strftime("%H:%M")

def receive_messages():
    """
    פונקציה שרצה ב-Thread נפרד ומאזינה להודעות מהשרת.
    במקום לעדכן מסך גרפי, היא מדפיסה את המידע לקונסולה.
    """
    global client
    while True:
        try:
            data = client.recv(1024).decode()
            if not data:
                print("\n[!] Disconnected from server.")
                break
            
            # מקרה 1: עדכון רשימת משתמשים
            if data.startswith("LIST|"):
                users_str = data.split("|")[1]
                # במקום לעדכן סרגל צד, נדפיס את הרשימה למשתמש
                print(f"\n[System] Active users updated: {users_str}")
                print("> ", end="", flush=True) # החזרת הסמן לכתיבה
            
            # מקרה 2: הודעה רגילה
            elif data.startswith("MSG|"):
                # הפורמט הוא MSG|sender|content
                parts = data.split("|", 2)
                if len(parts) == 3:
                    sender = parts[1]
                    content = parts[2]
                    timestamp = get_time()
                    
                    # הדפסה יפה של ההודעה
                    print(f"\n[{timestamp}] {sender}: {content}")
                    print("> ", end="", flush=True) # החזרת הסמן לכתיבה
                    
        except Exception as e:
            print(f"\n[!] Error receiving data: {e}")
            break
    
    # סגירה מסודרת במקרה של ניתוק
    try:
        client.close()
    except:
        pass
    sys.exit()

def main():
    global client, username
    
    print("--- WhatsApp Clone (CLI Version) ---")

    # --- שלב ההתחברות (Login Logic) ---
    # זהה ללוגיקה ב-GUI, רק עם print/input במקום חלונות קופצים
    while not username:
        input_user = input("Enter your username: ")
        
        if not input_user.strip():
            print("Username cannot be empty.")
            continue
            
        try:
            # יצירת סוקט וניסיון חיבור
            # הערה: חייבים ליצור סוקט חדש בכל ניסיון אם השרת סוגר חיבור בסירוב
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((SERVER_IP, PORT))
            
            client.send(input_user.encode()) # שליחת השם לבדיקה
            
            resp = client.recv(1024).decode() # קבלת תשובה מהשרת
            
            if resp == "APPROVE":
                username = input_user
                print(f"Successfully logged in as {username}!")
            else:
                print("Error: Username taken. Please try again.")
                client.close() # סגירת הסוקט כדי לנסות שוב נקי
                
        except Exception as e:
            print(f"Connection failed: {e}")
            return

    # --- הפעלת האזנה במקביל ---
    # מפעילים Thread שיקשיב להודעות נכנסות כדי שלא יתקע את ההקלדה
    # daemon=True אומר שה-Thread יסגר כשהתוכנה הראשית תיסגר
    threading.Thread(target=receive_messages, daemon=True).start()

    # --- לולאת שליחת הודעות (Main Loop) ---
    print("-" * 50)
    print(f"Hello, {username}") # בדיוק כמו הכותרת ב-GUI
    print("Instructions:")
    print("To send a message, use format: target|message")
    print("Example: user2|hello how are you?")
    print("Type 'exit' to quit.")
    print("-" * 50)

    while True:
        try:
            # קבלת קלט מהמשתמש
            msg = input("> ")
            
            if msg.lower() == 'exit':
                break
            
            # בדיקה בסיסית של הפורמט לפני שליחה
            if "|" in msg:
                # שליחה לשרת (בדיוק כמו ב-send_message ב-GUI)
                client.send(msg.encode())
            else:
                print("[!] Invalid format. Please use: target|message")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[!] Error sending message: {e}")
            break

    print("Goodbye!")
    if client:
        client.close()

if __name__ == "__main__":
    main()