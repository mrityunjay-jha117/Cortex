"""
=============================================================================
 LLM TEMPLATES
=============================================================================
This module stores the standard prompt templates used across the application.
It provides f-string compatible skeletons for dynamically injecting context.

Key Features:
1. Centralizes hardcoded prompts for extraction, reasoning, and judgment.
2. Ensures consistency in how the system speaks to the LLMs.

Think of this module as the recipe book for talking to artificial intelligence.
=============================================================================
"""

from __future__ import annotations

from typing import Any

from jinja2 import Environment, StrictUndefined, TemplateError, UndefinedError
# StrictUndefined is for hard check agar nhi available toh undefined
_env = Environment(undefined=StrictUndefined)

import re
import functools

# Naam ke aage underscore (_) kyun hai?
# Python me underscore ka matlab hota hai
# Ye internal helper function hai.
# Matlab Is function ko file ke bahar se use mat karo.
# sub->substitute
# re.sub(
#     pattern,
#     replacement,
#     string
# )
def _preprocess(template_str: str) -> str:
    """Convert ${var} to {{var}} for Jinja2 compatibility."""
    return re.sub(r"\$\{(.+?)\}", r"{{\1}}", template_str)
"""
 Decorator ek function hota hai jo dusre function ke behavior 
 ko modify karta hai bina us function ka code badle.
 jinja2 is used for the template manipulation
Asli expensive kaam ye hai
_env.from_string(processed_template)
Ye sirf string return nahi karta.
Ye template ko compile karta hai.
Socho tumhare paas template hai:
Hello {{name}}
Your age is {{age}}
Your city is {{city}}
Jinja2 ko ye kaam karna padta hai:
Step 1
Template ko character by character read karo.
H
e
l
l
o
{
{
name
}
}
Step 2
Samjho
Hello normal text hai.
Aur
{{name}}
ek variable hai.
Step 3
Internal object banao.
Jinja2 internally kuch aisa banata hai (conceptually):
[
    Text("Hello "),
    Variable("name"),
    Text("\nYour age is "),
    Variable("age"),
    Text("\nYour city is "),
    Variable("city")
]
Ye object baad me render hota hai.
Ye parsing aur compilation har baar karna padta agar cache na ho.
ye conversion ka kaam jinja mein specifically from_String ka hai
"""

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
        # this unpacks the context dictionary and gives to template to render
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
