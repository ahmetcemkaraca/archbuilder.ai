from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4

from app.database.session import AsyncSession
from app.ai.model_selector import ModelSelector
from app.ai.prompts.templates.prompt_versioning import registry as prompt_registry
from app.ai.interfaces import OpenAIClient, VertexClient, AIClient
from app.database.models.ai_command import AICommand


class AIService:
    def __init__(self) -> None:
        self._selector = ModelSelector()
        self._openai: AIClient = OpenAIClient()
        self._vertex: AIClient = VertexClient()

    async def create_command(
        self,
        db: AsyncSession,
        command: str,
        input_data: Dict[str, Any],
        user_id: Optional[str],
        project_id: Optional[str],
    ) -> Dict[str, Any]:
        # TR: Basit model seçimi (dil/karmaşıklık ipuçlarına göre)
        language = (
            (input_data.get("language") or "en")
            if isinstance(input_data, dict)
            else "en"
        )
        complexity = (
            (input_data.get("complexity") or "simple")
            if isinstance(input_data, dict)
            else "simple"
        )
        model = self._selector.select(language=language, complexity=complexity)

        # TR: Prompt versiyonlama ile giriş verisini normalize et
        try:
            tmpl = prompt_registry.get("layout_generation")
            prompt = tmpl.format(
                building_type=input_data.get("building_type", "residential"),
                total_area_m2=input_data.get("total_area_m2", 50),
                rooms=(
                    ",".join(input_data.get("rooms", []))
                    if isinstance(input_data.get("rooms"), list)
                    else str(input_data.get("rooms", ""))
                ),
            )
        except Exception:
            prompt = None

        # TR: (Opsiyonel) AI çağrısı — stub clientlerle prompt önizlemesi
        ai_preview: Dict[str, Any] | None = None
        try:
            if prompt and model["provider"] == "openai":
                ai_preview = await self._openai.generate(prompt, model=model["model"])
            elif prompt and model["provider"] == "vertex":
                ai_preview = await self._vertex.generate(prompt, model=model["model"])
        except Exception:
            ai_preview = None

        item = AICommand(
            id=str(uuid4()),
            user_id=user_id,
            project_id=project_id,
            command=command,
            input=input_data,
            output={"selectedModel": model, "prompt": prompt, "preview": ai_preview},
        )
        db.add(item)
        await db.flush()
        return {
            "id": item.id,
            "created_at": item.created_at.isoformat(),
            "selected_model": model,
        }

    async def get_command(self, db: AsyncSession, id_: str) -> Dict[str, Any] | None:
        res = await db.get(AICommand, id_)
        if not res:
            return None
        return {
            "id": res.id,
            "user_id": res.user_id,
            "project_id": res.project_id,
            "command": res.command,
            "input": res.input,
            "output": res.output,
            "created_at": res.created_at.isoformat(),
        }
