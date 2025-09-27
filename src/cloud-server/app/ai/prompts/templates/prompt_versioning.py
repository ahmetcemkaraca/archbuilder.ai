from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PromptTemplate:
    version: str
    system: str
    user_template: str

    def format(self, **kwargs) -> str:
        return self.user_template.format(**kwargs)


class PromptRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, Dict[str, PromptTemplate]] = {}
        self._active: Dict[str, str] = {}

    def register(self, name: str, template: PromptTemplate) -> None:
        self._registry.setdefault(name, {})[template.version] = template
        self._active.setdefault(name, template.version)

    def set_active(self, name: str, version: str) -> None:
        if name not in self._registry or version not in self._registry[name]:
            raise KeyError("prompt version not found")
        self._active[name] = version

    def get(self, name: str) -> PromptTemplate:
        ver = self._active.get(name)
        if not ver:
            raise KeyError("prompt not registered")
        return self._registry[name][ver]


# Defaults (v1)
layout_v1 = PromptTemplate(
    version="v1",
    system="You are an architect.",
    user_template=(
        "Generate layout JSON for building_type={building_type} total_area={total_area_m2}m2 "
        "with rooms={rooms}."
    ),
)

registry = PromptRegistry()
registry.register("layout_generation", layout_v1)
