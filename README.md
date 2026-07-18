# Cognitive Automator

**LLM-Powered Windows Automation Framework** — v1.0.0

Combines PyAutoGUI physical automation (mouse, keyboard, vision) with Large Language Models for intelligent, adaptive workflows.

---

## Quick Start

### Prerequisites

- **Windows 10 / 11** (64-bit)
- **Python 3.11+**
- **OpenRouter API key** (Unified provider for all LLMs)

### Install & Run (Development)

```bash
git clone https://github.com/your-org/cognitive-automator
cd cognitive-automator

# Install dependencies
pip install -e ".[dev]"

# Set your API key in a .env file or environment variable
echo OPENROUTER_API_KEY=sk-or-v1-... > .env

# Launch the application
cognitive-automator
# OR
python -m cognitive_automator
```

### Build the EXE

```bash
# Builds dist/CognitiveAutomator.exe
# If Inno Setup 6 is installed, also builds Output/CognitiveAutomator-Setup-1.0.0.exe
build.bat

# Build EXE only, skipping installer
build.bat --skip-installer
```

---

## Usage

### Advanced Vision: AI Fallback

`LocateElementNode` includes an intelligent fallback mechanism. If standard image matching fails:
1. It captures a screenshot.
2. Sends it to a Vision LLM (via OpenRouter).
3. The LLM identifies the element and returns normalized coordinates.
4. The system converts these to physical pixels and performs the action.
5. If **Auto-Heal** is enabled, it crops the new area and updates the reference image for future runs.

### Adding Nodes Manually

Use **Edit → Add Node → [Category]** to add any node type to the canvas.

### Saving Automations

Automations save as `.cogauto` files (YAML format, human-readable and VCS-friendly).

---

## Node Types

| Category | Node | Description |
|---|---|---|
| Physical IO | MouseNode | Click, double-click, right-click, move, drag |
| Physical IO | KeyboardNode | Typewrite text, press key, hotkeys |
| Physical IO | ClipboardNode | Read/write OS clipboard |
| Vision | LocateElementNode | Find UI element by reference image (pyautogui) |
| Vision | GenerativeOCRNode | Extract screen text via Vision LLM |
| LLM Logic | LLMJudgmentNode | Boolean True/False routing |
| LLM Logic | LLMExtractionNode | Extract structured JSON from text |
| LLM Logic | LLMGenerativeNode | Generate text to type |
| Flow | WaitNode | Static delay or wait for element |
| Flow | BranchNode | Route based on boolean context key |
| Flow | IterateNode | Loop over CSV file or list |
| Flow | SubGraphNode | Embed a nested automation |

---

## Prompt Templates

Use `{{variable}}` in prompt templates to inject values from the execution context:

```
Analyze the following text: {{clipboard}}
Is this related to stock prices? Return YES or NO.
```

Available context keys vary by workflow. Common keys: `clipboard`, `ocr_text`, `loop_item`, `located_xy`.

---

## LLM Provider

Cognitive Automator uses **OpenRouter** as the sole, provider-agnostic LLM interface.

| Environment Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter API key |

Specify models in the node properties using OpenRouter IDs (e.g., `openai/gpt-4o`, `anthropic/claude-3.5-sonnet`, `qwen/qwen-2.5-72b-instruct`).

---

## Safety

- **PyAutoGUI FAILSAFE** is always active: move the mouse to the **top-left corner** of the screen to immediately abort any running automation.
- The EXE does **not** require administrator privileges.
- LLM API keys are read from environment variables or a `.env` file — never stored in `.cogauto` files.

---

## Architecture

```
cognitive_automator/
├── main.py             ← Application entry point & .env loader
├── graph_model.py      ← Pydantic v2 node models + NetworkX DAG
├── serializer.py       ← JSON/YAML codec
├── nodes/
│   └── executors.py    ← Per-node execution logic (including AI Fallback)
├── llm/
│   ├── client.py       ← OpenRouter client adapter
│   ├── structured.py   ← Judgment / Extraction / OCR runners
│   └── templates.py    ← Jinja2 prompt engine
├── recorder/
│   ├── hooker.py       ← pynput OS event listener
│   └── translator.py   ← Events → graph nodes
├── runtime/
│   └── executor.py     ← Graph walker + retry + error edges
└── gui/
    ├── main_window.py   ← Main window + menus + toolbars
    ├── canvas.py        ← PyQt6 QGraphicsScene/View node editor
    ├── constants.py     ← Colors + stylesheet
    ├── panels/
    │   ├── property_panel.py
    │   └── log_panel.py
    └── widgets/
        ├── recording_overlay.py
        └── logic_inject_dialog.py
```

---

## Running Tests

```bash
pytest tests/ -v --cov=cognitive_automator --cov-report=term-missing
```

---

## License

MIT — see LICENSE.txt
