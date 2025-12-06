from __future__ import annotations
import time, threading
from typing import Callable, Optional, Dict, Any

import docker
from docker.errors import APIError, DockerException
from moondock.logger import logger

EventCallback = Callable[[Dict[str, Any]], None]


class DockerEventWatcher:
    """
    Docker event watcher:
        - opens stream with client.events(decode=True)
        - sends raw events to a callback
        - reconnects with exponential backoff
        - supports graceful stop via stop()
    """

    def __init__(
        self,
        client: docker.DockerClient,
        callback: EventCallback,
        *,
        initial_backoff: float = 1.0,
        backoff_factor: float = 2.0,
        max_backoff: float = 60.0,
        max_retries: Optional[int] = None,
    ):
        self.client = client
        self.callback = callback
        self.initial_backoff = float(initial_backoff)
        self.backoff_factor = float(backoff_factor)
        self.max_backoff = float(max_backoff)
        self.max_retries = None if max_retries is None else int(max_retries)

        self._stop_event = threading.Event()
        self._worker: Optional[threading.Thread] = None

    def start_in_background(self) -> None:
        """
        Starts the watcher in a background thread (non-blocking).
        """
        if self._worker and self._worker.is_alive():
            logger.warning("DockerEventWatcher already running.")
            return

        self._worker = threading.Thread(
            target=self._run,
            daemon=True,
            name="DockerEventWatcher"
        )
        self._worker.start()
        logger.info("DockerEventWatcher started in background thread.")

    def start_forever(self) -> None:
        """
        Starts the watcher on the current thread (blocking).
        """
        logger.info("DockerEventWatcher starting in foreground (blocking) mode.")
        self._run()

    def stop(self) -> None:
        """
        Gracefully stops the watcher.
        """
        logger.info("Stopping DockerEventWatcher...")
        self._stop_event.set()
        if self._worker:
            self._worker.join(timeout=5.0)
            logger.info("DockerEventWatcher thread joined.")

    def _run(self) -> None:
        """
        Main event loop:
        - tries to open event stream
        - forwards events to callback
        - reconnects on error with exponential backoff
        """
        retries = 0
        backoff = self.initial_backoff

        while not self._stop_event.is_set():
            try:
                logger.info("Opening Docker event stream...")
                stream = self.client.events(decode=True)

                # Reset state after successful open
                retries = 0
                backoff = self.initial_backoff

                for raw_event in stream:
                    if self._stop_event.is_set():
                        logger.info("Stop requested — breaking event loop.")
                        break

                    try:
                        self.callback(raw_event)
                    except Exception as cb_exc:
                        logger.exception("Error inside event callback: %s", cb_exc)

                if self._stop_event.is_set():
                    break

                logger.warning(
                    "Docker event stream closed unexpectedly; will attempt to reconnect."
                )
                time.sleep(backoff)

            except (APIError, DockerException, OSError) as exc:
                retries += 1
                logger.error("Docker event stream error: %s", exc)

                if self.max_retries is not None and retries > self.max_retries:
                    logger.critical(
                        "Exceeded maximum retries (%s). Stopping watcher.",
                        self.max_retries
                    )
                    break

                logger.info(
                    "Reconnecting to Docker events in %.1fs (attempt %d).",
                    backoff, retries
                )
                time.sleep(backoff)
                backoff = min(backoff * self.backoff_factor, self.max_backoff)

            except Exception as exc:
                logger.exception("Unexpected error in DockerEventWatcher main loop: %s", exc)
                time.sleep(backoff)
                backoff = min(backoff * self.backoff_factor, self.max_backoff)

        logger.info("DockerEventWatcher stopped.")
