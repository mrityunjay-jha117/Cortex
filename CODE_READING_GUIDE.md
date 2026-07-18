# Cognitive Automator — Code Reading Guide

Welcome to the **Cognitive Automator** codebase! This document provides a chronological guide on how to read and understand the source code. Follow this flow to grasp how the data model, execution engine, user interface, and recording system fit together.

---

## 1. Entry Point & Orchestration
Start here to understand how the application launches and initializes its core components.

* `cognitive_automator/__main__.py` — The package entry point (invoked via `python -m cognitive_automator`).
* `cognitive_automator/main.py` — The actual `main()` function that bootstraps the PyQt6 application and instantiates the main window.
* `cognitive_automator/__init__.py` — Package initialization.

## 2. Core Data Models (The Graph)
The heart of the application is a directed graph of nodes built on top of Pydantic. Understanding these files is critical, as they dictate the structure of automations.

* `cognitive_automator/graph_model/__init__.py` — Exports all node models.
* `cognitive_automator/graph_model/enums.py` — Shared enumerations (e.g., node categories, interaction types).
* `cognitive_automator/graph_model/edges.py` — Defines `Edge` and `EdgeLabel` connecting the nodes.
* `cognitive_automator/graph_model/base.py` — Contains `BaseNode`, the parent class of all nodes.
* **Specific Node Models:**
  * `cognitive_automator/graph_model/system.py` — System nodes (GlobalStart, GlobalEnd).
  * `cognitive_automator/graph_model/physical.py` — Mouse, Keyboard, Clipboard, and Navigation nodes.
  * `cognitive_automator/graph_model/vision.py` — LocateElement, OCR, Vision Extraction, and Screenshot nodes.
  * `cognitive_automator/graph_model/llm.py` — Generative, Judgment, and LLM Extraction nodes.
  * `cognitive_automator/graph_model/flow.py` — Logic nodes (Branching, Loops, Wait, SubGraph, Compare).
* `cognitive_automator/graph_model/graph.py` — Defines `ActionGraph`, the container holding all nodes and edges.

## 3. Serialization
Once you understand the graph models, see how they are saved to and loaded from disk.

* `cognitive_automator/serializer.py` — Handles dumping the Pydantic `ActionGraph` to JSON (`.cogauto` files) and loading it back safely.

## 4. Execution Engine (Runtime)
This section explains how the static `ActionGraph` is actually executed step-by-step.

* `cognitive_automator/runtime/__init__.py` — Module init.
* `cognitive_automator/runtime/executor.py` — The `GraphExecutor` class. This traverses the graph, manages the context pipeline, handles variables (`${var}` interpolation), and orchestrates node execution.
* **Node Executors (Implementations):**
  * `cognitive_automator/nodes/__init__.py` & `cognitive_automator/nodes/executors/__init__.py`
  * `cognitive_automator/nodes/executors/base.py` — The `execute_node` registry pattern.
  * `cognitive_automator/nodes/executors/physical.py` — PyAutoGUI implementations for clicks/keystrokes.
  * `cognitive_automator/nodes/executors/vision.py` — OpenCV template matching and screenshot logic.
  * `cognitive_automator/nodes/executors/llm.py` — Routing for AI nodes.
  * `cognitive_automator/nodes/executors/flow.py` — Implementations for loops, waits, and comparisons.

## 5. LLM Integration
The "Cognitive" part of the automator. These files handle communication with Gemini.

* `cognitive_automator/llm/__init__.py` — Module init.
* `cognitive_automator/llm/client.py` — The core `GeminiClient` wrapper for the `google-genai` SDK.
* `cognitive_automator/llm/structured.py` — Pydantic schemas enforcing structured JSON output from the LLM.
* `cognitive_automator/llm/templates.py` — System instructions and prompt templates used across AI nodes.

## 6. Graphical User Interface (GUI)
This section brings the graph to life visually.

* `cognitive_automator/gui/__init__.py` — Module init.
* `cognitive_automator/gui/constants.py` — Global theme colors (monochromatic black/white/grey aesthetic), styles, and UI layout constants.
* `cognitive_automator/gui/main_window.py` — `MainWindow`, the outer shell housing the toolbar, dockable panels, and the central canvas view.
* **Canvas Framework (QGraphics architecture):**
  * `cognitive_automator/gui/canvas/__init__.py`
  * `cognitive_automator/gui/canvas/base.py` — Grid settings and base math.
  * `cognitive_automator/gui/canvas/port.py` — Visual input/output sockets for nodes.
  * `cognitive_automator/gui/canvas/edge.py` — The bezier curve connections.
  * `cognitive_automator/gui/canvas/node.py` — The visual representation of `BaseNode` (cards, headers, shadow hover states).
  * `cognitive_automator/gui/canvas/scene.py` — `GraphScene`, manages node addition, selection, drawing the dotted background grid, and translating graph data to UI widgets.
  * `cognitive_automator/gui/canvas/view.py` — `GraphView`, handles zooming, panning, and right-click context menus for spawning nodes.

## 7. GUI Panels & Property Editing
How users configure node properties on the right side of the screen.

* `cognitive_automator/gui/panels/__init__.py`
* `cognitive_automator/gui/panels/log_panel.py` — The execution log readout widget.
* **Property Panel & Builders:**
  * `cognitive_automator/gui/panels/property_panel/__init__.py`
  * `cognitive_automator/gui/panels/property_panel/base.py` — The main `PropertyPanel` stacked widget that swaps forms based on the selected node.
  * `cognitive_automator/gui/panels/property_panel/helpers.py` — Helper functions for binding inputs (`QLineEdit`, `QSpinBox`) to Pydantic models dynamically.
  * `cognitive_automator/gui/panels/property_panel/builders/__init__.py` — Merges all domain-specific builder mixins.
  * `cognitive_automator/gui/panels/property_panel/builders/base.py` — Common rendering helpers.
  * `cognitive_automator/gui/panels/property_panel/builders/data.py` — Form builders for CSV / File nodes.
  * `cognitive_automator/gui/panels/property_panel/builders/flow.py` — Form builders for logical/loop nodes.
  * `cognitive_automator/gui/panels/property_panel/builders/llm.py` — Form builders for LLM nodes.
  * `cognitive_automator/gui/panels/property_panel/builders/physical.py` — Form builders for mouse/keyboard inputs.
  * `cognitive_automator/gui/panels/property_panel/builders/vision.py` — Form builders for vision nodes.

## 8. Recording System & Overlay Widgets
The system that translates real human demonstrations (mouse clicks, keyboard types) into graph nodes on the fly.

* `cognitive_automator/recorder/__init__.py`
* `cognitive_automator/recorder/hooker.py` — Uses the `pynput` library to globally listen for OS-level mouse and keyboard events.
* `cognitive_automator/recorder/translator.py` — Takes raw hooks and consolidates them into actionable graph nodes (e.g., merging consecutive key presses into a single string).
* **Overlay Widgets (The floating trainer UI):**
  * `cognitive_automator/gui/widgets/__init__.py`
  * `cognitive_automator/gui/widgets/recording_overlay.py` — The transparent, always-on-top window managing recording state, image looping, and graph construction.
  * `cognitive_automator/gui/widgets/screen_region_selector.py` — A semi-transparent overlay to draw a rectangle for selecting template images or OCR regions.
  * `cognitive_automator/gui/widgets/data_extraction_dialog.py` — Modal for specifying variable names and schema types for unstructured LLM data extraction.
  * `cognitive_automator/gui/widgets/logic_inject_dialog.py` — Modal to insert waits, comparisons, and branches on the fly while recording.
