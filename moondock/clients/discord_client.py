from __future__ import annotations
import requests
from typing import Optional
from moondock.config import DISCORD_WEBHOOK, HTTP_TIMEOUT_SECONDS
from moondock.events.parser import NormalizedEvent
from moondock.logger import logger

class DiscordClient:
    """
    Discord webhook client using embeds for nicely formatted messages.
    """

    # Map actions to emojis and embed colors
    ACTION_EMOJIS = {
        "die": "🪦 ",
        "kill": "💀 ",
        "oom": "💥 ",
        "restart": "⟲ ",
        "start": "▶️ ",
        "stop": "⏹️ ",
        "create": "🏗️ ",
        "destroy": "🗑️ ",
        "pause": "⏸️ ",
        "unpause": "▶️ ",
        "health_healthy": "❤️ ",
        "health_unhealthy": "💔 ",
        "pull": "⬇️ ",
        "push": "⬆️ ",
        "connect": "🔗 ",
        "disconnect": "⛓️ ",
        "attach": "🔌 "
    }

    ACTION_COLORS = {
        "die": 0xFF0000,         # Bright Red — critical
        "kill": 0xFF4500,        # OrangeRed — high impact
        "oom": 0xFF6347,         # Tomato — warning
        "restart": 0x1E90FF,     # Dodger Blue — restart
        "start": 0x00FF00,       # Green — OK
        "stop": 0x808080,        # Gray — neutral
        "create": 0x00CED1,      # Dark Turquoise — info
        "connect": 0xFFFF00,     # Yellow — minor warning
        "disconnect": 0xFFA500,  # Orange — warning
        "destroy": 0x8B0000,     # Maroon — final critical
        "pull": 0x1E90FF,        # Blue — info
        "push": 0x1E90FF,        # Blue — info
        "attach": 0x00CED1,      # Dark Turquoise — info
        "health_healthy": 0x00FF00,    # Red — OK
        "health_unhealthy": 0x00FF00   # Red — critical
    }

    def __init__(self, webhook_url: Optional[str] = None, timeout: int = HTTP_TIMEOUT_SECONDS):
        self.webhook_url = webhook_url or DISCORD_WEBHOOK
        self.timeout = timeout

        if not self.webhook_url:
            logger.warning("Discord webhook URL is not set. Messages will not be sent.")

    def send_event(self, event: NormalizedEvent) -> bool:
        """
        Sends a Discord embed message for the given Docker event.
        """
        if not self.webhook_url:
            logger.debug("No webhook URL configured, skipping Discord send.")
            return False

        embed = self._build_embed(event)
        payload = {"embeds": [embed]}

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=self.timeout)
            if response.status_code in (200, 204):
                logger.info("Event sent to Discord successfully.")
                return True
            else:
                logger.error(
                    "Failed to send event to Discord: %s %s",
                    response.status_code,
                    response.text
                )
                return False
        except requests.RequestException as e:
            logger.error("Exception while sending event to Discord: %s", e)
            return False

    def _build_embed(self, event: NormalizedEvent) -> dict:
        """
        Build a Discord embed dictionary from a NormalizedEvent with table-like alignment.
        """
        emoji = self.ACTION_EMOJIS.get(event.action, "")
        color = self.ACTION_COLORS.get(event.action, 0x808080)

        table_lines = [
            f"Domain      : {event.domain}",
            f"Action      : {event.action}"
        ]

        if event.domain == "container":
            table_lines.extend([
                f"Name        : {event.name or 'N/A'}",
                f"Image       : {event.image or 'N/A'}",
                f"ID          : {event.id[:12]}",
            ])
            if event.exit_code is not None:
                table_lines.append(f"Exit Code   : {event.exit_code}")
        elif event.domain == "network":
            table_lines.extend([
                f"Network     : {event.name or 'N/A'}",
                f"Container   : {event.name or 'N/A'}"
            ])
        else:
            table_lines.append(f"ID          : {event.id[:12] if event.id else '<unknown>'}")

        description = "```" + "\n".join(table_lines) + "```"

        embed = {
            "title": f"{emoji} Docker Event Detected",
            "color": color,
            "description": description
        }

        return embed


