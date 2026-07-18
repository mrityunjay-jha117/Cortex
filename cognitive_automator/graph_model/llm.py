from typing import Literal, Any
from pydantic import BaseModel, Field
from .enums import NodeCategory, LLMProvider
from .base import BaseNode

class LLMJudgmentNode(BaseNode):
    category: Literal[NodeCategory.LLM] = NodeCategory.LLM
    prompt_template: str = ""
    system_prompt: str = "You are a precise classification assistant. Always respond with valid JSON only."
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "qwen/qwen-2.5-72b-instruct"
    temperature: float = 0.0
    max_tokens: int = 256
    input_context_keys: list[str] = Field(default_factory=list)
    image_context_keys: list[str] = Field(default_factory=list)

class LLMExtractionNode(BaseNode):
    category: Literal[NodeCategory.LLM] = NodeCategory.LLM
    prompt_template: str = ""
    system_prompt: str = "Extract the requested information as valid JSON."
    output_schema: dict[str, Any] = Field(default_factory=dict)
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "qwen/qwen-2.5-72b-instruct"
    temperature: float = 0.0
    max_tokens: int = 2048
    input_context_keys: list[str] = Field(default_factory=list)
    image_context_keys: list[str] = Field(default_factory=list)
    output_key: str = "extracted_data"

class LLMGenerativeNode(BaseNode):
    category: Literal[NodeCategory.LLM] = NodeCategory.LLM
    prompt_template: str = ""
    system_prompt: str = "You are a helpful writing assistant."
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "openai/gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2048
    input_context_keys: list[str] = Field(default_factory=list)
    output_key: str = "generated_text"
