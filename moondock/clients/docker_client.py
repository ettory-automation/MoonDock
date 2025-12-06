from __future__ import annotations
import docker, os
from docker.errors import DockerException
from moondock.config import (
    DOCKER_HOST,
    DOCKER_TLS_VERIFY,
    DOCKER_CERT_PATH,
)
from moondock.logger import logger

cert_path = os.path.normpath(DOCKER_CERT_PATH)

def _build_tls_config():
    """
    Builds TLS configuration for tcp:// connections.
    Returns None when TLS is disabled.
    """
    if not DOCKER_TLS_VERIFY:
        return None
    
    if not DOCKER_CERT_PATH:
        logger.error("TLS enabled but DOCKER_CERT_PATH not provided.")
        raise RuntimeError("TLS is enabled but certificate path is missing.")
    
    return docker.tls.TLSConfig(
        client_cert=(
            f"{cert_path}/cert.pem",
            f"{cert_path}/key.pem",
        ),
        ca_cert=f"{cert_path}/ca.pem",
        verify=True
    )

def init_docker() -> docker.DockerClient:
    """
    Initialize and configures a DockerClient instance based on environment settings.
    Supports:
        - unix:///var/run/docker.sock
        - tcp://127.0.0.1:2375 (insecure)
        - tcp://127.0.0.1:2376 (secure)
    """

    logger.info(f"Initializing Docker client - host: {DOCKER_HOST}")

    tls_config = None

    if DOCKER_HOST.startswith("tcp://"):
        if DOCKER_TLS_VERIFY:
            logger.info("TLS mode enabled for Docker connection.")
            tls_config = _build_tls_config()
        else:
            logger.warning(
                "Connecting to Docker via TCP WITHOUT TLS..."
                "This is insecure for production environments."
            )
    
    try:
        client = docker.DockerClient(
            base_url=DOCKER_HOST,
            tls=tls_config,
        )

        # Testing connectivity
        client.ping()
        logger.info("Docker client initialized successfully.")

        return client
    except DockerException as e:
        logger.critical(f"Failed to connect to Docker Engine: {e}")
        raise RuntimeError(f"Could not connect to Docker daemon: {e}")
