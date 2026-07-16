# Assignment 7: Secure Network Application Development Using TCP

This repository contains the Assignment 7 implementation for the ISEA Phase 3 Cybersecurity Internship at Tezpur University. It extends the GUI-based multi-client TCP chat application from Assignment 6 by adding practical application-layer security mechanisms such as authentication, password hashing, duplicate login prevention, security logging, and packet-level verification using Wireshark.[file:81]

## Project Overview

The project is a Python-based client-server chat application built on TCP sockets with a Tkinter GUI client and a multithreaded server. Assignment 7 reuses the existing Assignment 6 architecture and enhances it with security-focused improvements while keeping the networking logic independent from the GUI.[file:81]

The application was tested in a Mininet topology with one server and four clients. Wireshark was used to verify successful login, failed login, duplicate login rejection, and the TCP connection handshake on port 5000.[file:81]

## Features

### Existing features from Assignment 6

- GUI login window
- Chat window with scrollable message area
- Multi-client TCP server
- Broadcast messaging
- Private messaging
- Online user list
- Background receive thread
- Queue-based GUI updates
- Thread-safe networking
- Connection logging

### Security features added in Assignment 7

- Username/password authentication
- SHA-256 password hashing
- `users.json` credential database
- JSON-based login protocol
- Server-side authentication
- Duplicate login prevention
- Security logging in `security_log.txt`
- Wireshark verification of authentication traffic

## Security Features

The security design focuses on practical application security rather than advanced cryptography, as required by the assignment.[file:81]

### 1. User Authentication

Each client must provide a valid username and password before being allowed to enter the chat. Authentication is performed on the server side so the client cannot bypass access control logic.

### 2. Secure Password Storage

Passwords are not stored in plaintext. User credentials are stored in `users.json` using SHA-256 hashes generated with Python's `hashlib.sha256()` as required by the assignment brief.[file:81]

### 3. Duplicate Login Prevention

The server tracks active authenticated users in memory and rejects a second simultaneous login attempt for the same username. This prevents two sessions from using the same account at the same time.

### 4. Security Logging

Authentication-related events are recorded in `security_log.txt`. Verified events include:

- `LOGIN_SUCCESS`
- `LOGIN_FAILED`
- `DUPLICATE_LOGIN`
- `LOGOUT`

### 5. Wireshark Verification

Authentication and session traffic were verified using Wireshark with the display filter:

```bash
tcp.port == 5000
```

This confirmed the TCP handshake and the application-layer login request/response workflow.

## Technologies Used

- Python 3.14.4
- Tkinter
- TCP socket programming
- Mininet
- Wireshark
- SHA-256 hashing
- JSON for credential storage
- Linux (Ubuntu aarch64)

## Mininet Topology

The application was tested using the following Mininet topology:[file:81]

| Host | Role     | IP Address | Username |
| ---- | -------- | ---------- | -------- |
| h1   | Server   | 10.0.0.1   | --       |
| h2   | Client A | 10.0.0.2   | Amit     |
| h3   | Client B | 10.0.0.3   | Priya    |
| h4   | Client C | 10.0.0.4   | Rahul    |
| h5   | Client D | 10.0.0.5   | Sneha    |

Server port: `5000`

## JSON Login Protocol

The login process uses a structured JSON protocol instead of the raw username string used in Assignment 6.

### Successful login request

```json
{ "action": "login", "username": "amit", "password": "amit123" }
```

### Successful login response

```json
{ "status": "success", "message": "Login successful" }
```

### Invalid credentials response

```json
{ "status": "error", "reason": "invalid_credentials" }
```

### Duplicate login response

```json
{ "status": "error", "reason": "duplicate_login" }
```

## Wireshark Verification

Wireshark analysis confirmed the following traffic on TCP port 5000:[file:81]

- TCP three-way handshake
- Login request from client to server
- Login success response
- Failed login response
- Duplicate login rejection response

An important observation from the verification is that passwords are stored as SHA-256 hashes in `users.json`, but login packets are still visible in plaintext on the wire because TLS was intentionally not implemented in this assignment.[file:81]

## Screenshots

The `screenshots/` directory contains the evidence collected during testing and verification.

| Figure   | Description                                          | File                                               |
| -------- | ---------------------------------------------------- | -------------------------------------------------- |
| Figure 1 | Successful User Authentication                       | `screenshots/fig_1_successful_authentication.png`  |
| Figure 2 | Authentication Failure Due to Invalid Credentials    | `screenshots/fig_2_invalid_credentials.png`        |
| Figure 3 | Duplicate Login Prevention Mechanism                 | `screenshots/fig_3_duplicate_login_prevention.png` |
| Figure 4 | TCP Three-Way Handshake During Client Connection     | `screenshots/fig_4_tcp_three_way_handshake.png`    |
| Figure 5 | Wireshark Capture of Successful Login Authentication | `screenshots/fig_5_successful_login_wireshark.png` |
| Figure 6 | Wireshark Capture of Failed Login Authentication     | `screenshots/fig_6_failed_login_wireshark.png`     |
| Figure 7 | Wireshark Capture of Duplicate Login Rejection       | `screenshots/fig_7_duplicate_login_wireshark.png`  |

## Project Structure

```text
EEB24023_JITUPAN_MONDAL_ASSIGNMENT7/
├── screenshots/
│   ├── fig_1_successful_authentication.png
│   ├── fig_2_invalid_credentials.png
│   ├── fig_3_duplicate_login_prevention.png
│   ├── fig_4_tcp_three_way_handshake.png
│   ├── fig_5_successful_login_wireshark.png
│   ├── fig_6_failed_login_wireshark.png
│   └── fig_7_duplicate_login_wireshark.png
├── client_gui.py
├── server.py
├── users.json
├── security_log.txt
├── server_log.txt
├── capture_auth.pcap
├── chat_history.csv
├── report.pdf
├── reflection.md
└── README.md
```

## How to Run

### 1. Start Mininet

```bash
sudo mn --topo single,5
```

### 2. Verify connectivity

```bash
nodes
net
pingall
```

### 3. Start the server on h1

```bash
h1 python3 server.py &
```

### 4. Start clients

Run the GUI client on the client hosts or through X11-enabled terminals as configured in your environment.

```bash
h2 python3 client_gui.py
h3 python3 client_gui.py
h4 python3 client_gui.py
h5 python3 client_gui.py
```

### 5. Test authentication

Use the usernames stored in `users.json` and verify:

- successful login
- invalid credential rejection
- duplicate login rejection

### 6. Capture traffic for verification

```bash
tcpdump -i h1-eth0 -w capture_auth.pcap tcp port 5000
```

Open the capture in Wireshark and apply:

```bash
tcp.port == 5000
```

## Future Improvements

The assignment focused on practical application-layer security, so several improvements remain possible for future versions:

- Add TLS/SSL to encrypt login credentials in transit
- Add salted password hashing for stronger credential protection
- Add failed login blocking and temporary account lockout
- Add input validation for usernames, commands, and oversized messages
- Add session timeout and inactivity handling
- Add role-based authorization if different permission levels are needed

## Author Information

**Jitupan Mondal**  
Roll No: EEB24023  
B.Tech Electrical Engineering, Tezpur University  
ISEA Phase 3 Cybersecurity Internship

## Repository Notes

This repository is an academic internship submission for Assignment 7. It reuses the Assignment 6 GUI-based chat application and extends it with security-focused enhancements required by the assignment brief.
