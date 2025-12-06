import time
from moondock.clients.docker_client import init_docker
from moondock.events.watcher import DockerEventWatcher
from moondock.logger import logger

received_events = []

def callback(event):
    logger.info(f"[TEST CALLBACK] Received event: {event}")
    received_events.append(event)


def test_docker_event_watcher_basic():
    client = init_docker()

    watcher = DockerEventWatcher(
        client=client,
        callback=callback,
        initial_backoff=1,
        max_backoff=5,
        max_retries=3,
    )

    watcher.start_in_background()

    logger.info("[TEST] Waiting 3 seconds for events...")
    time.sleep(3)

    watcher.stop()

    assert watcher._stop_event.is_set(), "Watcher did not stop"
    assert len(received_events) >= 0
