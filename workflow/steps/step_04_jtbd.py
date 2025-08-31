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

        # Возьмем стандарт JTBD (если есть)
        jtbd_std = standards.get("jtbd.md", "")

        # Сделаем компактный превью корпуса (LLM-friendly)
        preview_chunks = []
        for row in corpus[:20]:  # safety cap
            session = row.get("session") or row
            preview_chunks.append(json.dumps(session, ensure_ascii=False)[:1200])
        preview = "\n---\n".join(preview_chunks)

        system = "You produce clean JTBD graphs from qualitative VOC according to the provided standard and contract."
        prompt = f"""
Build a JTBD graph (Big/Medium/Small jobs) and associated evidence from the VOC preview below.
Return ONLY a JSON object that matches the contract for step_04_jtbd.schema.json.

VOC PREVIEW:
{preview}

STANDARD (JTBD.md):
{jtbd_std}
"""

        llm_json = self.llm.generate_json(system=system, prompt=prompt, standard_text=jtbd_std)
        # ожидаем формат {"data": {...}, "score": ..., "uncertainty": ..., "notes": ...}
        data = llm_json.get("data", {})

        # Валидация по контракту + чеклист
        schema_score, checklist_score, validation_notes = validate_artifact(self.name, data, standards)

        # Итоговая оценка
        self_score = float(llm_json.get("score", 0.7))
        final_score = min(self_score, schema_score, checklist_score)

        notes = f"JTBD built. Validation: {validation_notes}. LLM notes: {llm_json.get('notes','')}"
        return StepResult(data=data, score=final_score, notes=notes, uncertainty=float(llm_json.get("uncertainty", 0.2)))
