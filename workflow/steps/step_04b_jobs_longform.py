# workflow/steps/step_04b_jobs_longform.py
from __future__ import annotations
from pathlib import Path
import json
from typing import List, Dict, Any, Optional

from .base import BaseStep, StepResult
from utils.io import ensure_run_dir, save_md
from validators.standards_loader import load_core_standards
from llm.client import LLM


def _read_jsonl(path: Path) -> List[dict]:
    """Читает JSONL файл и возвращает список объектов."""
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


def _load_interview_corpus(run_dir: Path) -> List[dict]:
    """Загружает корпус интервью из всех JSONL файлов."""
    interviews_dir = run_dir / "interviews"
    rows: List[dict] = []
    
    for name in ("simulated.jsonl", "ingest.jsonl", "after_ingest.jsonl"):
        rows.extend(_read_jsonl(interviews_dir / name))
    
    return rows


def _extract_evidence_for_segment(segment_id: str, corpus: List[dict], jtbd_data: dict) -> List[dict]:
    """Извлекает evidence references для конкретного сегмента."""
    evidence_refs = []
    
    # Ищем evidence в JTBD данных
    jobs = jtbd_data.get("jobs", [])
    for job in jobs:
        if job.get("job_id", "").startswith("J-"):
            job_evidence = job.get("evidence_refs", [])
            for ev in job_evidence:
                if ev.get("id", "").startswith("E-"):
                    evidence_refs.append(ev)
    
    # Ищем evidence в корпусе интервью
    for row in corpus:
        session = row.get("session", row)
        if isinstance(session, dict):
            quotes = session.get("quotes", [])
            for quote in quotes:
                if isinstance(quote, dict) and quote.get("id", "").startswith("E-"):
                    evidence_refs.append({
                        "id": quote.get("id", ""),
                        "source_type": "interview",
                        "quote": quote.get("text", ""),
                        "confidence": 0.8,
                        "tags": quote.get("tags", [])
                    })
    
    return evidence_refs


class Step(BaseStep):
    name = "step_04b_jobs_longform"

    def __init__(self) -> None:
        self.llm = LLM()

    def _generate_longform_for_segment(self, segment: dict, jtbd_data: dict, 
                                     corpus: List[dict], standard_text: str, context: dict) -> str:
        """Генерирует длинный шаблон описания работ для сегмента."""
        
        segment_id = segment.get("segment_id", "")
        segment_name = segment.get("segment_name", "")
        
        # Извлекаем evidence для сегмента
        evidence_refs = _extract_evidence_for_segment(segment_id, corpus, jtbd_data)
        
        # Создаем превью корпуса для LLM
        corpus_preview = []
        for row in corpus[:10]:  # Ограничиваем размер
            session = row.get("session", row)
            if isinstance(session, dict):
                transcript = session.get("transcript", [])
                if transcript:
                    corpus_preview.append({
                        "persona": session.get("persona", ""),
                        "transcript": transcript[:3]  # Первые 3 Q/A
                    })
        
        system_prompt = (
            "You are a senior JTBD analyst creating detailed job descriptions for market segments. "
            "Create a comprehensive longform document following the jtbd_longform.md standard. "
            "Include evidence references with quotes and canonical tags for all claims."
        )
        
        user_prompt = f"""
SEGMENT DATA:
{json.dumps(segment, ensure_ascii=False, indent=2)}

JTBD DATA:
{json.dumps(jtbd_data, ensure_ascii=False, indent=2)}

INTERVIEW CORPUS PREVIEW:
{json.dumps(corpus_preview, ensure_ascii=False, indent=2)}

EVIDENCE REFERENCES:
{json.dumps(evidence_refs, ensure_ascii=False, indent=2)}

REQUIREMENTS:
1) Follow the jtbd_longform.md standard structure exactly
2) For EVERY claim include evidence references with:
   - id (E-...), quote, source, confidence, tags
3) Include Core Jobs, Emotional Jobs, Social Jobs, Big Job
4) Include 5 Whys analysis for each Core Job
5) Include Critical Path of Jobs (КПР)
6) Include Anti-JTBD (what people DON'T want)
7) Include Coverage analysis
8) Use canonical tags from Evidence Tags guide

STANDARD:
---
{standard_text[:3000]}
---

Return ONLY the markdown content for the longform document.
"""
        
        schema = context.get("schemas", {}).get("step_04b_jobs_longform", {})
        std_text = context.get("md_standards", {}).get("jtbd_longform.md", "")
        
        resp = self.llm.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            org_context=str(context.get("org_context", {})),
            standard_schema=schema,
            standard_text=std_text,
            reflection_notes=context.get("reflection_notes", "")
        )
        
        # LLM должен вернуть markdown в поле "markdown"
        return resp.get("data", {}).get("markdown", "")

    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Создает длинные шаблоны описания работ для каждого сегмента.
        
        Вход:
        - artifacts/step_04_jtbd.json
        - artifacts/step_05_segments.json  
        - artifacts/interviews/*.jsonl
        - prompts/standards/jtbd_longform.md
        
        Выход:
        - artifacts/exports/jobs_longform/<segment_id>__jobs_longform.md
        """
        run_dir: Path = context.get("run_dir") or ensure_run_dir()
        standards: Dict[str, str] = load_core_standards(context.get("project_dir"))
        
        # Загружаем входные данные
        jtbd_data = artifacts.get("step_04_jtbd", {})
        segments_data = artifacts.get("step_05_segments", {})
        
        if not jtbd_data or not segments_data:
            return StepResult(
                score=0.0, 
                notes="Missing required artifacts: step_04_jtbd or step_05_segments"
            )
        
        # Загружаем корпус интервью
        corpus = _load_interview_corpus(run_dir)
        if not corpus:
            return StepResult(
                score=0.3,
                notes="No interview corpus found. Run step_03 first."
            )
        
        # Получаем стандарт
        standard_text = standards.get("jtbd_longform.md", "")
        if not standard_text:
            return StepResult(
                score=0.0,
                notes="jtbd_longform.md standard not found"
            )
        
        # Создаем директорию для экспорта
        exports_dir = run_dir / "exports" / "jobs_longform"
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        segments = segments_data.get("segments", [])
        produced_files = []
        
        # Генерируем длинные шаблоны для каждого сегмента
        for segment in segments:
            try:
                segment_id = segment.get("segment_id", "")
                if not segment_id:
                    continue
                
                # Генерируем длинный шаблон
                longform_content = self._generate_longform_for_segment(
                    segment, jtbd_data, corpus, standard_text, context
                )
                
                if not longform_content.strip():
                    continue
                
                # Сохраняем файл
                filename = f"{segment_id}__jobs_longform.md"
                output_path = exports_dir / filename
                save_md(output_path, longform_content)
                produced_files.append(str(output_path))
                
            except Exception as e:
                print(f"Error generating longform for segment {segment_id}: {e}")
                continue
        
        # Создаем отчет
        report_lines = [
            f"# Jobs Longform Export Report",
            f"",
            f"**Generated**: {len(produced_files)} longform documents",
            f"**Segments processed**: {len(segments)}",
            f"**Interview corpus size**: {len(corpus)} sessions",
            f"",
            f"## Generated Files:",
        ]
        
        for file_path in produced_files:
            report_lines.append(f"- {Path(file_path).name}")
        
        report_content = "\n".join(report_lines)
        save_md(run_dir / "step_04b_report.md", report_content)
        
        # Оценка качества
        if produced_files:
            score = min(0.9, 0.5 + (len(produced_files) / len(segments)) * 0.4)
            notes = f"Generated {len(produced_files)} longform documents for {len(segments)} segments"
        else:
            score = 0.0
            notes = "No longform documents generated"
        
        return StepResult(
            data={
                "produced_files": produced_files,
                "segments_processed": len(segments),
                "corpus_size": len(corpus)
            },
            score=score,
            notes=notes
        )


