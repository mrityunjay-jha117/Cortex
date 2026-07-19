"""
llm/templates.py — Jinja2-based prompt template engine.

Variables injected from the execution context dict.
Undefined variables raise an error at render time (fail fast).
"""

from __future__ import annotations

from typing import Any

from jinja2 import Environment, StrictUndefined, TemplateError, UndefinedError


_env = Environment(undefined=StrictUndefined)

import re
import functools

def _preprocess(template_str: str) -> str:
    """Convert ${var} to {{var}} for Jinja2 compatibility."""
    return re.sub(r"\$\{(.+?)\}", r"{{\1}}", template_str)

@functools.lru_cache(maxsize=256)
def _get_template(template_str: str):
    processed_template = _preprocess(template_str)
    return _env.from_string(processed_template)

def render_prompt(template_str: str, context: dict[str, Any]) -> str:
    """
    Render a prompt template with the given context.
    Supports both ${variable} and {{variable}} syntax.
    Raises TemplateRenderError if any variable is undefined.
    """
    if not template_str:
        return ""
    
    try:
        template = _get_template(template_str)
        return template.render(**context)
    except UndefinedError as exc:
        raise TemplateRenderError(
            f"Prompt template references an undefined variable: {exc}. "
            f"Available keys: {list(context.keys())}"
        ) from exc
    except TemplateError as exc:
        raise TemplateRenderError(f"Prompt template syntax error: {exc}") from exc


def validate_template(template_str: str) -> list[str]:
    """
    Parse a template and return a list of variable names it references.
    Used by the GUI to warn the user about missing context keys before execution.
    """
    processed = _preprocess(template_str)
    try:
        ast = _env.parse(processed)
    except TemplateError:
        return []
    from jinja2 import meta  # type: ignore
    return sorted(meta.find_undeclared_variables(ast))


class TemplateRenderError(RuntimeError):
    pass
