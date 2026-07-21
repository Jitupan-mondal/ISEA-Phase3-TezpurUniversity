# Assignment 8: Application Optimization, Scalability, and Reliability

This repository contains the enhanced version of a secure GUI-based multi-client TCP chat application developed as part of the ISEA Phase 3 Cybersecurity Internship. The project extends the earlier secure chat system by adding practical reliability, scalability, configuration, and performance-monitoring features while preserving the existing client-server architecture.

## Overview

The application is a Python-based TCP chat system with a Tkinter GUI client and a multithreaded server. In this assignment, the system was improved to support graceful shutdown, heartbeat-based dead client detection, automatic reconnection, configurable runtime parameters, concurrency limits, and performance logging. The focus is on building a more reliable and scalable network application without changing the core communication model.

## Objectives

- Improve reliability of the secure chat application.
- Support configurable server and client parameters using `config.json`.
- Detect stale or dead clients automatically using heartbeat and timeout logic.
- Handle server shutdown gracefully without leaving clients in an inconsistent state.
- Reconnect clients automatically after unexpected disconnection.
- Limit the number of concurrent clients safely using a semaphore.
- Measure and analyze latency, throughput, CPU usage, and memory usage.
- Verify protocol behavior using Wireshark packet captures.

## Features Implemented

### Reliability Features
- Graceful shutdown using signal handling.
- Heartbeat mechanism for live client detection.
- Dead client cleanup through a reaper thread.
- Automatic client reconnection with exponential backoff.

### Scalability Features
- Semaphore-based concurrency control.
- Support for multiple simultaneous clients in Mininet.
- Runtime configuration through `config.json`.

### Monitoring Features
- Periodic performance sampling every 5 seconds.
- Logging of active connections, throughput, latency, CPU, and memory.
- Export of results to `performance_results.csv`.
- Graph generation for performance analysis.

### Security Features Reused from Assignment 7
- JSON-based login authentication.
- SHA-256 password hashing.
- Duplicate login prevention.
- Input validation.
- Temporary login lockout after repeated failed attempts.
- Secure event logging without storing plaintext passwords.

## Technologies Used

- Python 3
- Socket programming
- Tkinter
- Multithreading
- Mininet
- Wireshark
- JSON configuration
- CSV-based performance logging
- Matplotlib / Pandas for graph generation

## Project Structure

```text
.
├── graphs/
│   ├── cpu_vs_clients.png
│   ├── latency_vs_clients.png
│   ├── memory_vs_clients.png
│   └── throughput_vs_clients.png
├── screenshots/
│   ├── fig_1_experimental_setup.png
│   ├── fig_2_server_console_graceful_shutdown.png
│   ├── fig_3_client_shutdown_notification.png
│   ├── fig_4_reaper_timeout_console.png
│   ├── fig_5_client_reconnection_success.png
│   ├── fig_6_login_lockout_dialog.png
│   ├── fig_7_input_validation_rejections.png
│   ├── fig_8_scale_test_5_clients.png
│   ├── fig_9_scale_test_8_clients.png
│   ├── fig_10_scale_test_10_clients.png
│   ├── fig_11_server_busy_rejection.png
│   ├── fig_12_config_reverted_confirmation.png
│   ├── fig_13_tcp_three_way_handshake.png
│   ├── fig_14_json_login_playload.png
│   ├── fig_15_login_success_response.png
│   ├── fig_16_heartbeat_packets_wireshark.png
│   ├── fig_17_broadcast_message_capture.png
│   └── fig_18_tcp_teardown_finack.png
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

## How to Run

### 1. Start Mininet
```bash
sudo mn --topo single,11
```

### 2. Start the server on `h1`
```bash
mininet> h1 python3 server.py
```

### 3. Start GUI clients on other hosts
```bash
mininet> h2 python3 client_gui.py &
mininet> h3 python3 client_gui.py &
mininet> h4 python3 client_gui.py &
```

### 4. Test reliability and scalability features
- Stop the server and observe graceful shutdown.
- Kill a client process to verify stale client cleanup.
- Restart the server and observe automatic reconnection.
- Lower the concurrency limit in `config.json` temporarily to test server busy rejection.
- Run 5, 8, and 10 client experiments to collect performance data.

## Wireshark Verification

Packet capture was performed using the filter below:

```text
tcp.port == 5000
```

The capture verifies:
- TCP three-way handshake
- JSON login request
- Login success response
- Periodic heartbeat traffic
- Broadcast message transmission
- TCP teardown using FIN/ACK

## Performance Summary

The server logs periodic performance measurements to `performance_results.csv`. Using these results, four graphs were generated:

- Latency vs concurrent clients
- Throughput vs concurrent clients
- CPU utilization vs concurrent clients
- Memory usage vs concurrent clients

The results show that the application remains stable under increasing client load, with low latency and predictable memory growth.

## Files Included for Submission

- `server.py`
- `client_gui.py`
- `config.json`
- `users.json`
- `security_log.txt`
- `server_log.txt`
- `performance_results.csv`
- `capture_auth.pcap`
- `graphs/`
- `screenshots/`
- `report.pdf`
- `handwritten_reflection.pdf`

## Learning Outcome

This assignment helped demonstrate how a secure socket-based application can be improved to become more robust in real-world conditions. The final system combines authentication, thread-safe GUI networking, resilience against client/server failures, configurable deployment, and measurable scalability in a single application.

## Author

**Jitupan Mondal**  
B.Tech Electrical Engineering, Tezpur University  
ISEA Phase 3 Cybersecurity Internship
