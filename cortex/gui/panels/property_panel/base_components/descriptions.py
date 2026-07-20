"""
=============================================================================
 DESCRIPTIONS.PY (base_components)
=============================================================================
This module is a microservice component for base_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cortex.graph_model import AnyNode

def get_node_desc(node: AnyNode) -> str:  # type: ignore[type-arg]
    descs = {
        "MouseNode": "Simulates physical mouse movements, clicks, and scrolling on the screen. Used to interact with elements at specific coordinates.",
        "KeyboardNode": "Simulates physical keyboard key presses and text typing. Useful for entering data into forms or triggering shortcuts.",
        "ClipboardNode": "Reads from or writes to the system clipboard. Allows copying text to paste elsewhere or extracting copied data.",
        "NavigatorNode": "Performs scrolling or focus actions, optionally centering the screen on a provided reference image. Helpful for navigating large pages.",
        "FileDropNode": "Simulates dragging and dropping a specific file into a target application or window to automate file uploads.",
        "ScreenshotterNode": "Captures screenshots of the screen. Can scroll and capture multiple pages, stitching them together if needed.",
        "CSVDataLoaderNode": "Loads data from a CSV file line by line to feed into the workflow. Great for batch processing tasks.",
        "WriteFileNode": "Writes or appends generated text or data into a local text file for logging or output generation.",
        "CSVWriterNode": "Appends structured row data into a CSV file. Useful for saving extracted information into a spreadsheet format.",
        "LocateElementNode": "Uses computer vision (template matching or AI) to find the screen coordinates of a reference image or text.",
        "LocateAndClickNode": "Finds a specific image or text on the screen using computer vision and immediately clicks its center point.",
        "GenerativeOCRNode": "Uses a Vision Language Model (VLM) to read and extract text from the screen or a specific region.",
        "VisionExtractionNode": "Uses a Vision Language Model to analyze the screen and extract structured data, like tables or JSON.",
        "LLMJudgmentNode": "Asks an LLM a yes/no question based on provided context. Used to make intelligent logical branching decisions.",
        "LLMExtractionNode": "Uses an LLM to parse unstructured text and extract specific data points into a structured JSON format.",
        "LLMGenerativeNode": "Uses an LLM to generate creative text, summarize content, or answer questions based on the provided prompt.",
        "BranchNode": "Routes the workflow execution down one of two paths based on a true/false condition or previous judgment.",
        "CompareNode": "Compares two variables (e.g., equals, greater than, contains) and outputs a boolean true/false result for branching.",
        "ForLoopNode": "Executes a sequence of connected nodes a specific number of times. Perfect for repetitive, fixed-count actions.",
        "IterateNode": "Loops over a list of items (like a CSV row or JSON array), running the connected nodes for each item.",
        "DynamicIterateNode": "Uses an LLM to dynamically determine how to iterate over unstructured context, handling complex repeating patterns intelligently.",
        "SubGraphNode": "Calls another saved automation workflow as a subroutine. Useful for modularizing and reusing common automation tasks.",
        "WaitNode": "Pauses the execution of the workflow for a specified number of seconds before continuing to the next node.",
        "GlobalStartNode": "The mandatory starting point of the automation workflow. Execution always begins from this node.",
        "GlobalEndNode": "The final endpoint of the automation workflow. Reaching this node terminates the current execution path gracefully."
    }
    return descs.get(type(node).__name__, "No description available for this node.")
