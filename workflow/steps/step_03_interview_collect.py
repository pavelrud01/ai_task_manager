# workflow/steps/step_03_interview_collect.py
from __future__ import annotations
from pathlib import Path
import json
from typing import List, Dict, Any, Optional

from .base import BaseStep, StepResult
from utils.io import ensure_run_dir, save_md
from validators.standards_loader import (
    load_guide_markdown,
    parse_guide_markdown,
    contracts_dir,
)
from validators.validate import validate_with_schema_path
from llm.client import LLM


def _write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _ingest_sources(files: List[str]) -> List[dict]:
    """
    Простейший ingest: читаем тексты из файлов и кладём как сырой VOC-ряд.
    Можно расширить парсинг CSV/JSON при необходимости.
    """
    rows = []
    for fp in files:
        p = Path(fp)
        if not p.exists():
            continue
        content = _read_text_file(p)
        if not content.strip():
            continue
        rows.append({
            "source": str(p),
            "kind": "text",
            "content": content[:10000]  # safety cap
        })
    return rows


class Step(BaseStep):
    name = "step_03_interview_collect"

    def __init__(self) -> None:
        self.llm = LLM()

    def _validate_guide(self, guide_md: str) -> Dict[str, Any]:
        """
        Быстрая валидация: парсим front-matter/секции и приводим к объекту,
        который валидируем по contracts/guide.schema.json.
        """
        meta, sections = parse_guide_markdown(guide_md)
        guide_obj = {
            "meta": meta or {},
            "sections": {
                # нормализуем ключи
                "intro": sections.get("Intro", ""),
                "core_questions": [],  # заполним через LLM
                "deepening_5whys": sections.get("Deepening (5 Whys)", ""),
                "branching_rules": sections.get("Branching Rules", ""),
                "evidence_tags": [],
                "output_hints": sections.get("Output Contract Hints", ""),
                "safety_ethics": sections.get("Safety & Ethics", ""),
                "stop_conditions": sections.get("Stop Conditions", "")
            }
        }

        # Попросим LLM извлечь из секции Core Questions структуру (id, text, type, followups)
        system = "You convert human-written interview guides into a strict JSON structure."
        prompt = f"""
Read the following 'Core Questions' section and extract a list of questions with fields:
- id (string, unique)
- text (string)
- type (open|scale|multiple)
- followups (array of strings)

Return ONLY a JSON object with key "core_questions".

CORE QUESTIONS SECTION:
---
{sections.get("Core Questions", "")}
---
"""
        llm_json = self.llm.generate_json(system=system, prompt=prompt)
        cq = llm_json.get("data", {}).get("core_questions", [])
        if isinstance(cq, list):
            guide_obj["sections"]["core_questions"] = cq

        schema_path = contracts_dir() / "guide.schema.json"
        schema_score, schema_notes = validate_with_schema_path(schema_path, guide_obj)

        return {
            "guide": guide_obj,
            "schema_score": schema_score,
            "schema_notes": schema_notes
        }

    def _simulate_interviews(self, guide_obj: dict, n: int, personas: List[str], products: List[str]) -> List[dict]:
        system = "You are an expert qualitative researcher simulating AJTBD interviews."
        prompt = f"""
Using this guide (meta + sections), simulate {n} interview sessions.
Vary personas: {personas}
Vary products (if relevant): {products}

Return a JSON object with "sessions": an array, each session has:
- persona (string)
- product (string|null)
- transcript (array of Q/A turns)
- evidence_tags (array of strings)
- summary (string)

GUIDE (JSON):
{json.dumps(guide_obj, ensure_ascii=False)}
"""
        llm_json = self.llm.generate_json(system=system, prompt=prompt)
        sessions = llm_json.get("data", {}).get("sessions", [])
        # safety
        sessions = sessions if isinstance(sessions, list) else []
        return sessions

    def _gap_analysis_and_followups(self, guide_obj: dict, corpus_rows: List[dict], n: int) -> List[dict]:
        """
        Попросим LLM оценить пробелы покрытия и сгенерировать догон-интервью.
        """
        system = "You analyze existing VOC and design targeted follow-up interviews to close coverage gaps."
        corpus_preview = "\n---\n".join(r.get("content", "")[:1000] for r in corpus_rows[:8])
        prompt = f"""
Given the existing VOC corpus excerpts below, and the interview guide JSON,
perform a brief gap analysis: identify 3-5 major unanswered aspects relative to the guide.
Then simulate {n} focused interviews to close those gaps.

Return JSON with key "sessions" (same structure as earlier).

GUIDE (JSON):
{json.dumps(guide_obj, ensure_ascii=False)}

VOC EXCERPTS:
{corpus_preview}
"""
        llm_json = self.llm.generate_json(system=system, prompt=prompt)
        sessions = llm_json.get("data", {}).get("sessions", [])
        sessions = sessions if isinstance(sessions, list) else []
        return sessions

    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        A: data_availability == "A"
           - читаем гайд, валидируем, симулируем N интервью -> interviews/simulated.jsonl
        B/C:
           - ingest input.files -> interviews/ingest.jsonl
           - (опц) догон: валидируем гайд, симулируем follow-ups -> interviews/after_ingest.jsonl
        """
        run_dir: Path = context.get("run_dir") or ensure_run_dir()
        input_cfg: dict = context.get("input", {})
        project_dir: Optional[Path] = context.get("project_dir")

        # 1) загрузим гайд
        guides = input_cfg.get("guides", {}) or {}
        guide_path = guides.get("interview_core")
        if not guide_path:
            return StepResult(score=0.0, notes="No 'interview_core' guide specified in input.guides")

        try:
            guide_md = load_guide_markdown(guide_path, project_dir)
        except Exception as e:
            return StepResult(score=0.0, notes=f"Guide not found: {e}")

        val = self._validate_guide(guide_md)
        guide_obj = val["guide"]
        guide_schema_score = val["schema_score"]

        # 2) ветвление по сценарию
        availability = (input_cfg.get("data_availability") or "A").upper()
        personas = input_cfg.get("personas", [])
        products = input_cfg.get("products", [])

        interviews_dir = Path(run_dir) / "interviews"
        produced_files = []

        if availability == "A":
            n = int(input_cfg.get("n_interviews", 6))
            sessions = self._simulate_interviews(guide_obj, n, personas, products)
            out = interviews_dir / "simulated.jsonl"
            rows = [{"session": s} for s in sessions]
            _write_jsonl(out, rows)
            produced_files.append(str(out))

        else:
            files = input_cfg.get("files", [])
            corpus_rows = _ingest_sources(files)
            out_ingest = interviews_dir / "ingest.jsonl"
            _write_jsonl(out_ingest, corpus_rows)
            produced_files.append(str(out_ingest))

            # догон после ingest
            flags = input_cfg.get("flags", {}) or {}
            if flags.get("interview_after_ingest", True):
                n_follow = int(input_cfg.get("n_interviews_after_ingest", 2))
                sessions = self._gap_analysis_and_followups(guide_obj, corpus_rows, n_follow)
                out = interviews_dir / "after_ingest.jsonl"
                rows = [{"session": s} for s in sessions]
                _write_jsonl(out, rows)
                produced_files.append(str(out))

        # отчёт
        report = [
            f"- Guide schema score: {guide_schema_score:.2f}",
            f"- Produced: {produced_files}"
        ]
        save_md(Path(run_dir) / "step_03_report.md", "\n".join(report))

        # простая эвристика для score
        score = 0.9 if produced_files else 0.3
        notes = "Interview collection completed." if produced_files else "No interview files produced."

        return StepResult(
            data={"produced_files": produced_files, "guide_schema_score": guide_schema_score},
            score=score,
            notes=notes
        )
