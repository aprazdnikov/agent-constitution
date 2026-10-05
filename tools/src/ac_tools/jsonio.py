import json
from pathlib import Path


class ManifestError(Exception):
    pass


def as_object(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        msg = f"{where} must be an object"
        raise ManifestError(msg)
    return {str(key): item for key, item in value.items()}


def load_object(path: Path) -> dict[str, object]:
    try:
        data: object = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ManifestError("missing file") from error
    except UnicodeDecodeError as error:
        raise ManifestError("not valid UTF-8") from error
    except json.JSONDecodeError as error:
        msg = f"invalid JSON: {error.msg} at line {error.lineno}"
        raise ManifestError(msg) from error
    return as_object(data, "document")


def text_field(obj: dict[str, object], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str):
        msg = f"field '{key}' must be a string"
        raise ManifestError(msg)
    return value


def object_field(obj: dict[str, object], key: str) -> dict[str, object]:
    return as_object(obj.get(key), f"field '{key}'")


def object_list(obj: dict[str, object], key: str) -> list[dict[str, object]]:
    value = obj.get(key)
    if not isinstance(value, list):
        msg = f"field '{key}' must be an array"
        raise ManifestError(msg)
    return [as_object(item, f"{key}[{index}]") for index, item in enumerate(value)]
