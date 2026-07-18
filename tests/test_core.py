"""
tests/test_graph_model.py — Unit tests for the core graph model.

Run with: pytest tests/ -v --tb=short
"""

from __future__ import annotations

import os
import tempfile

import pytest

from cognitive_automator.graph_model import (
    ActionGraph, BranchNode, ClipboardAction, ClipboardNode, EdgeLabel,
    IterateNode, KeyboardAction, KeyboardNode, LLMJudgmentNode,
    MouseNode, WaitNode,
)
from cognitive_automator.serializer import (
    load_graph, new_graph, save_graph, graph_to_json_str, graph_from_json_str,
)
from cognitive_automator.nodes.executors import (
    execute_clipboard, execute_keyboard, execute_branch,
    execute_wait, execute_iterate,
)
from cognitive_automator.llm.templates import render_prompt, validate_template


# ---------------------------------------------------------------------------
# Graph model tests
# ---------------------------------------------------------------------------

class TestGraphModel:
    def test_add_node_sets_entry(self) -> None:
        graph = new_graph()
        n = MouseNode(label="click")
        graph.add_node(n)
        assert graph.entry_node_id == n.id
        assert n.id in graph.nodes

    def test_remove_node_cleans_edges(self) -> None:
        graph = new_graph()
        n1 = MouseNode(label="A")
        n2 = KeyboardNode(label="B")
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_edge(n1.id, n2.id)
        assert len(graph.edges) == 1
        graph.remove_node(n1.id)
        assert len(graph.edges) == 0
        assert n1.id not in graph.nodes

    def test_duplicate_node(self) -> None:
        graph = new_graph()
        n1 = MouseNode(label="Original", x_coord=100, y_coord=200, x=10, y=20)
        graph.add_node(n1)
        
        new_id = graph.duplicate_node(n1.id)
        assert new_id is not None
        assert new_id != n1.id
        
        n2 = graph.nodes[new_id]
        assert n2.label == "Original"
        assert n2.x_coord == 100
        assert n2.y_coord == 200
        assert n2.x == 50  # 10 + 40
        assert n2.y == 60  # 20 + 40
        assert isinstance(n2, MouseNode)

    def test_cycle_detection_raises(self) -> None:
        """A cycle that isn't loop-body/loop-end should raise at validation."""
        graph = new_graph()
        n1 = MouseNode(label="A")
        n2 = MouseNode(label="B")
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_edge(n1.id, n2.id)
        graph.add_edge(n2.id, n1.id)
        with pytest.raises(Exception):
            # Re-run validation
            ActionGraph(**graph.model_dump_with_types())

    def test_edge_unknown_node_raises(self) -> None:
        graph = new_graph()
        n1 = MouseNode()
        graph.add_node(n1)
        graph.edges.append(
            __import__("cognitive_automator.graph_model", fromlist=["GraphEdge"]).GraphEdge(
                source_id=n1.id, target_id="nonexistent"
            )
        )
        with pytest.raises(Exception):
            ActionGraph(**graph.model_dump_with_types())


# ---------------------------------------------------------------------------
# Serialization tests
# ---------------------------------------------------------------------------

class TestSerialization:
    def _make_graph(self) -> ActionGraph:
        graph = new_graph("Test Graph")
        n1 = MouseNode(label="Click Sign In", x_coord=100, y_coord=200)
        n2 = KeyboardNode(label="Type Password", action=KeyboardAction.TYPEWRITE, text="secret")
        n3 = LLMJudgmentNode(label="Check Result", prompt_template="Is {{clipboard}} valid? YES/NO")
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        graph.add_edge(n1.id, n2.id)
        graph.add_edge(n2.id, n3.id, EdgeLabel.DEFAULT)
        graph.add_edge(n3.id, n1.id, EdgeLabel.TRUE)   # intentional true-loop via valid edge
        return graph

    def test_json_round_trip(self) -> None:
        graph = self._make_graph()
        json_str = graph_to_json_str(graph)
        restored = graph_from_json_str(json_str)
        assert restored.metadata.name == graph.metadata.name
        assert len(restored.nodes) == len(graph.nodes)
        assert len(restored.edges) == len(graph.edges)

    def test_yaml_file_round_trip(self) -> None:
        graph = self._make_graph()
        with tempfile.NamedTemporaryFile(suffix=".cogauto", delete=False) as f:
            path = f.name
        try:
            save_graph(graph, path)
            restored = load_graph(path)
            assert restored.metadata.name == graph.metadata.name
            assert set(restored.nodes.keys()) == set(graph.nodes.keys())
        finally:
            os.unlink(path)

    def test_json_file_round_trip(self) -> None:
        graph = self._make_graph()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_graph(graph, path)
            restored = load_graph(path)
            assert len(restored.nodes) == 3
        finally:
            os.unlink(path)

    def test_node_types_preserved(self) -> None:
        graph = self._make_graph()
        json_str = graph_to_json_str(graph)
        restored = graph_from_json_str(json_str)
        node_types = {type(n).__name__ for n in restored.nodes.values()}
        assert "MouseNode" in node_types
        assert "KeyboardNode" in node_types
        assert "LLMJudgmentNode" in node_types


# ---------------------------------------------------------------------------
# Executor tests (with mocked pyautogui)
# ---------------------------------------------------------------------------

class TestExecutors:
    def test_clipboard_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("pyperclip.paste", lambda: "test clipboard content")
        node = ClipboardNode(action=ClipboardAction.READ)
        result = execute_clipboard(node, {})
        assert result.success
        assert result.output_key == "clipboard"
        assert result.output_value == "test clipboard content"

    def test_clipboard_write(self, monkeypatch: pytest.MonkeyPatch) -> None:
        written = []
        monkeypatch.setattr("pyperclip.copy", lambda t: written.append(t))
        node = ClipboardNode(action=ClipboardAction.WRITE, write_text="hello world")
        result = execute_clipboard(node, {})
        assert result.success
        assert written == ["hello world"]

    def test_clipboard_write_from_context(self, monkeypatch: pytest.MonkeyPatch) -> None:
        written = []
        monkeypatch.setattr("pyperclip.copy", lambda t: written.append(t))
        node = ClipboardNode(action=ClipboardAction.WRITE, source_output_key="gen_text")
        result = execute_clipboard(node, {"gen_text": "generated content"})
        assert result.success
        assert written == ["generated content"]

    def test_branch_true(self) -> None:
        node = BranchNode(condition_key="judgment_result")
        result = execute_branch(node, {"judgment_result": True})
        assert result.success
        assert result.next_edge == EdgeLabel.TRUE

    def test_branch_false(self) -> None:
        node = BranchNode(condition_key="my_flag")
        result = execute_branch(node, {"my_flag": False})
        assert result.success
        assert result.next_edge == EdgeLabel.FALSE

    def test_branch_dict_result(self) -> None:
        """BranchNode should handle LLMJudgmentNode's dict output."""
        node = BranchNode(condition_key="judgment_result")
        result = execute_branch(node, {"judgment_result": {"result": True, "confidence": 0.9}})
        assert result.next_edge == EdgeLabel.TRUE

    def test_branch_missing_key(self) -> None:
        node = BranchNode(condition_key="nonexistent")
        result = execute_branch(node, {})
        assert not result.success

    def test_keyboard_typewrite_jinja2(self, monkeypatch: pytest.MonkeyPatch) -> None:
        typed = []
        monkeypatch.setattr("pyautogui.typewrite", lambda t, interval: typed.append(t))
        node = KeyboardNode(action=KeyboardAction.TYPEWRITE, text="Hello {{user}}!")
        result = execute_keyboard(node, {"user": "Gemini"})
        assert result.success
        assert typed == ["Hello Gemini!"]

    def test_keyboard_paste(self, monkeypatch: pytest.MonkeyPatch) -> None:
        copied = []
        hotkeys = []
        monkeypatch.setattr("pyperclip.copy", lambda t: copied.append(t))
        monkeypatch.setattr("pyautogui.hotkey", lambda *keys: hotkeys.append(keys))
        
        node = KeyboardNode(action=KeyboardAction.PASTE, text="Fast {{text}}")
        result = execute_keyboard(node, {"text": "Pasting"})
        
        assert result.success
        assert copied == ["Fast Pasting"]
        import sys
        modifier = "command" if sys.platform == "darwin" else "ctrl"
        assert hotkeys == [(modifier, "v")]

    def test_keyboard_select_all(self, monkeypatch: pytest.MonkeyPatch) -> None:
        hotkeys = []
        monkeypatch.setattr("pyautogui.hotkey", lambda *keys: hotkeys.append(keys))
        
        node = KeyboardNode(action=KeyboardAction.SELECT_ALL)
        result = execute_keyboard(node, {})
        
        assert result.success
        import sys
        modifier = "command" if sys.platform == "darwin" else "ctrl"
        assert hotkeys == [(modifier, "a")]

    def test_wait_static(self, monkeypatch: pytest.MonkeyPatch) -> None:
        slept = []
        monkeypatch.setattr("time.sleep", lambda s: slept.append(s))
        node = WaitNode(static_seconds=0.5)
        result = execute_wait(node, {})
        assert result.success
        assert sum(slept) == pytest.approx(0.5)

    def test_iterate_list(self) -> None:
        node = IterateNode(items=["apple", "banana", "cherry"], output_key="fruit")
        ctx: dict = {}
        # First call
        result = execute_iterate(node, ctx)
        assert result.success
        assert result.next_edge == EdgeLabel.LOOP_BODY
        assert result.output_value == "apple"
        # Second call
        result = execute_iterate(node, ctx)
        assert result.output_value == "banana"
        # Third call
        result = execute_iterate(node, ctx)
        assert result.output_value == "cherry"
        # Exhausted
        result = execute_iterate(node, ctx)
        assert result.next_edge == EdgeLabel.LOOP_END

    def test_iterate_empty(self) -> None:
        node = IterateNode(items=[], output_key="item")
        ctx: dict = {}
        result = execute_iterate(node, ctx)
        assert result.next_edge == EdgeLabel.LOOP_END


# ---------------------------------------------------------------------------
# Template tests
# ---------------------------------------------------------------------------

class TestTemplates:
    def test_basic_render(self) -> None:
        result = render_prompt("Hello {{name}}!", {"name": "World"})
        assert result == "Hello World!"

    def test_multiple_vars(self) -> None:
        result = render_prompt("{{a}} + {{b}} = {{c}}", {"a": 1, "b": 2, "c": 3})
        assert result == "1 + 2 = 3"

    def test_undefined_raises(self) -> None:
        from cognitive_automator.llm.templates import TemplateRenderError
        with pytest.raises(TemplateRenderError):
            render_prompt("Hello {{undefined_var}}!", {})

    def test_empty_template(self) -> None:
        assert render_prompt("", {}) == ""

    def test_validate_variables(self) -> None:
        variables = validate_template("Check {{clipboard}} and {{ocr_text}}")
        assert "clipboard" in variables
        assert "ocr_text" in variables

    def test_validate_empty(self) -> None:
        assert validate_template("") == []


# ---------------------------------------------------------------------------
# LLM structured output parsing tests
# ---------------------------------------------------------------------------

class TestJudgmentParsing:
    def test_valid_json(self) -> None:
        from cognitive_automator.llm.structured import _parse_judgment
        result = _parse_judgment('{"result": true, "confidence": 0.95, "reasoning": "yes"}')
        assert result["result"] is True
        assert result["confidence"] == 0.95

    def test_false_json(self) -> None:
        from cognitive_automator.llm.structured import _parse_judgment
        result = _parse_judgment('{"result": false, "confidence": 0.7, "reasoning": "no"}')
        assert result["result"] is False

    def test_fallback_yes(self) -> None:
        from cognitive_automator.llm.structured import _parse_judgment
        result = _parse_judgment("YES, this is related to stock prices.")
        assert result["result"] is True

    def test_fallback_no(self) -> None:
        from cognitive_automator.llm.structured import _parse_judgment
        result = _parse_judgment("NO - not relevant.")
        assert result["result"] is False

    def test_invalid_raises(self) -> None:
        from cognitive_automator.llm.structured import _parse_judgment
        with pytest.raises(ValueError):
            _parse_judgment("I cannot determine this from the context provided.")
