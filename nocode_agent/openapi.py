from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HTTP_METHODS = ("get", "post", "put", "patch", "delete")


@dataclass
class Operation:
    name: str
    method: str
    path: str
    summary: str
    path_params: list[str]
    schema: dict[str, Any]
    required: list[str] = field(default_factory=list)

    @property
    def body_params(self) -> list[str]:
        return [name for name in self.schema.get("properties", {}) if name not in self.path_params]


def resolve_refs(node: Any, components: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        if "$ref" in node:
            name = node["$ref"].split("/")[-1]
            return resolve_refs(copy.deepcopy(components[name]), components)
        return {key: resolve_refs(value, components) for key, value in node.items()}
    if isinstance(node, list):
        return [resolve_refs(item, components) for item in node]
    return node


def strip_noise(schema: Any) -> Any:
    if isinstance(schema, dict):
        return {key: strip_noise(value) for key, value in schema.items() if not (key == "title" and isinstance(value, str))}
    if isinstance(schema, list):
        return [strip_noise(item) for item in schema]
    return schema


def operation_schema(spec: dict[str, Any], operation: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    components = spec.get("components", {}).get("schemas", {})
    properties: dict[str, Any] = {}
    required: list[str] = []
    path_params: list[str] = []
    for parameter in operation.get("parameters", []):
        if parameter.get("in") != "path":
            continue
        path_params.append(parameter["name"])
        properties[parameter["name"]] = strip_noise(parameter.get("schema", {"type": "integer"}))
        required.append(parameter["name"])
    body = operation.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
    if body:
        resolved = strip_noise(resolve_refs(body, components))
        properties.update(resolved.get("properties", {}))
        required.extend(resolved.get("required", []))
    schema = {"type": "object", "properties": properties, "required": required, "additionalProperties": False}
    return schema, path_params


def extract_operations(spec: dict[str, Any]) -> dict[str, Operation]:
    operations: dict[str, Operation] = {}
    for path, methods in spec.get("paths", {}).items():
        for method in HTTP_METHODS:
            raw = methods.get(method)
            if not raw or "operationId" not in raw:
                continue
            schema, path_params = operation_schema(spec, raw)
            operations[raw["operationId"]] = Operation(
                name=raw["operationId"],
                method=method.upper(),
                path=path,
                summary=raw.get("summary", ""),
                path_params=path_params,
                schema=schema,
                required=list(schema["required"]),
            )
    return operations


def load_operations(path: Path) -> dict[str, Operation]:
    return extract_operations(json.loads(path.read_text(encoding="utf-8")))


def validate_arguments(operation: Operation, arguments: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(operation.schema)
    messages: list[str] = []
    for error in sorted(validator.iter_errors(arguments), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path)
        messages.append(f"{location}: {error.message}" if location else error.message)
    return messages
