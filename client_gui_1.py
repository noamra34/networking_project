import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime

# --- הגדרות עיצוב (WhatsApp Dark Mode Style) ---
COLORS = {
    "bg": "#111b21",           # רקע כללי כהה
    "sidebar": "#202c33",      # צבע צד (רשימת משתמשים)
    "my_bubble": "#005c4b",    # צבע הודעה שלי (ירוק כהה)
    "other_bubble": "#37404a", # צבע הודעה של אחר (אפור)
    "text": "#e9edef",         # צבע טקסט ראשי
    "time": "#8696a0",         # צבע טקסט שעה
    "input_bg": "#2a3942",     # רקע תיבת כתיבה
    "list_select": "#2a3942",  # בחירה ברשימה
    "btn": "#00a884"           # כפתור שליחה ירוק
}

SERVER_IP = "127.0.0.1"
PORT = 5566

# --- משתנים גלובליים ---
client = None
username = ""
current_chat_partner = None

# מבנה הנתונים להיסטוריה:
# { "user1": [ {"sender": "me", "msg": "hi", "time": "10:00"}, ... ], "user2": ... }
conversations = {} 

root = tk.Tk()
root.withdraw() # החבאה עד להתחברות

# --- פונקציות עזר לציור בועות ---
def create_rounded_rect(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """פונקציה שמציירת מלבן עם פינות עגולות בקנבס"""
    points = [x1+radius, y1,
              x1+radius, y1,
              x2-radius, y1,
              x2-radius, y1,
              x2, y1,
              x2, y1+radius,
              x2, y1+radius,
              x2, y2-radius,
              x2, y2-radius,
              x2, y2,
              x2-radius, y2,
              x2-radius, y2,
              x1+radius, y2,
              x1+radius, y2,
              x1, y2,
              x1, y2-radius,
              x1, y2-radius,
              x1, y1+radius,
              x1, y1+radius,
              x1, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

# --- לוגיקת התחברות ---
while not username:
    input_user = simpledialog.askstring("Login", "Enter your username:")
    
    if input_user is None: # לחצו ביטול
        exit()
        
    if not input_user.strip():
        messagebox.showerror("Error", "Username cannot be empty")
        continue
        
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, PORT))
        client.send(input_user.encode())
        
        resp = client.recv(1024).decode()
        if resp == "APPROVE":
            username = input_user
        else:
            messagebox.showerror("Error", "Username taken.")
            client.close()
    except Exception as e:
        messagebox.showerror("Error", f"Connection failed: {e}")
        exit()

# --- הגדרת החלון הראשי ---
root.deiconify()
root.title(f"WhatsApp Clone | {username}")
root.geometry("900x600")
root.configure(bg=COLORS["bg"])

# --- חלוקה למסגרות ---
main_container = tk.Frame(root, bg=COLORS["bg"])
main_container.pack(fill=tk.BOTH, expand=True)

# סרגל צד (רשימת משתמשים)
sidebar = tk.Frame(main_container, bg=COLORS["sidebar"], width=250)
sidebar.pack(side=tk.LEFT, fill=tk.Y)
sidebar.pack_propagate(False) # שומר על רוחב קבוע

tk.Label(sidebar, text="Contacts", bg=COLORS["sidebar"], fg=COLORS["text"], font=("Helvetica", 14, "bold")).pack(pady=10)

users_listbox = tk.Listbox(sidebar, bg=COLORS["sidebar"], fg=COLORS["text"], 
                           selectbackground=COLORS["list_select"], borderwidth=0, font=("Helvetica", 12))
users_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# אזור הצ'אט (ימין)
chat_area = tk.Frame(main_container, bg=COLORS["bg"])
chat_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# כותרת הצ'אט
header_lbl = tk.Label(chat_area, text="Select a contact", bg=COLORS["list_select"], fg=COLORS["text"], font=("Helvetica", 12, "bold"), pady=10)
header_lbl.pack(fill=tk.X)

# קנבס להודעות (כדי לאפשר בועות וגלילה)
chat_canvas = tk.Canvas(chat_area, bg=COLORS["bg"], highlightthickness=0)
chat_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# מסגרת תחתונה להקלדה
input_frame = tk.Frame(chat_area, bg=COLORS["sidebar"], pady=10)
input_frame.pack(fill=tk.X, side=tk.BOTTOM)

msg_entry = tk.Entry(input_frame, bg=COLORS["input_bg"], fg="white", font=("Helvetica", 12), borderwidth=0, insertbackground="white")
msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15, ipady=8)

# --- לוגיקת ניהול הודעות ---

def get_time():
    return datetime.now().strftime("%H:%M")

def refresh_chat_view():
    """מנקה את המסך ומצייר מחדש את השיחה עם המשתמש שנבחר"""
    chat_canvas.delete("all") # ניקוי
    
    if not current_chat_partner:
        header_lbl.config(text="Select a contact to start chatting")
        return

    header_lbl.config(text=f"Chat with {current_chat_partner}")
    
    # שליפת ההיסטוריה
    msgs = conversations.get(current_chat_partner, [])
    
    y_pos = 20
    
    for item in msgs:
        is_me = (item['sender'] == 'me')
        text = item['msg']
        timestamp = item['time']
        
        # חישוב גדלים ומיקומים
        # משתמשים בטקסט זמני כדי למדוד רוחב נדרש
        text_id = chat_canvas.create_text(0, 0, text=text, font=("Helvetica", 11), anchor="nw")
        bbox = chat_canvas.bbox(text_id)
        chat_canvas.delete(text_id)
        
        width = bbox[2] - bbox[0] + 30 # קצת ריווח
        height = bbox[3] - bbox[1] + 25
        
        # גבולות הבועה
        canvas_width = chat_canvas.winfo_width()
        
        if is_me:
            rect_color = COLORS["my_bubble"]
            x1 = canvas_width - width - 30
            x2 = canvas_width - 10
        else:
            rect_color = COLORS["other_bubble"]
            x1 = 10
            x2 = 10 + width

        y1 = y_pos
        y2 = y_pos + height
        
        # ציור הבועה
        create_rounded_rect(chat_canvas, x1, y1, x2, y2, radius=10, fill=rect_color, outline="")
        
        # ציור הטקסט
        chat_canvas.create_text(x1 + 10, y1 + 10, text=text, fill=COLORS["text"], font=("Helvetica", 11), anchor="nw")
        
        # ציור הזמן
        chat_canvas.create_text(x2 - 5, y2 - 5, text=timestamp, fill=COLORS["time"], font=("Helvetica", 8), anchor="se")
        
        y_pos += height + 10 # קידום המיקום להודעה הבאה

    # גלילה אוטומטית למטה
    chat_canvas.config(scrollregion=chat_canvas.bbox("all"))
    chat_canvas.yview_moveto(1)

def send_message(event=None):
    global current_chat_partner
    msg = msg_entry.get().strip()
    
    if not msg or not current_chat_partner:
        return

    # 1. שליחה לשרת
    try:
        full_msg = f"{current_chat_partner}|{msg}"
        client.send(full_msg.encode())
    except:
        messagebox.showerror("Error", "Connection lost")
        root.destroy()
        return

    # 2. שמירה בהיסטוריה המקומית
    if current_chat_partner not in conversations:
        conversations[current_chat_partner] = []
        
    conversations[current_chat_partner].append({
        "sender": "me",
        "msg": msg,
        "time": get_time()
    })
    
    # 3. עדכון מסך וניקוי שורה
    msg_entry.delete(0, tk.END)
    refresh_chat_view()

# כפתור שליחה (אייקון חץ או טקסט)
send_btn = tk.Button(input_frame, text="➤", command=send_message, bg=COLORS["bg"], fg=COLORS["btn"], 
                     font=("Helvetica", 16), borderwidth=0, activebackground=COLORS["bg"])
send_btn.pack(side=tk.RIGHT, padx=10)
msg_entry.bind("<Return>", send_message)

def on_user_select(event):
    global current_chat_partner
    selection = users_listbox.curselection()
    if selection:
        selected_user = users_listbox.get(selection[0])
        # מניעת בחירה בעצמך (למרות שזה לא אמור לקרות כי השרת לא ישלח אותך ברשימה, אבל ליתר ביטחון)
        if selected_user == username: 
            return
            
        current_chat_partner = selected_user
        refresh_chat_view()

users_listbox.bind("<<ListboxSelect>>", on_user_select)

# --- האזנה לשרת ---
def receive_messages():
    while True:
        try:
            data = client.recv(1024).decode()
            if not data: break
            
            # מקרה 1: עדכון רשימת משתמשים
            if data.startswith("LIST|"):
                users_str = data.split("|")[1]
                active_users = users_str.split(",")
                
                # עדכון ה-Listbox ב-Main Thread
                users_listbox.delete(0, tk.END)
                for user in active_users:
                    if user != username: # אל תציג את עצמי ברשימה
                        users_listbox.insert(tk.END, user)
                        # אם עדיין אין לנו היסטוריה איתו, ניצור רשימה ריקה
                        if user not in conversations:
                            conversations[user] = []
            
            # מקרה 2: הודעה רגילה
            elif data.startswith("MSG|"):
                _, sender, content = data.split("|", 2)
                
                # שמירה בהיסטוריה
                if sender not in conversations:
                    conversations[sender] = []
                
                conversations[sender].append({
                    "sender": "other",
                    "msg": content,
                    "time": get_time()
                })
                
                # אם אנחנו כרגע בצ'אט עם השולח, נרענן את המסך
                if current_chat_partner == sender:
                    refresh_chat_view() # קריאה ישירה כי אנחנו ב-Thread נפרד, ב-Tkinter לפעמים צריך after, אבל כאן זה יעבוד פשוט
                    
        except Exception as e:
            print("Error receiving:", e)
            break

threading.Thread(target=receive_messages, daemon=True).start()

def on_closing():
    try: client.close()
    except: pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()