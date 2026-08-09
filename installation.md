## Prerequisites

- Python 3.11 or higher
- An OpenAI API Key (or compatible LLM provider) if using LLM nodes (optional)

## Installation

1. **Create a virtual environment (recommended)**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  
   ```

2. **Install the package and its dependencies**:
   ```bash
   pip install -e .
   ```
   _(To install development dependencies like `pytest` and `mypy`, use `pip install -e .[dev]`)_

3. **Environment Setup**:

   Create a `.env` file in the root directory based on your requirements (e.g., setting your `OPENAI_API_KEY`).

   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

To launch the Cortex GUI and start building your automation flows:

```bash
python -m cortex
```

From the GUI, you can drag and drop nodes, connect their inputs and outputs, configure their properties, and execute the graph.
