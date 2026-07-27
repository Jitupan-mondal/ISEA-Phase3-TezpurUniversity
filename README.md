# ISEA Phase III Networking Internship 2026

## Secure GUI-Based Multi-Client TCP Chat Application

> This repository contains the complete coursework and final project developed during the ISEA Phase III Networking Internship. The final project integrates networking, GUI development, authentication, reliability, scalability, and performance evaluation into a secure multi-client TCP chat application.

This repository documents the complete ISEA Phase III Networking Internship, progressing from foundational socket programming assignments to a final secure, GUI-based, multi-client TCP chat application. It contains all internship assignments (1–8) along with the final consolidated project and lecture slides.

## Table of Contents

- [About the Internship](#about-the-internship)
- [Technical Stack](#technical-stack)
- [Repository Structure](#repository-structure)
- [Internship Progress](#internship-progress)
- [Final Project: Secure GUI-Based Multi-Client TCP Chat Application](#final-project-secure-gui-based-multi-client-tcp-chat-application)
  - [Overview](#overview)
  - [Project Highlights](#project-highlights)
  - [Objectives](#objectives)
  - [Features](#features)
  - [Architecture](#architecture)
  - [Final Project Structure](#final-project-structure)
  - [Technologies Used](#technologies-used)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Server](#running-the-server)
  - [Running the Client](#running-the-client)
  - [Testing using Mininet](#testing-using-mininet)
  - [Security Features](#security-features)
  - [Reliability Features](#reliability-features)
  - [Scalability Features](#scalability-features)
- [Experimental Results](#experimental-results)
- [Screenshots](#screenshots)
- [Future Improvements](#future-improvements)
- [Learning Outcomes](#learning-outcomes)
- [License](#license)
- [Author](#author)

## About the Internship

The ISEA Phase III Networking Internship focuses on practical networking and cybersecurity skills, including socket programming, packet-level analysis, secure application design, and network performance evaluation using Mininet and Wireshark. Each assignment builds incrementally toward the final project: a secure, reliable, and scalable multi-client chat system.

## Technical Stack

| Component           | Technology                            |
| ------------------- | ------------------------------------- |
| **Language**        | Python 3                              |
| **GUI**             | Tkinter                               |
| **Networking**      | TCP Sockets                           |
| **Authentication**  | SHA-256                               |
| **Configuration**   | JSON                                  |
| **Testing**         | Mininet                               |
| **Packet Analysis** | Wireshark                             |
| **Concurrency**     | Thread-per-client (Semaphore-bounded) |
| **Performance**     | CSV + Matplotlib                      |

## Repository Structure

```text
ISEA-Phase3-TezpurUniversity/
│
├── README.md
├── LICENSE
├── Lectures_PDFs/
├── Assignment_PDFs/
├── screenshots/
├── graphs/
├── EEB24023_JITUPAN-MONDAL_UDP_ASSIGNMENT/
├── EEB24023_JITUPAN-MONDAL_TCP_ASSIGNMENT/
├── EEB24023_JITUPAN-MONDAL_RAWSOCKET_ASSIGNMENT/
├── EEB24023_JITUPAN-MONDAL_CHATSERVER_ASSIGNMENT/
├── EEB24023_JITUPAN-MONDAL_ASSIGNMENT5/
├── EEB24023_JITUPAN-MONDAL_ASSIGNMENT6/
├── EEB24023_JITUPAN-MONDAL_ASSIGNMENT7/
└── EEB24023_JITUPAN-MONDAL_ASSIGNMENT8/   ← Final Project (see below)
```

The final project — the secure GUI-based multi-client TCP chat application — resides in `EEB24023_JITUPAN-MONDAL_ASSIGNMENT8`, and represents the culmination of all prior assignments.

## Internship Progress

| Assignment    | Topic                                              | Status |
| ------------- | -------------------------------------------------- | ------ |
| Assignment 1  | Reliable UDP using Mininet                         | ✅     |
| Assignment 2  | TCP Performance & Wireshark                        | ✅     |
| Assignment 3  | Raw Socket Packet Analysis                         | ✅     |
| Assignment 4  | Multi-Client TCP Chat Server                       | ✅     |
| Assignment 5  | Advanced Multi-Client Chat Server                  | ✅     |
| Assignment 6  | GUI-Based Chat Application                         | ✅     |
| Assignment 7  | Secure Network Application                         | ✅     |
| Assignment 8  | Scalability & Reliability                          | ✅     |
| Final Project | Secure GUI-Based Multi-Client TCP Chat Application | ✅     |

## Final Project: Secure GUI-Based Multi-Client TCP Chat Application

### Overview

The final project implements a secure, multithreaded, GUI-based chat application over TCP. It supports authenticated multi-client communication, real-time broadcast and private messaging, and includes practical reliability, scalability, and security engineering. Development progressed incrementally: a functional multi-client chat system, followed by authentication and secure credential storage, followed by reliability, scalability, and performance instrumentation.

### Project Highlights

- Secure multi-client TCP chat application
- Tkinter-based graphical user interface
- SHA-256 user authentication
- Duplicate login prevention
- Automatic client reconnection
- Heartbeat-based dead client detection
- Graceful server shutdown
- Semaphore-bounded concurrency
- Runtime configuration through JSON
- Performance monitoring with CSV logging
- Tested using Mininet and Wireshark

### Objectives

- Implement a multithreaded TCP server and Tkinter-based GUI client supporting broadcast and private messaging.
- Authenticate users with hashed credentials and prevent duplicate logins.
- Validate all client input and block brute-force login attempts.
- Ensure resilience to disconnections through heartbeat detection, graceful shutdown, and automatic reconnection.
- Support multiple concurrent clients through a semaphore-bounded thread-per-client design.
- Measure real performance metrics (latency, throughput, CPU, memory) under increasing client load.

### Features

- User authentication with SHA-256 hashed password verification.
- Duplicate login prevention (one active session per username).
- Broadcast messaging to all connected clients.
- Private messaging between two specific users.
- Real-time online users list.
- Graphical user interface built using Tkinter.
- Secure event logging without storing plaintext passwords.
- Heartbeat-based dead client detection and cleanup.
- Graceful server shutdown with client notification.
- Automatic client reconnection with exponential backoff.
- Semaphore-bounded concurrency control for scalability.
- Runtime configuration via `config.json`.
- Continuous performance monitoring and CSV logging.

### Architecture

The application follows a three-layer separation between the network layer, the GUI layer, and the server layer:

- **NetworkClient** — handles all socket communication, JSON-based login handshake, background receive/heartbeat threads, and automatic reconnection logic, independent of the GUI.
- **LoginWindow / ChatWindow** — Tkinter GUI components that only render data placed into a thread-safe queue by the network layer.
- **server.py** — a multithreaded TCP server using one daemon thread per client connection, guarded by a connection semaphore, with dedicated background threads for the stale-connection reaper and the performance monitor.

All shared server-side state (`clients`, `logged_in_users`, `stats`) is protected using `threading.Lock` objects to prevent race conditions across concurrent client threads.

The system architecture separates networking, presentation, and server logic into independent components. The GUI communicates only through the NetworkClient layer, while the server manages authentication, message routing, heartbeat monitoring, logging, scalability control, and performance monitoring.

### Final Project Structure

```text
EEB24023_JITUPAN-MONDAL_ASSIGNMENT8/
├── graphs/
│   ├── cpu_vs_clients.png
│   ├── latency_vs_clients.png
│   ├── memory_vs_clients.png
│   └── throughput_vs_clients.png
├── screenshots/
│   └── (fig_1_... to fig_18_...)
├── README.md
├── capture_auth.pcap
├── chat_history.csv
├── client_gui.py
├── config.json
├── performance_results.csv
├── security_log.txt
├── server_log.txt
├── server.py
├── users.json
├── report.pdf
└── handwritten_reflection.pdf
```

### Technologies Used

- Python 3
- Socket programming (`socket`, `threading`)
- Tkinter (GUI)
- JSON-based application protocol
- SHA-256 password hashing (`hashlib`)
- Mininet (network emulation)
- Wireshark (packet verification)
- Matplotlib (graph generation)
- CSV-based performance logging

### Installation

```bash
git clone https://github.com/Jitupan-mondal/ISEA-Phase3-TezpurUniversity.git
cd ISEA-Phase3-TezpurUniversity/EEB24023_JITUPAN-MONDAL_ASSIGNMENT8
```

No external Python packages are required for core functionality. If `psutil` is available, the performance monitor uses it for more accurate CPU/memory readings; otherwise it falls back to OS-level metrics automatically.

### Configuration

All runtime parameters are externalized into `config.json`, removing hardcoded values from both server and client. Server parameters include host, port, heartbeat timeout, reaper interval, maximum failed login attempts, lockout duration, maximum message length, and maximum concurrent clients. Client parameters include server address, heartbeat interval, and reconnection attempts/backoff settings. Both `server.py` and `client_gui.py` load `config.json` at startup and fall back to safe defaults if the file is missing.

### Running the Server

```bash
python3 server.py
```

### Running the Client

```bash
python3 client_gui.py
```

### Testing using Mininet

```bash
sudo mn --topo single,11
mininet> h1 python3 server.py
mininet> h2 python3 client_gui.py &
mininet> h3 python3 client_gui.py &
mininet> h4 python3 client_gui.py &
```

Test scenarios: graceful shutdown with client notification, stale client cleanup via the reaper thread, automatic reconnection after server restart, server-busy rejection under a lowered concurrency limit, and scalability runs at 5, 8, and 10 concurrent clients.

### Security Features

- JSON-based login authentication protocol.
- SHA-256 password hashing; plaintext passwords are never stored.
- Duplicate login prevention (one active session per username).
- Input validation: username format, message length limits, and unsupported command rejection.
- Temporary account lockout after five consecutive failed login attempts.
- Secure event logging (`security_log.txt`) that never records plaintext passwords.

### Reliability Features

- Heartbeat mechanism for live client detection.
- Background reaper thread that detects and closes stale/dead connections.
- Graceful shutdown via SIGINT/SIGTERM handling, notifying all connected clients before closing sockets.
- Automatic client reconnection with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 30s).

### Scalability Features

- Semaphore-bounded concurrent client limit, preserving the thread-per-client design.
- Clear "server busy" response for connections beyond the configured limit.
- Thread-safe shared state using `threading.Lock` across all client-handler threads.

## Experimental Results

Performance evaluation was conducted using Mininet with increasing client loads. Latency, throughput, CPU utilization, and memory usage were recorded automatically by the performance monitor.

| Clients | Latency (ms) | Throughput (msg/s) | CPU (%) | Memory (MB) |
| ------- | ------------ | ------------------ | ------- | ----------- |
| 1       | 0.010        | 0.016              | 0.04    | 25.24       |
| 5       | 0.032        | 0.077              | 0.04    | 32.13       |
| 8       | 0.022        | 0.064              | 0.04    | 35.06       |
| 10      | 0.032        | 0.086              | 0.05    | 44.80       |

Latency remained under 0.05 ms and CPU usage stayed below 0.1% throughout all test runs, while memory usage scaled predictably with client count.

### Latency

![Latency](graphs/fig_g01_latency_vs_clients.png)

### Throughput

![Throughput](graphs/fig_g02_throughput_vs_clients.png)

### CPU Usage

![CPU](graphs/fig_g03_cpu_usage_vs_clients.png)

### Memory Usage

![Memory](graphs/fig_g04_memory_usage_vs_clients.png)

## Screenshots

### System Architecture

![System Architecture](screenshots/fig_01_system_architecture.png)

### Server Startup

![Server Startup](screenshots/fig_02_server_startup.png)

### Graceful Shutdown

![Graceful Shutdown](screenshots/fig_03_graceful_shutdown.png)

### Reaper Cleanup

![Reaper Cleanup](screenshots/fig_04_reaper_cleanup.png)

### Client Reconnection

![Client Reconnection](screenshots/fig_05_client_reconnection.png)

### Login Lockout

![Login Lockout](screenshots/fig_06_login_lockout.png)

### Input Validation

![Input Validation](screenshots/fig_07_input_validation.png)

### Scalability (10 Clients)

![Scalability 10 Clients](screenshots/fig_08_scalability_10_clients.png)

### Server Busy

![Server Busy](screenshots/fig_09_server_busy.png)

### TCP Handshake

![TCP Handshake](screenshots/fig_10_tcp_handshake.png)

### JSON Login Payload

![JSON Login Payload](screenshots/fig_11_json_login_payload.png)

### Login Success Response

![Login Success Response](screenshots/fig_12_login_success_response.png)

### Heartbeat Packets

![Heartbeat Packets](screenshots/fig_13_heartbeat_packets.png)

### TCP Teardown

![TCP Teardown](screenshots/fig_14_tcp_teardown.png)

### GUI Login Window

![GUI Login Window](screenshots/fig_15_gui_login_window.png)

### Chat Features

![Chat Features](screenshots/fig_16_chat_features.png)

### Duplicate Login

![Duplicate Login](screenshots/fig_17_duplicate_login.png)

## Future Improvements

- Integrate TLS/SSL to encrypt client-server communication, since credentials and messages currently travel in plaintext at the application layer.
- Replace plain SHA-256 hashing with salted password hashing using a modern password hashing algorithm (e.g., bcrypt or Argon2).
- Transition from a thread-per-client model to asynchronous I/O or a worker-pool architecture to support significantly larger numbers of concurrent users with lower resource overhead.

## Learning Outcomes

- TCP Socket Programming
- Concurrent Network Programming
- GUI Development with Tkinter
- Client-Server Software Design
- Secure Authentication Mechanisms
- Password Hashing with SHA-256
- Network Performance Evaluation
- Mininet-based Network Emulation
- Wireshark Packet Analysis
- Software Testing and Documentation

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

This repository was developed as part of the ISEA Phase III Networking Internship at Tezpur University.

## Author

**Jitupan Mondal**
Tezpur University
ISEA Phase III Networking Internship 2026
GitHub: <https://github.com/Jitupan-mondal>
