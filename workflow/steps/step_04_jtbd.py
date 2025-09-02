# workflow/steps/step_04_jtbd.py
from __future__ import annotations
from pathlib import Path
import json
from typing import List, Dict, Any

from .base import BaseStep, StepResult
from utils.io import ensure_run_dir
from llm.client import LLM
from validators.standards_loader import load_core_standards
from validators.validate import validate_artifact


def _read_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _load_corpus(run_dir: Path) -> List[dict]:
    interviews_dir = run_dir / "interviews"
    rows: List[dict] = []
    for name in ("simulated.jsonl", "ingest.jsonl", "after_ingest.jsonl"):
        rows.extend(_read_jsonl(interviews_dir / name))
    return rows


class Step(BaseStep):
    name = "step_04_jtbd"

    def __init__(self) -> None:
        self.llm = LLM()

    def run(self, context: dict, artifacts: dict) -> StepResult:
        run_dir: Path = context.get("run_dir") or ensure_run_dir()
        standards: Dict[str, str] = load_core_standards(context.get("project_dir"))

        corpus = _load_corpus(run_dir)
        if not corpus:
            return StepResult(score=0.2, notes="No interview corpus found. Run step_03 first.")

        # Получаем стандарты и гайды
        tdd = standards.get("tdd.md", "")
        jtbd_std = standards.get("jtbd.md", "")
        evidence_tags_md = (context.get("guides", {}) or {}).get("Evidence_Tags.md", "")

        # Сделаем компактный превью корпуса (LLM-friendly)
        preview_chunks = []
        for row in corpus[:20]:  # safety cap
            session = row.get("session") or row
            preview_chunks.append(json.dumps(session, ensure_ascii=False)[:1200])
        preview = "\n---\n".join(preview_chunks)

        system_prompt = (
            "You are a senior JTBD analyst. Produce structured JTBD items that VALIDATE against the JSON Schema. "
            "Attach evidence_refs with quotes and canonical tags. Follow TDD standard (red→green→refactor, 5 whys, DOD)."
        )

        user_prompt = f"""
INPUT CONTEXT:
- Company: {context['input'].get('company', 'N/A')}
- Products: {context['input'].get('products', [])}
- Raw interviews/reviews may be available in artifacts and previous steps.

REQUIREMENTS:
1) Follow JTBD standard and TDD rules strictly.
2) For EVERY JTBD item include at least ONE evidence_ref with:
   id (E-...), source_type, quote, confidence, and tags[] from the canonical list.
3) Use tag families from Evidence Tags guide.
4) Output MUST validate against step_04_jtbd.schema.json.

EVIDENCE TAGS GUIDE:
---
{evidence_tags_md[:2500]}
---

STANDARDS:
---
{jtbd_std[:2500]}
---
TDD:
---
{tdd[:2500]}
---
"""

        schema = (context.get("schemas") or {}).get("step_04_jtbd", {})
        std_text = (context.get("md_standards") or {}).get("jtbd.md", "")
        resp = self.llm.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            org_context="",
            standard_schema=schema,
            standard_text=std_text,
            reflection_notes=context.get("reflection_notes","")
        )
        # ожидаем формат {"data": {...}, "score": ..., "uncertainty": ..., "notes": ...}
        data = resp.get("data", {})

        # Валидация по контракту + чеклист
        schema_score, checklist_score, validation_notes = validate_artifact(self.name, data, standards)

        # Итоговая оценка
        self_score = float(resp.get("score", 0.7))
        final_score = min(self_score, schema_score, checklist_score)

        notes = f"JTBD built. Validation: {validation_notes}. LLM notes: {resp.get('notes','')}"
        return StepResult(data=data, score=final_score, notes=notes, uncertainty=float(resp.get("uncertainty", 0.2)))
