from moondock.logger import logger
from moondock.clients.docker_client import init_docker
from moondock.clients.discord_client import DiscordClient
from moondock.events.watcher import DockerEventWatcher
from moondock.events.parser import parse_event, NormalizedEvent

def docker_event_callback(raw_event: dict, discord_client: DiscordClient) -> None:
    ne: NormalizedEvent | None = parse_event(raw_event)
    if ne:
        try:
            discord_client.send_event(ne)
            logger.info("Event sent to Discord: %s %s", ne.domain, ne.action)
        except Exception as exc:
            logger.exception("Failed to send event to Discord: %s", exc)

def main() -> None:
    docker_client = init_docker()
    discord_client = DiscordClient()

    watcher = DockerEventWatcher(
        docker_client,
        lambda e: docker_event_callback(e, discord_client)
    )

    try:
        watcher.start_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping watcher...")
        watcher.stop()
    except Exception as exc:
        logger.critical("Unexpected error in main loop: %s", exc)
        watcher.stop()

if __name__ == "__main__":
    main()
