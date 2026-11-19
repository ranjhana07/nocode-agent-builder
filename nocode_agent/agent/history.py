from __future__ import annotations

from pathlib import Path
from typing import Any

from nocode_agent.agent.graph import make_checkpointer


def load_thread_state(checkpoint_db: Path, thread_id: str) -> dict[str, Any] | None:
    if not checkpoint_db.exists():
        return None
    saved = make_checkpointer(checkpoint_db).get_tuple({"configurable": {"thread_id": thread_id}})
    if saved is None:
        return None
    return dict(saved.checkpoint["channel_values"])
