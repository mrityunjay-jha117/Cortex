"""
serializer.py — Bidirectional JSON ↔ YAML codec for ActionGraph.

File extension .cogauto → YAML (human-readable, VCS-friendly).
JSON used internally for IPC between recorder and GUI.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from cognitive_automator.graph_model import ActionGraph


COGAUTO_EXTENSION = ".cogauto"
SCHEMA_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_graph(graph: ActionGraph, path: str | Path) -> None:
    """
    Save an ActionGraph to disk.
    • .cogauto or .yaml → YAML
    • .json           → JSON
    """
    path = Path(path)
    graph.metadata.modified_at = _now_iso()
    if not graph.metadata.created_at:
        graph.metadata.created_at = graph.metadata.modified_at

    data = graph.model_dump_with_types()
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix in (".cogauto", ".yaml", ".yml"):
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    else:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def load_graph(path: str | Path) -> ActionGraph:
    """
    Load an ActionGraph from a .cogauto / .yaml / .json file.
    Runs full Pydantic validation on load.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Graph file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        if path.suffix in (".cogauto", ".yaml", ".yml"):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    _check_schema_version(data, path)
    return ActionGraph(**data)


def graph_to_json_str(graph: ActionGraph) -> str:
    """Compact JSON string for IPC."""
    return json.dumps(graph.model_dump_with_types(), separators=(",", ":"))


def graph_from_json_str(s: str) -> ActionGraph:
    return ActionGraph(**json.loads(s))


def new_graph(name: str = "Untitled Automation") -> ActionGraph:
    graph = ActionGraph()
    graph.metadata.name = name
    graph.metadata.created_at = _now_iso()
    graph.metadata.modified_at = graph.metadata.created_at
    graph.metadata.schema_version = SCHEMA_VERSION
    return graph


def _check_schema_version(data: dict, path: Path) -> None:
    version = data.get("metadata", {}).get("schema_version", 1)
    if version > SCHEMA_VERSION:
        raise ValueError(
            f"Graph '{path.name}' uses schema v{version} but this "
            f"version of Cognitive Automator only supports up to v{SCHEMA_VERSION}. "
            "Please update the application."
        )
    if version < SCHEMA_VERSION:
        _migrate(data, from_version=version)


def _migrate(data: dict, from_version: int) -> None:
    """Schema migration stubs — extend as schema evolves."""
    if from_version == 0:
        # v0 → v1: add metadata block if missing
        data.setdefault("metadata", {})
        data["metadata"].setdefault("schema_version", 1)
