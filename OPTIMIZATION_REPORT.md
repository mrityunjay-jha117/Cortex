# Cognitive Automator — Optimization Report

This document details the performance optimizations made across the repository to improve execution speed, reduce disk I/O bottlenecks, and enhance visual responsiveness.

## 1. Graph Traversal and Edge Lookup Optimization
**File:** `cognitive_automator/runtime/executor.py`
* **Previous Problem:** The graph execution engine relied on full-list traversals (`O(E)`) for every edge lookup (e.g., `[e for e in self.graph.edges if e.source_id == u]`). When checking for back-edges (via DFS) or popping nodes from the execution queue, the engine traversed the entire edge list repeatedly, leading to an `O(V * E)` time complexity. This could cause severe slowdowns on large graphs with many nodes and edges.
* **Optimization:** Replaced the full list traversals with pre-calculated adjacency lists (a dictionary mapping nodes to their respective edges). This reduced the complexity to `O(V + E)`, enabling instant constant-time lookups during graph traversal and the node execution phase.

## 2. Dynamic Signature Parsing Caching
**File:** `cognitive_automator/runtime/executor.py`
* **Previous Problem:** The executor's internal dispatcher `_call_executor` used `inspect.signature(func)` on every single node execution to check if the node's underlying executor function accepted arguments like `abort_signal` or `emit_info`. `inspect.signature` is known to be computationally heavy, causing an unnecessary multi-millisecond delay for every node executed in tight iterative loops.
* **Optimization:** Implemented a class-level LRU cache (`_executor_sig_cache`) that stores the compiled `inspect.Signature` object for each executor function after its first invocation. Subsequent executions now pull the signature directly from memory, virtually eliminating the overhead.

## 3. Removal of Arbitrary Hardcoded Sleeps
**File:** `cognitive_automator/runtime/executor.py`
* **Previous Problem:** The main execution loop contained a hardcoded `time.sleep(0.5)` after every successfully executed node. This effectively bottlenecked the entire automation process to a maximum throughput of 2 nodes per second, which was highly detrimental to fast loops and micro-tasks.
* **Optimization:** Removed the arbitrary 500ms sleep entirely. The engine now runs at maximum speed, relying on user-configured explicit wait nodes, application delays, and natural PyAutoGUI limits, vastly improving the throughput of iterative algorithms.

## 4. In-Memory Image Processing (Disk I/O Reduction)
**Files:** 
* `cognitive_automator/nodes/executors/vision.py`
* `cognitive_automator/nodes/executors/physical.py`
* `cognitive_automator/nodes/executors/flow/screenshotter.py`
* **Previous Problem:** Whenever a node required an AI reference image (e.g., locating an element or finding a focus point), the Base64 image string was decoded, written to a temporary `.png` file on the hard drive using the `tempfile` module, parsed by Pillow (`PIL`), and finally deleted from disk. Disk I/O operations are orders of magnitude slower than memory operations, and performing this heavily on every iteration caused massive performance throttling and SSD wear.
* **Optimization:** Rewrote the image decoding pipeline to use Python's `io.BytesIO`. The Base64 string is decoded directly into a byte stream in-memory, which is read natively by `PIL.Image.open()`. By bypassing the disk completely, reference images are loaded instantly.

## 5. Vision Polling Responsiveness
**File:** `cognitive_automator/nodes/executors/vision.py`
* **Previous Problem:** Inside the retry/wait loop for locating elements dynamically (`execute_locate_element`), the script paused for `0.3s` (300ms) between captures. If an element appeared immediately after a scan, the framework would idle for a third of a second before reacting.
* **Optimization:** Lowered the sleep interval in the polling loop from `0.3s` to `0.05s`. This provides a much tighter reaction window (scanning at ~20 FPS), ensuring the automation clicks elements the moment they appear without burning excessive CPU.

## 6. Physical Action Delays Tuning
**File:** `cognitive_automator/nodes/executors/physical.py`
* **Previous Problem:** Post-navigation clicks forced a `0.3s` delay to "ensure focus is gained," which artificially dragged out rapid keyboard and navigator events.
* **Optimization:** Reduced the stabilization sleep down to `0.1s`. The underlying `pyautogui` library natively incorporates sensible delays, so reducing this maintains UI stability while speeding up overall interactions.

## 7. LLM Template Engine Compilation Caching
**File:** `cognitive_automator/llm/templates.py`
* **Previous Problem:** The custom prompt renderer (`render_prompt`) was converting raw string templates to Jinja2 AST trees via `_env.from_string()` on every single LLM call and variable interpolation. Re-parsing string inputs dynamically is computationally wasteful and slows down data-binding inside large iterative graphs.
* **Optimization:** Extracted the parsing logic into `_get_template` and decorated it with `@functools.lru_cache(maxsize=256)`. The Jinja AST is now compiled once per unique template string, meaning all iterative calls and repetitive data bindings reuse the cached template engine directly, resulting in microsecond-fast interpolations.
