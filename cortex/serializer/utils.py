"""
=============================================================================
 SERIALIZER UTILS
=============================================================================
This module provides helper functions for data conversion.
It contains recurring patterns for dictionary manipulation and type casting.

Key Features:
1. Handles complex type conversions that standard JSON libraries struggle with.
2. Cleans up edge-case data before it hits the disk.

Think of this module as the Swiss army knife for formatting text.
=============================================================================
"""

from __future__ import annotations
from datetime import datetime, timezone

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
