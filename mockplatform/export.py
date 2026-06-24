from __future__ import annotations

import json
import sys
from pathlib import Path

from mockplatform.main import create_platform_app


def export_openapi(target: Path) -> None:
    spec = create_platform_app("sqlite://").openapi()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(spec, indent=2, sort_keys=True) + "\n"
    target.write_text(payload, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    export_openapi(Path(sys.argv[1] if len(sys.argv) > 1 else "docs/openapi.json"))
