"""
serializer/utils.py — Serializer Utilities

This file provides common helper functions for the serialization engine, such as generating ISO-8601 UTC timestamps for metadata tracking.
"""
from __future__ import annotations
from datetime import datetime, timezone

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
