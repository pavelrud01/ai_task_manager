# workflow/steps/step_02a_guide_compile.py
from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, Any, Optional

from .base import BaseStep, StepResult
from utils.io import ensure_run_dir, save_md
from validators.standards_loader import resolve_guide_path, contracts_dir
from validators.validate import validate_with_schema_path
from llm.client import LLM


def _guide_json_to_markdown(guide: dict) -> str:
    meta = guide.get("meta", {}) or {}
    sec = guide.get("sections", {}) or {}

    # YAML front-matter
    fm = [
        "---",
        f"title: {meta.get('title','AJTBD Interview Guide')}",
        f"language: {meta.get('language','ru')}",
        f"audience: {meta.get('audience','B2C')}",
        f"goal: {meta.get('goal','')}",
        f"interview_mode: {meta.get('interview_mode','async')}",
        f"version: {meta.get('version','1.0')}",
        "---",
        ""
    ]

    out = []
    out.extend(fm)

    def add_h2(title: str, body: str = ""):
        out.append(f"## {title}")
        out.append(body.strip() if body else "")
        out.append("")

    # Intro
    add_h2("Intro", sec.get("intro", ""))

    # Core Questions — красиво разложим
    out.append("## Core Questions")
    cq = sec.get("core_questions", [])
    if isinstance(cq, list) and cq:
        for i, q in enumerate(cq, 1):
            qid = q.get("id", f"Q{i}")
            qtext = q.get("text", "").strip()
            qtype = q.get("type", "open")
            fups = q.get("followups", []) or []
            out.append(f"- **{qid}** ({qtype}): {qtext}")
            if fups:
                out.append(f"  - _follow-ups_: " + "; ".join(fups))
    out.append("")

    add_h2("Deepening (5 Whys)", sec.get("deepening_5whys", ""))
    add_h2("Branching Rules", sec.get("branching_rules", ""))

    out.append("## Evidence Tags")
    et = sec.get("evidence_tags", []) or []
    if et:
        out.append("- " + "\n- ".join(et))
    out.append("")

    add_h2("Output Contract Hints", sec.get("output_hints", ""))
    add_h2("Safety & Ethics", sec.get("safety_ethics", ""))
    add_h2("Stop Conditions", sec.get("stop_conditions", ""))

    return "\n".join(out).strip() + "\n"


class Step(BaseStep):
    name = "step_02a_guide_compile"

    def __init__(self) -> None:
        self.llm = LLM()

    def run(self, context: dict, artifacts: dict) -> StepResult:
        run_dir: Path = context.get("run_dir") or ensure_run_dir()
        project_dir: Optional[Path] = context.get("project_dir")
        input_cfg: dict = context.get("input", {}) or {}
        guides = input_cfg.get("guides", {}) or {}
        raw_guide_ref = guides.get("interview_core")

        if not raw_guide_ref:
            return StepResult(score=0.0, notes="input.guides.interview_core is not set")

        raw_path = resolve_guide_path(raw_guide_ref, project_dir)
        if not raw_path.exists():
            return StepResult(score=0.0, notes=f"Guide file not found: {raw_path}")

        raw_md = raw_path.read_text(encoding="utf-8")

        # Мастер-промт: просим LLM собрать строгий JSON-гайд по нашему контракту
        system = (
            "You convert messy interview manuals into a clean, production-ready AJTBD interview guide "
            "that strictly follows the JSON schema I give you. "
            "Think like a senior UX researcher: normalize sections, extract core questions, keep 5 Whys logic, "
            "and make it consistent and safe."
        )

        # JSON-ответ: ожидаем ключ 'guide' по contracts/guide.schema.json
        prompt = f"""
Transform the following raw AJTBD interview manual into a normalized guide that matches the JSON schema.

Return ONLY a JSON object with key "guide" (no markdown, no extra text).

RAW MANUAL (Markdown, 600+ lines possible):
---
{raw_md}
---

HARD REQUIREMENTS:
- Construct 'meta' with at least: title, language, audience, goal, interview_mode, version.
- Construct 'sections' with: intro, core_questions[], deepening_5whys, branching_rules, evidence_tags[], output_hints, safety_ethics, stop_conditions.
- core_questions[] must include: id, text, type (open|scale|multiple), followups[].
"""

        llm_json = self.llm.generate_json(system=system, prompt=prompt)
        guide = llm_json.get("data", {}).get("guide")
        if not isinstance(guide, dict):
            return StepResult(score=0.2, notes=f"LLM did not return valid 'guide' object. Notes: {llm_json.get('notes','')}")

        # Валидация по JSON-схеме
        schema_path = contracts_dir() / "guide.schema.json"
        schema_score, schema_notes = validate_with_schema_path(schema_path, guide)

        # Рендерим в нормальный Markdown с YAML front-matter
        compiled_md = _guide_json_to_markdown(guide)

        # Сохраняем в artifacts
        guides_dir = run_dir / "guides"
        guides_dir.mkdir(parents=True, exist_ok=True)
        out_path = guides_dir / f"{raw_path.stem}.compiled.md"
        save_md(out_path, compiled_md)

        # Дополнительно — копия в проект (если проект известен)
        project_out_path = None
        if project_dir:
            proj_compiled = project_dir / "guides" / "_compiled"
            proj_compiled.mkdir(parents=True, exist_ok=True)
            project_out_path = proj_compiled / f"{raw_path.stem}.compiled.md"
            save_md(project_out_path, compiled_md)

        data = {
            "compiled_path": str(project_out_path or out_path),
            "artifacts_compiled_path": str(out_path),
            "schema_score": schema_score,
            "schema_notes": schema_notes
        }

        # Итоговая оценка: берём минимум из самооценки и валидности схемы
        self_score = float(llm_json.get("score", 0.85))
        final_score = min(self_score, schema_score)

        return StepResult(data=data, score=final_score, notes=f"Guide compiled. {schema_notes}", uncertainty=float(llm_json.get("uncertainty", 0.15)))
