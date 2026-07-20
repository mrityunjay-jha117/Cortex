"""
=============================================================================
 NODES INITIALIZATION
=============================================================================
This module initializes the node execution package.
It bridges the data models (graph_model) with their actual runtime logic (executors).

Key Features:
1. Aggregates all node executor classes into a discoverable module.
2. Simplifies registration of available nodes for the runtime engine.

Think of this module as the directory mapping blueprints to actual workers.
=============================================================================
"""

