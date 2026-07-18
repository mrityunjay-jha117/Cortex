# Cognitive Automator — Project Guidelines

Welcome to the Cognitive Automator project. This document outlines the architectural principles, coding standards, and workflows used in this codebase.

##  Project Overview

Cognitive Automator is an LLM-powered Windows automation framework. It bridges the gap between traditional "brute force" RPA (mouse/keyboard/vision) and modern AI, allowing for adaptive, intelligent workflows.

##  Core Architecture

- **Graph-Based Execution:** Automations are DAGs (Directed Acyclic Graphs) managed by `NetworkX` and validated by `Pydantic`.
- **OpenRouter First:** We use OpenRouter as a unified interface for all LLM calls (OpenAI, Anthropic, Gemini, etc.).
- **AI Fallback for Vision:** When traditional image matching fails, we fallback to Vision LLMs to locate elements and "auto-heal" the automation.
- **PyQt6 GUI:** A professional-grade node editor for building and visualizing workflows.

##  Development Standards

### Python & Types
- **Version:** Python 3.11+
- **Typing:** Use strict type hints everywhere.
- **Validation:** Use Pydantic v2 for all data models (see `graph_model.py`).

### Style & Linting
- **Ruff:** Used for linting and formatting. Line length is 100.
- **Mypy:** Used for static type checking. Always run `mypy .` before committing.
- **Conventions:** Follow PEP 8. Use descriptive variable names and document complex logic.

### Testing
- **Framework:** `pytest`
- **Coverage:** Aim for high coverage, especially in `runtime/` and `nodes/`.
- **Reproducibility:** Before fixing a bug, create a reproduction test case.

##  Key Workflows

### Adding a New Node Type
1. Define the node model in `cognitive_automator/graph_model.py`.
2. Implement the execution logic in `cognitive_automator/nodes/executors.py`.
3. (Optional) Add a custom property widget in `cognitive_automator/gui/panels/property_panel.py` if the default doesn't suffice.

### Modifying LLM Logic
- All LLM client logic lives in `cognitive_automator/llm/client.py`.
- Prompt templates are in `cognitive_automator/llm/templates.py`.

##  Build & Release
- Use `build.bat` for Windows builds.
- Ensure `version_info.txt` is updated before a release.
- Installer is generated via Inno Setup 6 using `CognitiveAutomator_Setup.iss`.
