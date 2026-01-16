# MoonDock 🌕🐳

MoonDock is a lightweight, event-driven monitoring agent designed to observe Docker Engine events and dispatch real-time, formatted alerts to Discord. Built with resilience in mind, it ensures you never miss a container failure, OOM kill, or health status change.

## 🚀 Key Features

- Real-time Event Watcher: Utilizes the Docker Engine API to stream events with low overhead.

- Resilient Connectivity: Implements exponential backoff for automatic reconnection if the Docker daemon or network fails.

- Advanced Parsing: Normalizes raw Docker events into canonical structures, capturing exit codes, image tags, and container names.

- Rich Discord Alerts: Sends color-coded Discord embeds based on event severity (e.g., Critical Red for die/oom, Green for start).

- Production Ready: Supports Unix Sockets and TCP/TLS connections for remote Docker hosts.

- Highly Configurable: 100% environment-variable driven for easy deployment in CI/CD pipelines.

## 🛠️ Tech Stack

Language: Python 3.10+

Libraries: docker-py, requests, python-dotenv, colorama.

Testing: pytest with unittest.mock for infrastructure simulation.

## 📋 Prerequisites

1. Docker Engine installed and running.

2. A Discord Webhook URL.

3. Python 3.10+ (if running bare-metal).

## ⚙️ Configuration

Define your variables in the .env file present in the root of this repository, using the guide below:

| Variable | Description |
|:---:|:---:|
| DISCORD_WEBHOOK	| Your Discord Channel Webhook URL|
| DOCKER_HOST	| Docker daemon socket/address |
| DOCKER_TLS_VERIFY | Enable TLS for TCP connections |
| DOCKER_CERT_PATH | Path to TLS certificates |
| LOG_LEVEL | Logging verbosity (DEBUG, INFO, ERROR) |

## 📦 Installation & Usage

1. Clone the repository:

```bash
git clone https://github.com/ettory-automation/MoonDock.git
cd MoonDock
```

2. Setup Environment: Edit .env with your Discord Webhook.

3. Running as a System Service (Recommended):

To ensure MoonDock remains independent of the Docker Daemon state, it is recommended to run it as a system service. This allows the agent to alert even if the Docker Engine crashes.

- Create a Virtual Environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

- Running Tests:

```bash
pytest -q
```

- Setup Systemd Service: Create a file at `/etc/systemd/system/moondock.service`:

```ini
[Unit]
Description=MoonDock - Docker Event Watcher
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/moondock
EnvironmentFile=/path/to/moondock/.env
ExecStartPre=/path/to/moondock/venv/bin/pytest -q
ExecStart=/path/to/moondock/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- Enable and Start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable moondock
sudo systemctl start moondock
```

## 🧪 Project Structure

- moondock/clients/: Connectivity logic for Docker and Discord.

- moondock/events/: Core logic for watching and parsing raw Docker streams.

- moondock/logger.py: Tailored logging with terminal colors for better debugging.

- tests/: Comprehensive test suite using mocks to ensure parser and watcher reliability.

## 🛡️ Safety & Security

- TLS Support: Ready for secured Docker remote API communication.

- Graceful Shutdown: Handles SIGINT and SIGTERM to close event streams properly.

- Defensive Parsing: The event parser is designed to handle malformed Docker events without crashing the main loop.
