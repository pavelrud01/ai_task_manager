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
from validators.validate import validate_artifact
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

    def _validate_guide(self, guide_md: str, context: dict) -> Dict[str, Any]:
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
        schema = (context.get("schemas") or {}).get("step_03_interview_collect", {})
        std_text = (context.get("md_standards") or {}).get("interview_ajtbd.md", "")
        llm_json = self.llm.generate_json(
            system_prompt=system,
            user_prompt=prompt,
            org_context="",
            standard_schema=schema,
            standard_text=std_text,
            reflection_notes=context.get("reflection_notes","")
        )
        cq = llm_json.get("data", {}).get("core_questions", [])
        if isinstance(cq, list):
            guide_obj["sections"]["core_questions"] = cq

        # Валидация гайда
        standards = {"guide": {}}  # Пустые стандарты для валидации
        schema_score, checklist_score, schema_notes = validate_artifact("guide", guide_obj, standards)

        return {
            "guide": guide_obj,
            "schema_score": schema_score,
            "schema_notes": schema_notes
        }

    def _simulate_interviews(self, guide_obj: dict, n: int, personas: List[str], products: List[str], context: dict) -> List[dict]:
        system = "You are an expert qualitative researcher simulating AJTBD interviews. Extract key quotes and assign E-identifiers for evidence tracking."
        prompt = f"""
Using this guide (meta + sections), simulate {n} interview sessions.
Vary personas: {personas}
Vary products (if relevant): {products}

IMPORTANT: For each session, extract 3-5 key quotes and assign unique E-identifiers (E-001, E-002, etc.)

Return a JSON object with "sessions": an array, each session has:
- persona (string)
- product (string|null)
- transcript (array of Q/A turns)
- evidence_tags (array of strings)
- summary (string)
- quotes (array of objects with: id, text, context, tags)

QUOTE STRUCTURE:
- id: "E-001", "E-002", etc. (unique across all sessions)
- text: the actual quote from the transcript
- context: brief description of when/why this quote was said
- tags: relevant evidence tags (pain_point, motivation, barrier, etc.)

GUIDE (JSON):
{json.dumps(guide_obj, ensure_ascii=False)}
"""
        schema = (context.get("schemas") or {}).get("step_03_interview_collect", {})
        std_text = (context.get("md_standards") or {}).get("interview_ajtbd.md", "")
        llm_json = self.llm.generate_json(
            system_prompt=system,
            user_prompt=prompt,
            org_context="",
            standard_schema=schema,
            standard_text=std_text,
            reflection_notes=context.get("reflection_notes","")
        )
        sessions = llm_json.get("data", {}).get("sessions", [])
        # safety
        sessions = sessions if isinstance(sessions, list) else []
        return sessions

    def _gap_analysis_and_followups(self, guide_obj: dict, corpus_rows: List[dict], n: int, context: dict) -> List[dict]:
        """
        Попросим LLM оценить пробелы покрытия и сгенерировать догон-интервью.
        """
        system = "You analyze existing VOC and design targeted follow-up interviews to close coverage gaps. Extract key quotes and assign E-identifiers for evidence tracking."
        corpus_preview = "\n---\n".join(r.get("content", "")[:1000] for r in corpus_rows[:8])
        prompt = f"""
Given the existing VOC corpus excerpts below, and the interview guide JSON,
perform a brief gap analysis: identify 3-5 major unanswered aspects relative to the guide.
Then simulate {n} focused interviews to close those gaps.

IMPORTANT: For each session, extract 3-5 key quotes and assign unique E-identifiers (E-001, E-002, etc.)

Return JSON with key "sessions" (same structure as earlier), each session must include:
- persona (string)
- product (string|null)
- transcript (array of Q/A turns)
- evidence_tags (array of strings)
- summary (string)
- quotes (array of objects with: id, text, context, tags)

QUOTE STRUCTURE:
- id: "E-001", "E-002", etc. (unique across all sessions)
- text: the actual quote from the transcript
- context: brief description of when/why this quote was said
- tags: relevant evidence tags (pain_point, motivation, barrier, etc.)

GUIDE (JSON):
{json.dumps(guide_obj, ensure_ascii=False)}

VOC EXCERPTS:
{corpus_preview}
"""
        schema = (context.get("schemas") or {}).get("step_03_interview_collect", {})
        std_text = (context.get("md_standards") or {}).get("interview_ajtbd.md", "")
        llm_json = self.llm.generate_json(
            system_prompt=system,
            user_prompt=prompt,
            org_context="",
            standard_schema=schema,
            standard_text=std_text,
            reflection_notes=context.get("reflection_notes","")
        )
        sessions = llm_json.get("data", {}).get("sessions", [])
        sessions = sessions if isinstance(sessions, list) else []
        return sessions

    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Поддерживает режимы: simulate | ingest | both
        
        simulate: симулируем интервью на основе гайда
        ingest: загружаем существующие данные из файлов
        both: сначала ingest, потом догон-симуляция
        
        Конфигурация через input.interview_mode или data_availability (для обратной совместимости)
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

        val = self._validate_guide(guide_md, context)
        guide_obj = val["guide"]
        guide_schema_score = val["schema_score"]

        # 2) Определяем режим работы
        # Новый способ: input.interview_mode
        # Старый способ: data_availability (для обратной совместимости)
        interview_mode = input_cfg.get("interview_mode", "").lower()
        if not interview_mode:
            # Обратная совместимость с data_availability
            availability = (input_cfg.get("data_availability") or "A").upper()
            if availability == "A":
                interview_mode = "simulate"
            else:
                interview_mode = "both" if input_cfg.get("flags", {}).get("interview_after_ingest", True) else "ingest"
        
        personas = input_cfg.get("personas", [])
        products = input_cfg.get("products", [])

        interviews_dir = Path(run_dir) / "interviews"
        produced_files = []

        # 3) Выполняем в зависимости от режима
        if interview_mode == "simulate":
            n = int(input_cfg.get("n_interviews", 6))
            sessions = self._simulate_interviews(guide_obj, n, personas, products, context)
            out = interviews_dir / "simulated.jsonl"
            rows = [{"session": s} for s in sessions]
            _write_jsonl(out, rows)
            produced_files.append(str(out))

        elif interview_mode == "ingest":
            files = input_cfg.get("files", [])
            if not files:
                return StepResult(score=0.0, notes="No files specified for ingest mode")
            corpus_rows = _ingest_sources(files)
            out_ingest = interviews_dir / "ingest.jsonl"
            _write_jsonl(out_ingest, corpus_rows)
            produced_files.append(str(out_ingest))

        elif interview_mode == "both":
            # Сначала ingest
            files = input_cfg.get("files", [])
            if not files:
                return StepResult(score=0.0, notes="No files specified for both mode")
            corpus_rows = _ingest_sources(files)
            out_ingest = interviews_dir / "ingest.jsonl"
            _write_jsonl(out_ingest, corpus_rows)
            produced_files.append(str(out_ingest))

            # Потом догон-симуляция
            n_follow = int(input_cfg.get("n_interviews_after_ingest", 2))
            sessions = self._gap_analysis_and_followups(guide_obj, corpus_rows, n_follow, context)
            out = interviews_dir / "after_ingest.jsonl"
            rows = [{"session": s} for s in sessions]
            _write_jsonl(out, rows)
            produced_files.append(str(out))

        else:
            return StepResult(score=0.0, notes=f"Unknown interview mode: {interview_mode}. Supported: simulate, ingest, both")

        # отчёт
        report = [
            f"- Interview mode: {interview_mode}",
            f"- Guide schema score: {guide_schema_score:.2f}",
            f"- Produced: {produced_files}"
        ]
        save_md(Path(run_dir) / "step_03_report.md", "\n".join(report))

        # простая эвристика для score
        score = 0.9 if produced_files else 0.3
        notes = f"Interview collection completed in {interview_mode} mode." if produced_files else "No interview files produced."

        return StepResult(
            data={
                "produced_files": produced_files, 
                "guide_schema_score": guide_schema_score,
                "interview_mode": interview_mode
            },
            score=score,
            notes=notes
        )
