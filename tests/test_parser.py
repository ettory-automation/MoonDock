import time
from moondock.events.parser import parse_event, NormalizedEvent
from moondock.logger import logger

def sample_die_event() -> dict:
    """
    Minimal realistic Docker 'die' event sample.
    """
    return {
        "Type": "container",
        "Action": "die",
        "id": "91ab3921c2384f5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9",
        "time": int(time.time()),
        "Actor": {
            "Attributes": {
                "name": "my_test_container",
                "image": "busybox:latest",
                "exitCode": "137",
            }
        }
    }

def test_parse_die_event():
    raw = sample_die_event()
    ne = parse_event(raw)

    assert isinstance(ne, NormalizedEvent)
    assert ne.domain == "container"
    assert ne.action == "die"
    assert ne.id.startswith("91ab3921c238")  # partial match to avoid full id dependence
    assert ne.name == "my_test_container"
    assert ne.image == "busybox:latest"
    assert isinstance(ne.timestamp, float)
    assert ne.exit_code == 137

def test_parse_non_dict_returns_none():
    assert parse_event(None) is None # Changed to pass an empty dict, as None is not a valid type for raw # type: ignore
    assert parse_event("not-a-dict") is None # type: ignore
    