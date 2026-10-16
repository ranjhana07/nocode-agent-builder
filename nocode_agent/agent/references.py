from __future__ import annotations

import re
from typing import Any

REFERENCE = re.compile(r"^\$([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$")


def resolve_references(value: Any, refs: dict[str, dict[str, Any]], errors: list[str]) -> Any:
    if isinstance(value, str):
        match = REFERENCE.match(value)
        if not match:
            return value
        alias, attribute = match.groups()
        if alias not in refs:
            errors.append(f"unknown reference {value}: no object was saved as {alias}")
            return value
        if attribute not in refs[alias]:
            errors.append(f"unknown reference {value}: {alias} has no field {attribute}")
            return value
        return refs[alias][attribute]
    if isinstance(value, dict):
        return {key: resolve_references(item, refs, errors) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_references(item, refs, errors) for item in value]
    return value
