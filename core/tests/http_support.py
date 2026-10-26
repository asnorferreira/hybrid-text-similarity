from typing import Any


def json_object(response) -> dict[str, Any]:
    value = response.get_json()
    assert isinstance(value, dict), value
    return value
