from __future__ import annotations

import json
from typing import Any

from nocode_agent.rag.types import Chunk

HTTP_METHODS = ("get", "post", "put", "patch", "delete")


def resolve_ref(spec: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    reference = schema.get("$ref")
    if not reference:
        return schema
    node: Any = spec
    for part in reference.removeprefix("#/").split("/"):
        node = node[part]
    return node


def describe_property(name: str, prop: dict[str, Any], required: set[str]) -> str:
    details = [prop.get("type", "any")]
    if "enum" in prop:
        details.append("one of " + ", ".join(str(value) for value in prop["enum"]))
    for bound in ("minLength", "maxLength", "minItems", "maxItems", "minimum", "maximum", "pattern"):
        if bound in prop:
            details.append(f"{bound}={prop[bound]}")
    if "default" in prop:
        details.append(f"default={json.dumps(prop['default'])}")
    flag = "required" if name in required else "optional"
    description = prop.get("description", "")
    return f"- {name} ({', '.join(details)}, {flag}): {description}".rstrip()


def describe_schema(spec: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    schema = resolve_ref(spec, schema)
    required = set(schema.get("required", []))
    return [describe_property(name, prop, required) for name, prop in schema.get("properties", {}).items()]


def split_openapi(spec: dict[str, Any], source: str = "openapi.json") -> list[Chunk]:
    version = str(spec.get("info", {}).get("version", ""))
    chunks: list[Chunk] = []
    for path, methods in spec.get("paths", {}).items():
        for method in HTTP_METHODS:
            operation = methods.get(method)
            if not operation:
                continue
            name = operation.get("operationId", f"{method}_{path}")
            lines = [f"OpenAPI operation {name}: {method.upper()} {path}"]
            if operation.get("summary"):
                lines.append(operation["summary"])
            for parameter in operation.get("parameters", []):
                lines.append(f"- path parameter {parameter['name']} ({parameter['schema'].get('type', 'any')})")
            body = operation.get("requestBody", {}).get("content", {}).get("application/json", {})
            if body:
                lines.append("Request body fields:")
                lines.extend(describe_schema(spec, body["schema"]))
            for status, response in operation.get("responses", {}).items():
                lines.append(f"Response {status}: {response.get('description', '')}")
            chunks.append(
                Chunk(
                    id=f"{source}#op-{name}",
                    text="\n".join(lines),
                    metadata={
                        "source": source,
                        "title": f"OpenAPI {name}",
                        "doc_type": "openapi",
                        "workflow": name,
                        "section": f"{method.upper()} {path}",
                        "version": version,
                    },
                )
            )
    for schema_name, schema in spec.get("components", {}).get("schemas", {}).items():
        if not schema.get("properties"):
            continue
        lines = [f"OpenAPI schema {schema_name}", *describe_schema(spec, schema)]
        chunks.append(
            Chunk(
                id=f"{source}#schema-{schema_name}",
                text="\n".join(lines),
                metadata={
                    "source": source,
                    "title": f"OpenAPI schema {schema_name}",
                    "doc_type": "openapi",
                    "workflow": "none",
                    "section": f"schema {schema_name}",
                    "version": version,
                },
            )
        )
    return chunks
