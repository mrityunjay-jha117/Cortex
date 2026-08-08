Traditional automation tools often break when a website redesigns a button, an unexpected pop-up appears, or an app runs inside a remote desktop (RDP/Citrix) where web selectors simply do not exist.

**Cortex** bridges the gap between traditional UI automation and modern artificial intelligence:

* **The Eyes (Computer Vision):** Cortex "sees" the screen using template matching and Optical Character Recognition (OCR), completely independent of fragile HTML DOM code.
* **The Brain (Large Language Models / VLMs):** Cortex "thinks" and makes dynamic decisions when unexpected scenarios occur, with self-healing capabilities that adapt to UI shifts.
* **The Hands (Physical Device Control):** Cortex "acts" by commanding the operating system to move the mouse, click, drag, scroll, and type keys just like a real human sitting at the machine.

Automations in Cortex are built as **visual node graphs** that are saved as `.cortex` project files and executed by a resilient runtime engine across **Windows, Linux, and macOS**.

---

## Core USPs (Unique Selling Propositions)

### 1. Token-Based Graph Execution Algorithm
Unlike standard automation tools that rely on sequential scripts, basic `while/if` recursion, or simple DAG (Directed Acyclic Graph) topological sorts:
* **Why traditional tools fail:** Standard visual editors struggle with complex control flow like `do-while` loops, conditional branching, or multi-path joins. They either hit Python recursion limits, lock up in infinite loops, or freeze in deadlocks when branches merge.
* **Why Cortex succeeds:** Cortex uses a **Token-Passing Traversal Engine** (inspired by Petri nets and Kahn’s Algorithm). A node only fires when it has collected all required tokens from its incoming dependencies. When a condition skips a branch, it emits **Ghost Tokens** so downstream joining nodes never get stuck waiting. It handles loops and non-linear paths seamlessly without deep recursion.

### 2. Built-in LLM Reasoning & Self-Healing (The "Brain")
Standard automation breaks when a UI element moves or changes style. Cortex integrates Large Language Models (LLMs) and Vision-Language Models (VLMs) directly into the execution flow:
* **Dynamic Decision Making:** Route execution conditionally based on an AI's semantic understanding of screen text or pop-ups.
* **Auto-Healing Vision:** If a button cannot be located via classic computer vision, Cortex takes a screenshot, prompts a Vision Model to identify the new location, clicks the target, and automatically crops and refreshes the template image in memory for future fast, zero-cost runs.

### 3. Computer Vision & Screen Perception (The "Eyes")
Modern web and desktop applications frequently update their internal DOM IDs and classes. Cortex bypasses DOM dependencies entirely by reading pixels:
* **Template Matching:** Finds UI icons, buttons, and custom controls via OpenCV pixel matching.
* **Optical Character Recognition (OCR):** Reads text directly off the screen across legacy apps, canvas apps, and Citrix/RDP streams.
* **Multi-Monitor & DPI Awareness:** Automatically handles virtual screen metrics and high-DPI scaling on multi-monitor setups.

### 4. Physical OS-Level Simulation (The "Hands")
Cortex does not rely on synthetic JavaScript events or headless browser APIs that trigger bot-detection shields:
* It simulates **real OS hardware events** (mouse clicks, drags, scrolls, keystrokes, modifier shortcuts, clipboard transfers).
* Inputs are indistinguishable from a physical user, making it ideal for automating protected desktop apps and web portals.

### 5. PyQt6 Visual Node Canvas (No-Code / Low-Code GUI)
Built with a sleek PyQt6 interface, Cortex lets both technical and non-technical users drag, drop, and wire together automation blocks:
* Real-time execution visualizer highlights nodes as they run.
* Dynamic property inspectors allow configuring delays, retries, prompts, and conditions effortlessly.

---

## Technical Jargon Explained (Simply!)

To understand why Cortex is architecturally powerful, here is a quick breakdown of key technical concepts explained in simple terms:

| Technical Jargon | What It Means | Simple Analogy / Intuition |
| :--- | :--- | :--- |
| **Node Graph** | A collection of action blocks (**Nodes**) connected by directional lines (**Edges**). | Like a flowchart where each box is a step (e.g., *Find Button* → *Click* → *Type Text*). |
| **DAG (Directed Acyclic Graph)** | A graph that flows forward in one direction without accidental infinite loops. | A one-way roadmap where every road moves you toward the destination. |
| **In-Degree** | The number of prerequisite incoming lines pointing into a specific node. | The number of people who must say *"I'm ready"* before a team meeting can begin. |
| **Token-Passing Traversal** | An execution method where nodes pass "tokens" (green signals) forward upon completion. | Like a relay race where a runner only sprints after receiving batons from all teammates. |
| **Ghost Tokens (Skip Tokens)** | A dummy signal sent down a skipped conditional branch (e.g., the *False* branch of an *If* condition). | Like sending an *"I won't be attending"* RSVP so the host knows not to wait for you. |
| **Back-Edges & DFS** | Lines in a graph that point backward to create intentional loops (e.g., *Retry 3 times* or *Loop over CSV rows*). | A roundabout in a roadmap that allows you to take another lap on purpose without getting lost. |
| **VLM (Vision-Language Model)** | An AI model that can understand both images and text (e.g., GPT-4o, Claude, Qwen-VL). | An AI with eyes that can look at a screenshot and answer *"Where is the blue submit button?"*. |
| **Self-Healing** | The ability of the automation to fix its own broken visual selectors on the fly. | A self-repairing car that fixes a loose part while driving so it doesn't break down tomorrow. |
| **Dependency Injection** | The engine automatically gives a function only the exact tools/variables it asks for. | A chef being handed only the knife and spices needed for the current dish. |
| **Runtime Context (`_context`)** | A shared memory dictionary where nodes store and read variables across steps. | A communal whiteboard where step 1 writes down an address so step 2 can read and navigate to it. |

---

## System Architecture & Visual Process Guide

> **Note for Contributors / Presenters:**  
> Use the structured visual placeholders below to insert architectural diagrams, workflow screenshots, and schematics when presenting or documenting the system.

### Visual Diagram Placeholders

#### Architecture Overview
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                        │
│                     [ PLACEHOLDER: SYSTEM ARCHITECTURE OVERVIEW ]                      │
│                                                                                        │
│   Recommended Graphic: 5-Tier Architecture Diagram                                     │
│   (Presentation UI ➔ Serialization ➔ Graph Data Model ➔ Runtime Engine ➔ OS Drivers)  │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
*Figure 1: High-Level Layered Architecture of Cortex.*

---

#### Graph Traversal & Token Lifecycle
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                        │
│                  [ PLACEHOLDER: TOKEN-PASSING GRAPH TRAVERSAL FLOW ]                   │
│                                                                                        │
│   Recommended Graphic: Petri-Net Token Queue & Diamond Convergence                     │
│   (Active Tokens vs Ghost Skip Tokens resolving joining nodes without deadlocks)       │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
*Figure 2: Token-Passing Traversal Mechanism with Ghost Token Propagation.*

---

#### Perception & Self-Healing Subsystem
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                        │
│               [ PLACEHOLDER: COMPUTER VISION & SELF-HEALING VLM PIPELINE ]             │
│                                                                                        │
│   Recommended Graphic: Dual-Tier Vision & Auto-Healing Flowchart                       │
│   (Screen Grab ➔ OpenCV Match ➔ Fallback to VLM ➔ Bounding Box ➔ Auto-Crop & Save)     │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
*Figure 3: Dual-Tier Vision Pipeline with Autonomous Template Auto-Healing.*

---

## End-to-End Execution Process (How It Works in Our Current Setup)

Here is the exact step-by-step breakdown of how a `.cortex` workflow is loaded, analyzed, traversed, and executed on the physical operating system:

```
 ┌─────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
 │ 1. Load & Parse │ ───► │ 2. Topology Analysis    │ ───► │ 3. Token-Passing Loop   │
 │ YAML ➔ Pydantic │      │ In-Degree & Back-Edges  │      │ Queue & Ghost Tokens    │
 └─────────────────┘      └─────────────────────────┘      └────────────┬────────────┘
                                                                        │
 ┌─────────────────┐      ┌─────────────────────────┐                   │
 │ 6. UI Sync      │ ◄─── │ 5. Perception & Action  │ ◄─────────────────┘
 │ Qt Event Bus    │      │ OpenCV / VLM / PyAutoGUI│      4. Dispatch & DI
 └─────────────────┘      └─────────────────────────┘      Registry + Context
```

### Phase 1: Workflow Loading & Deserialization
1. **File Reading (`cortex/serializer/file_io/load.py`):** The user loads a `.cortex` file, which is a structured YAML document containing graph metadata, LLM configurations, nodes, and edges.
2. **Polymorphic Model Instantiation (`parse_nodes`):** Cortex uses Pydantic V2. A custom validator inspects the `_type` property of every node (e.g., `LocateElementNode`, `MouseNode`, `BranchNode`) and instantiates the exact strongly-typed Python class.
3. **Graph Integrity Check:** Before running, `ActionGraph.validate_graph_integrity` checks that all edge endpoints exist, verifies that the entry node is valid, and checks graph connectivity using `networkx`.

### Phase 2: Topology Preparation & Back-Edge Discovery
1. **DFS Back-Edge Detection (`execution_graph.py`):** To allow user-defined loops (like retrying a block 5 times or iterating through rows) without infinite recursion, Cortex runs a Depth-First Search (DFS) to identify **back-edges** (edges that loop back up the graph).
2. **Forward In-Degree Calculation:** Cortex counts how many forward incoming edges each node has. Back-edges are excluded from this initial count so the starting nodes can be identified.
3. **Queue Initialization:** All root nodes with an in-degree of `0` (including `GlobalStartNode`) are placed into the execution queue.

### Phase 3: The Token-Passing Execution Loop (`execution.py`)
1. **Token Accumulation:** As the queue processes nodes, it tracks how many tokens each node has collected (`node_tokens[node_id]`).
2. **Firing Condition:** A node only executes when:
   $$\text{Tokens Received} = \text{Forward In-Degree}$$
   and at least one of those tokens is an active execution request (`node_exec_requests > 0`).
3. **Resolving Diamond Deadlocks with Ghost Tokens:** If a `BranchNode` evaluates to *True*, it sends an active `True` token down the *True* branch, but sends a **Ghost Token** (`False`) down the *False* branch. When the two paths converge at a downstream join node, the join node receives all its expected tokens without hanging or executing twice.
4. **Iterative Loop Handling:** When a loop node finishes an iteration and pushes across a back-edge, the engine temporarily resets that target node's token count, enabling iterative loops safely in a flat loop structure.
5. **State Interruption & FailSafe:** Between node dispatches, the engine checks `_paused` and `_abort` flags. If the user clicks "Pause", the thread sleeps in non-blocking 100ms intervals. If the user rams the mouse cursor into a screen corner, the `pyautogui.FailSafeException` is caught immediately, cleanly halting execution.

### Phase 4: Dynamic Dispatch & Dependency Injection (`dispatch.py`)
1. **Decoupled Registry (`registry.py`):** The node data models do not contain execution code. The engine looks up the node's class in `EXECUTOR_REGISTRY` to find its matching executor function.
2. **Signature Introspection:** The engine uses Python’s `inspect.signature` to check what arguments the executor function requires. It dynamically injects only the requested dependencies:
   - `node`: The strongly-typed Pydantic model.
   - `_context`: The global shared runtime context.
   - `abort_signal`: A callable lambda checking if the user requested an emergency stop.
   - `emit_info`: A logging callback to stream live updates to the UI.
   - `llm_config`: Global API keys and AI model preferences.
3. **Automatic Retries & Error Edges:** If an executor fails, Cortex checks the node's `retry_count` and `retry_delay`. If all retries are exhausted, it checks for an outgoing edge labeled `error` (allowing visual Try/Catch flows). If no error path exists, it obeys the `on_error` rule (`stop` or `continue`).

### Phase 5: Perception, AI Reasoning & Physical Execution
* **Vision (`locate_core.py`):** Captures multi-monitor desktop screenshots, crops to defined Regions of Interest (ROI), and matches templates using OpenCV.
* **Self-Healing Fallback (`locate_fallback.py`):** If template matching times out, Cortex sends the screenshot and a natural-language description (e.g., *"Find the orange Submit button"*) to a Multimodal VLM. The VLM returns coordinates, and if `auto_heal` is enabled, Cortex crops the new visual element and updates the node's template in memory.
* **Physical Actions (`mouse.py`, `keyboard.py`, `clipboard.py`):** Translates logical coordinates and strings into native OS clicks, drags, scrolls, typing, and clipboard pastes.
* **Context Mutation:** When a node finishes, its return value is stored in `_context[node.output_key]`, making it immediately accessible to downstream nodes (with support for Jinja2 template interpolation like `Hello {{ extracted_name }}`).

### Phase 6: Telemetry & Real-Time GUI Sync
* The background worker thread communicates with the PyQt6 main thread via Qt Signals (`NODE_STARTED`, `NODE_COMPLETED`, `LOG_EMITTED`, `GRAPH_COMPLETE`).
* The UI canvas illuminates active nodes in real time, displays live logs, and updates property inspectors without freezing the interface.

---

## Node Categories Overview

Cortex provides a rich library of pre-built nodes categorized into four functional groups:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 CORTEX NODE LIBRARY                                    │
├───────────────────┬───────────────────┬───────────────────────┬────────────────────────┤
│   Flow Control    │ Physical Actions  │ Vision & Perception   │ AI & Cognitive         │
├───────────────────┼───────────────────┼───────────────────────┼────────────────────────┤
│ Global Start / End│ Mouse Move/Click  │ Locate Element        │ LLM Prompt / Reasoning │
│ Branch (If/Else)  │ Keyboard Type     │ Locate & Click        │ VLM Visual Fallback    │
│ Compare Condition │ Shortcut / Hotkey │ Screen OCR (Text)     │ Structured JSON Extract│
│ For / Iterate Loop│ Drag & Drop       │ Screenshot Capture    │ Auto-Heal Refresher    │
│ CSV Read / Write  │ Clipboard I/O     │ Multi-Region Crop     │ Natural Language Logic │
└───────────────────┴───────────────────┴───────────────────────┴────────────────────────┤
```

1. **Flow Nodes (`cortex.nodes.executors.flow`)**: Orchestrate branching logic, loops, delays, file reading/writing, and CSV data processing.
2. **Physical Nodes (`cortex.nodes.executors.physical_components`)**: Perform native mouse actions, keystrokes, clipboard manipulation, and OS file dropping.
3. **Vision Nodes (`cortex.nodes.executors.vision_components`)**: Locate images, recognize on-screen text via OCR, and handle multi-monitor DPI scaling.
4. **LLM Nodes (`cortex.nodes.executors.llm`)**: Provide AI-driven reasoning, semantic judgment, screen interpretation, and autonomous error recovery.

---

## Prerequisites

* **Python:** Version `3.11` or higher
* **Operating System:** Windows 10/11, macOS, or Linux
* **LLM API Key (Optional):** OpenAI, OpenRouter, or compatible API keys for cognitive and self-healing features.

---

## Installation

1. **Clone the repository and set up a virtual environment:**
   ```bash
   git clone https://github.com/mrityunjay-jha117/automator.git cortex
   cd cortex
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   # macOS / Linux:
   source venv/bin/activate
   ```

2. **Install dependencies in editable mode:**
   ```bash
   pip install -e .
   ```
   *(To install testing and linting tools: `pip install -e .[dev]`)*

3. **Configure Environment Variables:**  
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

---

## Running Cortex

To launch the visual node editor:

```bash
# Via python module
python -m cortex

# Or via installed console script
cortex
```

From the GUI, you can:
- Drag and drop nodes from the library or right-click radial menu.
- Connect input and output ports to build your automation graph.
- Configure properties and test individual nodes in real time.
- Click **Run** to execute the automation with live visual feedback.
- Save and load `.cortex` workflow files anytime.

---

<!-- GOAL_COMPLETE -->
