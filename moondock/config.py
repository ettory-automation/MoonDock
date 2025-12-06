from __future__ import annotations
from typing import List 
from dotenv import load_dotenv
import os

load_dotenv()

# Discord Webhook (unique string). Absolute necessary in production environment
DISCORD_WEBHOOK: str = os.getenv("DISCORD_WEBHOOK", "").strip()

# Docker Engine host. Default -> unix:///var/run/docker.sock for local environment (secure pattern)
# If necessary, change to -> tcp://host:2375 (2375 for normal TLS communication)
DOCKER_HOST: str = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock").strip()

# If using connection mode as TCP with TLS:
DOCKER_TLS_VERIFY: bool = os.getenv("DOCKER_TLS_VERIFY", "").strip() in ("1", "true", "True")
DOCKER_CERT_PATH: str = os.getenv("DOCKER_CERT_PATH", "").strip()

# Critical events (default values). Can be overrided for a env var CSV
_default_events = ["die", "oom", "kill", "restart"]
CRITICAL_EVENTS: List[str] = [
    e.strip() for e in os.getenv("CRITICAL_EVENTS", ",".join(_default_events)).strip(",") if e.strip()
]

# Logging base config
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# Timeout for requests (Discord, etc)
HTTP_TIMEOUT_SECONDS: int = int(os.getenv("HTTP_TIMEOUT_SECONDS", "5"))

# Recommendations / safety hints (debug helper step)
if DOCKER_HOST.startswith("tcp://") and not DOCKER_TLS_VERIFY:
    # don't use exception - only print for development environments. Main logging may realize this verification step.
    print("WARNING: DOCKER_HOST is configured as TCP without TLS. This is insecure for production environments.")
if not DISCORD_WEBHOOK:
    print("WARNING: DISCORD_WEBHOOK not configured — alerts will not be sent to Discord.")