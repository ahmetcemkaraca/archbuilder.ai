from __future__ import annotations

"""
Prompt renderer based on Jinja2.
"""

from typing import Any, Mapping

from jinja2 import Environment, StrictUndefined

from ..interfaces import PromptRenderResult, PromptRenderer


class JinjaPromptRenderer(PromptRenderer):
    def __init__(self) -> None:
        # Varsayılan olarak StrictUndefined, eksik alanları erken yakalar
        self.env = Environment(undefined=StrictUndefined, autoescape=False, trim_blocks=True, lstrip_blocks=True)

    def render(self, template_text: str, context: Mapping[str, Any]) -> PromptRenderResult:
        template = self.env.from_string(template_text)
        text = template.render(**dict(context))
        return PromptRenderResult(prompt_text=text, metadata={"engine": "jinja2", "context_keys": list(context.keys())})


