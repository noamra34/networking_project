# PySocket Chat System

## Introduction
In this document, we present a chat system project based on TCP sockets, including its design, implementation, and analysis using Python.
The goal is to understand fundamental networking concepts, client–server communication, and the architecture of distributed systems. 
The project was developed by Noa Rachmani, Noa Zadok and Liran Shterenberg — Computer Science students.

---

## Features
- Implement two-way communication between clients and a central server using TCP.
- Enable the server to handle multiple clients concurrently.
- Allow clients to initiate a private chat with another client by specifying the target client's unique username.
- Capture and analyze the network traffic of the application using Wireshark.

---

## Technical Requirements

### **1. Communication**
- The system uses the **TCP protocol**.
- Full duplex communication between clients and the server.
- The server supports **at least 5 simultaneous client connections**.

### **2. System Structure**
#### **Server**
- Listens for incoming client connections.
- Manages a list of active clients and their unique usernames.
- Upon receiving a client request to communicate with another client, the server creates a chat session between the two.

#### **Client**
- Connects to the server using a unique username.
- Can send and receive messages in real time.
- Text-based interface (no GUI required).

### **3. Restrictions**
- The implementation must use **raw sockets only** — no frameworks like Spring or pre-built networking libraries.
- Threading or multiprocessing is used to support multiple clients.
- Example references used during development:
  - Basic TCP socket example  
    (https://pymotw.com/2/socket/tcp.html)
  - Multi-client Python socket server  
    (https://www.dunebook.com/creating-a-python-socket-server-with-multiple-clients)

### **4. Code Standards**
- Code is readable, documented, and logically organized across files/classes.
- Error handling is included — e.g., unexpected client disconnection.

---

## Project Structure
project/
├── server.py # Server implementation (TCP, multithreading)
├── client.py # Client implementation (username-based)
├── traffic_capture.pcap # Wireshark traffic capture file
├── analysis_report.pdf # Network traffic analysis up to Network Layer
└── README.md # Project documentation

---

## ▶️ How to Run the Application

### **1. Start the server**

### **2. Start one or more clients**

### **3. Enter a unique username**
Each client must identify itself with a unique name.

### **4. Open a chat**
Type the username of the target client you want to chat with.

### **5. Start sending messages**
The server routes messages privately between the two selected clients.

---

## 📡 Network Traffic Capture

### **1. Capturing the traffic**
- Wireshark was used to capture all TCP packets exchanged between the server and clients.
- The recorded traffic is saved in a `.pcap` file (`traffic_capture.pcap`).

### **2. Traffic Analysis**
The analysis includes:
- The TCP 3-way handshake
- Client–server message flows
- Port numbers and socket connections
- Segmentation and reassembly behavior
- Network layer analysis (IP headers, packet routing)
- Identification of chat session patterns in the TCP stream

The detailed analysis is included in `analysis_report.pdf`.

---

## 🚀 Future Improvements
- Adding encrypted communication (TLS)
- User authentication & password system
- Group chat support
- Graphical user interface (GUI)
- Offline message storage

---

## 👤 Authors
**Noa Rachmani, Noa Zadok and Liran Shterenberg**  
Computer Science Students
