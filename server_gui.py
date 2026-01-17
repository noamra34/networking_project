import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

# --- הגדרות עיצוב (ערכת צבעים) ---
# ריכוז כל הצבעים במקום אחד מאפשר לשנות את עיצוב האפליקציה בקלות
COLORS = {
    "bg": "#111b21",           # רקע ראשי (כהה מאוד - סגנון WhatsApp)
    "sidebar": "#202c33",      # רקע משני (אזור הלוגים)
    "text": "#e9edef",         # צבע טקסט בהיר לקריאות
    "btn_start": "#00a884",    # ירוק - כפתור הפעלה
    "btn_stop": "#f15c6d",     # אדום - כפתור עצירה
    "success": "#00a884",      # צבע ירוק להודעות הצלחה בלוג
    "error": "#f15c6d",        # צבע אדום לשגיאות בלוג
    "warning": "#eebc23"       # צבע צהוב לאזהרות
}

# --- משתנים גלובליים לניהול השרת ---
# clients: מילון שממפה בין שם המשתמש (מפתח) לסוקט החיבור שלו (ערך)
clients = {} 

# lock: מנעול שמונע "התנגשויות" (Race Conditions).
# מכיוון שיש הרבה משתמשים (Threads) שרצים במקביל, המנעול מבטיח שרק אחד מהם
# יוכל לשנות את רשימת המחוברים ברגע נתון.
lock = threading.Lock()

server_socket = None  # המשתנה שיחזיק את החיבור הראשי של השרת
is_running = False    # דגל בוליאני: האם השרת אמור לעבוד כרגע?

# --- פונקציות לוגיקה של השרת ---

def log(message, tag=None):
    """
    פונקציה שכותבת הודעות לחלון הלוג בממשק הגרפי.
    מקבלת: את הטקסט (message) ותג צבע אופציונלי (tag).
    """
    try:
        log_area.config(state=tk.NORMAL)          # פתיחת הלוג לכתיבה (הוא נעול בדרך כלל)
        log_area.insert(tk.END, message + "\n", tag) # הוספת השורה החדשה
        log_area.see(tk.END)                      # גלילה אוטומטית למטה להודעה החדשה
        log_area.config(state=tk.DISABLED)        # נעילת הלוג חזרה (שהמשתמש לא ימחק טקסט)
    except:
        pass # מונע קריסה אם מנסים לכתוב כשהחלון כבר סגור

def broadcast_user_list():
    """
    שולח לכל המשתמשים את הרשימה המעודכנת של מי שמחובר כרגע.
    נקראת בכל פעם שמישהו מתחבר או מתנתק.
    """
    with lock: # נעילת הרשימה לקריאה בטוחה
        # יצירת מחרוזת שמות מופרדים בפסיקים (למשל: "Moshe,David,Sarah")
        user_list = ",".join(clients.keys())
        message = f"LIST|{user_list}" # הודעת הפרוטוקול
        
        # שליחה לכל הלקוחות הקיימים
        for sock in clients.values():
            try:
                sock.send(message.encode())
            except:
                pass # נתעלם משגיאות שליחה (יטופלו בנפרד)

def handle_client(client_socket, addr):
    """
    הפונקציה הראשית שמטפלת בלקוח בודד.
    פונקציה זו רצה ב-Thread נפרד עבור כל משתמש.
    """
    username = ""
    try:
        # --- שלב 1: התחברות (Handshake) ---
        # ההודעה הראשונה שהלקוח שולח היא תמיד שם המשתמש
        username = client_socket.recv(1024).decode()
        
        with lock:
            # בדיקה האם השם כבר תפוס
            if username in clients:
                client_socket.send("REFUSED".encode()) # סירוב
                client_socket.close()                  # ניתוק מיידי
                return
            else:
                client_socket.send("APPROVE".encode()) # אישור
                clients[username] = client_socket      # שמירה במילון
        
        # דיווח ללוג ועדכון שאר המשתמשים
        log(f"[+] User connected: {username}", "success")
        broadcast_user_list()

        # --- שלב 2: לולאת השיחה ---
        while True:
            # המתנה להודעה מהלקוח (פעולה חוסמת)
            data = client_socket.recv(1024)
            if not data: break # אם התקבל מידע ריק - הלקוח התנתק

            message = data.decode()
            
            # בדיקת תקינות הפרוטוקול: "Target|Message"
            if "|" in message:
                target_user, msg_content = message.split("|", 1)
                
                # שליחת ההודעה ליעד דרך השרת
                with lock:
                    if target_user in clients:
                        # הפורמט שנשלח למקבל: MSG|השולח|התוכן
                        clients[target_user].send(f"MSG|{username}|{msg_content}".encode())

    except:
        pass # טיפול בניתוקים פתאומיים
    
    finally:
        # --- שלב 3: ניתוק וניקוי ---
        # בלוק זה ירוץ תמיד בסוף, גם אם הייתה שגיאה
        with lock:
            if username in clients:
                del clients[username] # מחיקה מהרשימה
        
        try: client_socket.close()
        except: pass
        
        # נרשום לוג רק אם השרת פעיל (כדי למנוע הצפת הודעות בעצירה)
        if username and is_running: 
            log(f"[-] User disconnected: {username}", "error")
            broadcast_user_list()

def start_server_logic():
    """
    הלולאה הראשית של השרת שמקבלת חיבורים חדשים.
    רצה ב-Thread נפרד כדי לא לתקוע את ה-GUI.
    """
    global server_socket, is_running
    server_ip = "0.0.0.0" # האזנה לכל כרטיסי הרשת
    port = 5566
    
    try:
        # יצירת סוקט מסוג TCP
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((server_ip, port))
        server_socket.listen(5) # מקסימום 5 ממתינים בתור
        
        log(f"Server started on port {port}", "success")
        status_lbl.config(text="Status: RUNNING", fg=COLORS["success"])
        
        while is_running:
            try:
                # קבלת חיבור חדש (הקוד עוצר כאן ומחכה ללקוח)
                client_socket, addr = server_socket.accept()
                
                if not is_running: break
                
                # יצירת Thread חדש לטיפול בלקוח הספציפי הזה
                threading.Thread(target=handle_client, args=(client_socket, addr)).start()
            except OSError:
                break # קורה כשהשרת נסגר ידנית

    except Exception as e:
        if is_running: 
            log(f"Error: {e}", "error")
            stop_server()

def on_start_click():
    """מה קורה כשלוחצים על כפתור Start"""
    global is_running
    if not is_running:
        is_running = True
        
        # עדכון ויזואלי של הכפתורים
        start_btn.config(state=tk.DISABLED, bg=COLORS["sidebar"])
        stop_btn.config(state=tk.NORMAL, bg=COLORS["btn_stop"])
        
        # הפעלת השרת ברקע (daemon=True אומר שייסגר אם נסגור את החלון)
        threading.Thread(target=start_server_logic, daemon=True).start()

def stop_server():
    """
    פונקציה לעצירת חירום של השרת וניתוק כל המשתמשים.
    """
    global is_running, server_socket
    
    if not is_running: return

    is_running = False
    log("Stopping server...", "warning")
    status_lbl.config(text="Status: STOPPED - Restart required to use app", fg=COLORS["error"])

    # 1. ניתוק יזום של כל הלקוחות המחוברים
    # זה יגרום לצד הלקוח לקבל שגיאה ולהסגר/להתנתק
    with lock:
        for user, sock in clients.items():
            try:
                sock.close() # סגירת החיבור בכוח
            except:
                pass
        clients.clear() # איפוס הרשימה
    
    # 2. סגירת הסוקט הראשי של השרת
    # זה יגרום לשגיאה ב-start_server_logic ויוציא אותו מהלולאה
    if server_socket:
        try:
            server_socket.close()
        except:
            pass

    log("Server stopped. All clients disconnected.", "error")
    
    # איפוס הכפתורים למצב ההתחלתי
    start_btn.config(state=tk.NORMAL, bg=COLORS["btn_start"])
    stop_btn.config(state=tk.DISABLED, bg=COLORS["sidebar"])

# --- בניית הממשק הגרפי (GUI) ---
root = tk.Tk()
root.title("WhatsApp Server Control")
root.geometry("500x400")
root.configure(bg=COLORS["bg"])

# כותרת ראשית
tk.Label(root, text="Server Control Panel", bg=COLORS["bg"], fg=COLORS["text"], font=("Helvetica", 16, "bold")).pack(pady=15)

# מסגרת לכפתורים
btn_frame = tk.Frame(root, bg=COLORS["bg"])
btn_frame.pack(pady=5)

# כפתור הפעלה
start_btn = tk.Button(btn_frame, text="Start Server", command=on_start_click, 
                      bg=COLORS["btn_start"], fg="white", font=("Helvetica", 12, "bold"), 
                      borderwidth=0, padx=20, pady=10)
start_btn.pack(side=tk.LEFT, padx=10)

# כפתור עצירה (מתחיל במצב לא פעיל)
stop_btn = tk.Button(btn_frame, text="Stop Server", command=stop_server, 
                     bg=COLORS["sidebar"], fg="white", font=("Helvetica", 12, "bold"), 
                     borderwidth=0, padx=20, pady=10, state=tk.DISABLED)
stop_btn.pack(side=tk.LEFT, padx=10)

# תווית סטטוס
status_lbl = tk.Label(root, text="Status: STOPPED", bg=COLORS["bg"], fg=COLORS["text"], font=("Helvetica", 10))
status_lbl.pack(pady=10)

# אזור הלוגים (טקסט נגלל)
log_frame = tk.Frame(root, bg=COLORS["sidebar"], padx=2, pady=2)
log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

log_area = scrolledtext.ScrolledText(log_frame, bg=COLORS["sidebar"], fg=COLORS["text"], font=("Consolas", 9), height=10)
log_area.pack(fill=tk.BOTH, expand=True)

# הגדרת צבעים להודעות בלוג
log_area.tag_config("success", foreground=COLORS["success"])
log_area.tag_config("error", foreground=COLORS["error"])
log_area.tag_config("warning", foreground=COLORS["warning"])

# טיפול בסגירת החלון (X)
def on_window_close():
    stop_server()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_window_close)
root.mainloop()