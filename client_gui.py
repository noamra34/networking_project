import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime

DARK_BG = "#1e1e1e"        # רקע כללי כהה
SIDEBAR_BG = "#252526"     # רקע רשימת משתמשים
CHAT_BG = "#1e1e1e"        # רקע הצ'אט
TEXT_COLOR = "#dcdcdc"     # צבע טקסט רגיל
MY_MSG_COLOR = "#4EC9B0"   # צבע ההודעות שלי (טורקיז)
OTHER_MSG_COLOR = "#569CD6" # צבע ההודעות שלהם (כחול)
ENTRY_BG = "#3c3c3c"       # רקע תיבת כתיבה
BUTTON_COLOR = "#007acc"

server_ip = "127.0.0.1"
port = 5566

root = tk.Tk()
root.withdraw()
root.title("Chat App")
root.geometry("750x500")
root.configure(bg=DARK_BG)

username=""
client = None


while not username:
    msg_prompt = "Enter your username: \n (Allowd: user1, user2, user3, user4, user5)"
    input_user = simpledialog.askstring("Login", msg_prompt)
    
    if input_user is None:
        root.destroy()
        exit()

    if input_user.strip() == "":
        messagebox.showerror("Error", "Username cannot be empty")
        continue
        #username = input_user
    try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((server_ip, port))

            client.send(input_user.encode())

            response = client.recv(1024).decode()

            if response == "APPROVE":
                username = input_user
            else:
                messagebox.showerror("Login Error", f"Username '{input_user}' is already taken. \n Please choose another one.")
                client.close()

    except ConnectionRefusedError:
            messagebox.showerror("Connection Error", f"Could not connect to server.\n Make sure server.py is running.")
            exit()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        exit()

root.deiconify()
root.title(f"Chat App | Logged in as: {username}")

current_target = None

def get_time():
    return  datetime.now().strftime("%H:%M")

left_frame = tk.Frame(root, width=200, bg=SIDEBAR_BG)
left_frame.pack(side=tk.LEFT, fill=tk.Y)

tk.Label(left_frame, text="Add Contact", bg=SIDEBAR_BG, fg="#888888", font=("Segoe UI", 10, "bold")).pack(pady=15)

add_contact_frame = tk.Frame(left_frame, bg=SIDEBAR_BG)
add_contact_frame.pack(pady=5, padx=10, fill=tk.X)

# תיבת טקסט להוספת שם
new_contact_entry = tk.Entry(add_contact_frame, bg="#3c3c3c", fg="white", borderwidth=0)
new_contact_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)

# פונקציה להוספת השם לרשימה
def add_manual_contact():
    new_user = new_contact_entry.get().strip()
    if new_user:
        if new_user == username:
            messagebox.showinfo("Oops", "You cannot chat with yourself!")
            return
            
        # בדיקה אם השם כבר קיים ברשימה
        all_items = user_list.get(0, tk.END)
        if new_user in all_items:
            messagebox.showinfo("Info", "User already in list")
            return

        user_list.insert(tk.END, new_user)
        new_contact_entry.delete(0, tk.END)

# כפתור הפלוס (+)
add_btn = tk.Button(add_contact_frame, text="+", command=add_manual_contact, bg=BUTTON_COLOR, fg="white", width=3, relief=tk.FLAT)
add_btn.pack(side=tk.RIGHT)

tk.Label(left_frame, text="Contacts List", bg=SIDEBAR_BG, fg="#888888", font=("Segoe UI", 10, "bold")).pack(pady=(20, 5))

user_list = tk.Listbox(left_frame, bg=SIDEBAR_BG, fg="white", selectbackground="#37373d", selectforeground="white", borderwidth=0, highlightthickness=0, font=("Segoe UI", 11))
user_list.pack(fill=tk.BOTH, expand=True, padx=10)


def select_user(event):
    global current_target
    selection = user_list.curselection()
    if selection:
        current_target = user_list.get(selection[0])
user_list.bind("<<ListboxSelect>>", select_user)

right_frame = tk.Frame(root, bg="#ffffff")
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

header_label = tk.Label(right_frame, text="Select a contact to start chatting", bg=CHAT_BG, font=("Segoe UI", 14))
header_label.pack(pady=10)

bottom_frame = tk.Frame(right_frame, bg=CHAT_BG)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=15, padx=15)

send_button = tk.Button(bottom_frame, text="Send", command=lambda: send_message, bg=BUTTON_COLOR, fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, activebackground="#005a9e", activeforeground="white", width=10)
send_button.pack(side=tk.RIGHT)

msg_entry = tk.Entry(bottom_frame, bg=ENTRY_BG, fg="white", insertbackground="white", font=("Segue UI", 12), borderwidth=0, relief=tk.FLAT)
msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0,10))
msg_entry.bind("<Return>", lambda event:send_message())

chat_box = tk.Text(right_frame, state=tk.DISABLED, wrap=tk.WORD, bg=CHAT_BG, fg=TEXT_COLOR, font=("Segoe UI", 11), borderwidth=0, highlightthickness=0, padx=10, pady=10)
chat_box.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

chat_box.tag_config('me', foreground=MY_MSG_COLOR)
chat_box.tag_config('other', foreground=OTHER_MSG_COLOR)
chat_box.tag_config('time', foreground="#888888", font=("Segoe UI", 8))

def send_message():
        if not current_target:
            messagebox.showinfo("Info", "Please select a user to chat with first.")
            return
        
        message = msg_entry.get()
        if not message:
            return
        
        full_message = f"{current_target}|{message}"
        try:
            client.send(full_message.encode())
            chat_box.config(state= tk.NORMAL)
            chat_box.insert(tk.END, f"You -> {current_target}: {message}\n", "me")
            chat_box.config(state=tk.DISABLED)
            msg_entry.delete(0,tk.END)
        except:
            messagebox.showerror("Error", "Connection lost")
            root.destroy()

def receive_message():
    while True:
        try:
            msg = client.recv(1024).decode()
            if not msg: break

            chat_box.config(state=tk.NORMAL)
            chat_box.insert(tk.END, msg + "\n", "other")
            chat_box.config(state=tk.DISABLED)

            chat_box.see(tk.END)
        except:
            break

threading.Thread(target=receive_message, daemon=True).start()

def on_closing():
    try:
        if client:
            client.close()
    except:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
    

