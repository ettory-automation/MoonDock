from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import time

from moondock.logger import logger

@dataclass
class NormalizedEvent:
    """
    NormalizedEvent: canonical event structure used by MoonDock.
    - domain: original event Type (container, image, network, etc)
    - action: normalized action name (start, stop, die, create, etc)
    - id: resource id (container id, image id, ...)
    - name: human-friendly name (container name when available)
    - image: container image (if available)
    - exit_code: exit code for 'die' events (if present)
    - timestamp: unix epoch seconds (float)
    - attributes: raw Actor.Attributes (helpful for labels, etc)
    - raw: original raw event dict (for debugging)
    """
    domain: str
    action: str
    id: str
    name: Optional[str]
    image: Optional[str]
    exit_code: Optional[int]
    timestamp: float
    attributes: Dict[str, Any]
    raw: Dict[str, Any]

# mapping of common docker actions to normalized action names (keeps same where appropriate)
_ACTION_NORMALIZATION = {
    # container lifecycle
    "create": "create",
    "start": "start",
    "stop": "stop",
    "die": "die",
    "destroy": "destroy",
    "restart": "restart",
    "pause": "pause",
    "unpause": "unpause",
    # health
    "health_status: healthy": "health_healthy",
    "health_status: unhealthy": "health_unhealthy",
    # image
    "pull": "pull",
    "push": "push",
    # generic fallback: we will return the original action lowercased when unknown
}

def _to_timestamp(raw: Dict[str, Any]) -> float:
    """
    Extract a unix seconds timestamp from the raw event.
    Docker often provides 'time' (seconds) or 'timeNano' (nanoseconds).
    Fall back to current time if missing.
    """
    if raw is None:
        return time.time()

    t = raw.get("time")
    if isinstance(t, (int, float)) and t > 0:
        return float(t)

    tnano = raw.get("timeNano")
    if isinstance(tnano, (int, float)) and tnano > 0:
        # convert nanoseconds to seconds
        return float(tnano) / 1e9

    # sometimes there is 'timestamp' or 'timeStamp'
    t_alt = raw.get("timestamp") or raw.get("timeStamp")
    if isinstance(t_alt, (int, float)) and t_alt > 0:
        return float(t_alt)

    # fallback to now
    return time.time()

def _normalize_action(raw_action: Optional[str]) -> Optional[str]:
    """
    Normalize docker action strings.
    If action is None, try to fallback to 'status' key.
    """
    if not raw_action:
        return None

    # keep exact match first
    normalized = _ACTION_NORMALIZATION.get(raw_action)
    if normalized:
        return normalized

    # Some actions come like "health_status: healthy" — normalize by lowering.
    # For unknown ones, return lowercase trimmed string.
    try:
        return raw_action.strip().lower()
    except Exception:
        return raw_action

def _safe_get_actor_attributes(raw: Dict[str, Any]) -> Dict[str, Any]:
    actor = raw.get("Actor") or raw.get("actor") or {}
    attrs = actor.get("Attributes") or actor.get("attributes") or {}
    if not isinstance(attrs, dict):
        return {}
    return attrs

def _extract_container_info(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract container-specific info such as name, image, exit code, etc.
    Return a dict with keys: id, name, image, exit_code, attributes.
    """
    attrs = _safe_get_actor_attributes(raw)
    container_id = raw.get("id") or raw.get("ID") or attrs.get("container") or attrs.get("id")
    # container name usually under 'name' attribute
    name = attrs.get("name") or attrs.get("container") or None

    # image may be under 'image' attribute or 'image.name' etc
    image = attrs.get("image") or attrs.get("image.name") or None

    # exit code often in 'exitCode', 'exitCode', or 'exit' inside attributes or in raw
    exit_code = None
    for key in ("exitCode", "exit_code", "exit"):
        val = attrs.get(key)
        if val is None:
            val = raw.get(key)
        if val is not None:
            try:
                exit_code = int(val)
                break
            except Exception:
                # not an integer -> ignore
                exit_code = None

    return {
        "id": container_id,
        "name": name,
        "image": image,
        "exit_code": exit_code,
        "attributes": attrs,
    }

def parse_event(raw: Dict[str, Any]) -> Optional[NormalizedEvent]:
    """
    Parse a raw docker event dict and return a NormalizedEvent or None if the event
    is not relevant / cannot be normalized.

    The function is defensive: it will not raise on malformed input, it will log
    debug information on unexpected shapes.
    """
    if not isinstance(raw, dict):
        logger.debug("parse_event received non-dict raw event: %r", raw)
        return None

    domain = (raw.get("Type") or raw.get("type") or "unknown").lower()
    # prefer 'Action', but fallback to 'status' or 'action'
    raw_action = raw.get("Action") or raw.get("action") or raw.get("status")
    action = _normalize_action(raw_action)

    # If action still None, nothing to do
    if not action:
        logger.debug("parse_event: no action found in raw event: %r", raw)
        return None

    ts = _to_timestamp(raw)

    # Currently focus on container events; still create a normalized event for other domains.
    try:
        if domain == "container":
            info = _extract_container_info(raw)
            event_id = info.get("id") or "<unknown>"
            name = info.get("name")
            image = info.get("image")
            exit_code = info.get("exit_code")
            attributes = info.get("attributes", {})

            # Build normalized event
            ne = NormalizedEvent(
                domain=domain,
                action=action,
                id=event_id,
                name=name,
                image=image,
                exit_code=exit_code,
                timestamp=ts,
                attributes=attributes,
                raw=raw,
            )
            return ne

        else:
            # For non-container events we still return a simple normalized representation
            # Extract id if present
            resource_id = raw.get("id") or raw.get("ID") or None
            attributes = _safe_get_actor_attributes(raw)
            ne = NormalizedEvent(
                domain=domain,
                action=action,
                id=resource_id or "<unknown>",
                name=attributes.get("name"),
                image=attributes.get("image"),
                exit_code=None,
                timestamp=ts,
                attributes=attributes,
                raw=raw,
            )
            return ne

    except Exception as exc:
        logger.exception("parse_event failed to normalize raw event: %s", exc)
        return None
