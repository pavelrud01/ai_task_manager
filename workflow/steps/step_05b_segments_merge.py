# workflow/steps/step_05b_segments_merge.py
from __future__ import annotations
from pathlib import Path
import json
from typing import List, Dict, Any, Optional

from .base import BaseStep, StepResult
from utils.io import ensure_run_dir, save_md
from validators.standards_loader import load_guide_markdown
from llm.client import LLM


def _load_longform_exports(run_dir: Path) -> Dict[str, str]:
    """Загружает экспортированные longform документы."""
    exports_dir = run_dir / "exports" / "jobs_longform"
    longform_docs = {}
    
    if not exports_dir.exists():
        return longform_docs
    
    for md_file in exports_dir.glob("*__jobs_longform.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            segment_id = md_file.stem.replace("__jobs_longform", "")
            longform_docs[segment_id] = content
        except Exception:
            continue
    
    return longform_docs


class Step(BaseStep):
    name = "step_05b_segments_merge"

    def __init__(self) -> None:
        self.llm = LLM()

    def _merge_segments(self, segments: List[dict], longform_docs: Dict[str, str], 
                       guide_text: str, context: dict) -> Dict[str, Any]:
        """Объединяет сегменты и генерирует персоны."""
        
        system_prompt = (
            "You are a senior market analyst specializing in AJTBD segmentation. "
            "Merge 10-15 segments into 3-5 larger, more actionable segments and create personas. "
            "Follow the Segment_Hypotheses_B2C.md guide for segment selection criteria."
        )
        
        user_prompt = f"""
SEGMENTS TO MERGE:
{json.dumps(segments, ensure_ascii=False, indent=2)}

AVAILABLE LONGFORM DOCS:
{json.dumps(list(longform_docs.keys()), ensure_ascii=False)}

REQUIREMENTS:
1) Merge 10-15 segments into 3-5 larger segments based on:
   - Similar Core Jobs and Big Jobs
   - Similar context and criteria
   - Similar TAM/SAM/SOM potential
   - Similar customer profiles

2) For each merged segment, create a persona with:
   - Demographics and role
   - Pain points and motivations
   - Behavioral patterns
   - Decision-making criteria

3) Prioritize segments by:
   - Market size (TAM/SAM/SOM)
   - Customer value potential
   - Profitability
   - Scalability

4) Include evidence references from original segments

SEGMENT HYPOTHESES GUIDE:
---
{guide_text[:4000]}
---

Return JSON with structure:
{{
  "merged_segments": [
    {{
      "segment_id": "MS-001",
      "segment_name": "Merged Segment Name",
      "priority": 1,
      "original_segments": ["S-001", "S-002", "S-003"],
      "core_jobs": ["J-001", "J-002"],
      "big_job": "Higher-level goal",
      "tam_sam_som": {{
        "tam": "Large market description",
        "sam": "Addressable market description", 
        "som": "Obtainable market description"
      }},
      "attractiveness": "Why this segment is attractive",
      "evidence_refs": [...]
    }}
  ],
  "personas": [
    {{
      "persona_id": "P-001",
      "persona_name": "Persona Name",
      "segment_id": "MS-001",
      "demographics": "Age, role, situation",
      "pain_points": ["Pain 1", "Pain 2"],
      "motivations": ["Motivation 1", "Motivation 2"],
      "behavioral_patterns": ["Pattern 1", "Pattern 2"],
      "decision_criteria": ["Criteria 1", "Criteria 2"],
      "description": "2-3 paragraph persona description"
    }}
  ]
}}
"""
        
        schema = context.get("schemas", {}).get("step_05b_segments_merge", {})
        std_text = context.get("md_standards", {}).get("segmentation.md", "")
        
        resp = self.llm.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            org_context=str(context.get("org_context", {})),
            standard_schema=schema,
            standard_text=std_text,
            reflection_notes=context.get("reflection_notes", "")
        )
        
        return resp.get("data", {})

    def _generate_personas_markdown(self, personas: List[dict]) -> str:
        """Генерирует Markdown документ с персонами."""
        
        md_lines = [
            "# Personas for Market Segments",
            "",
            "This document contains detailed personas for the merged market segments.",
            ""
        ]
        
        for persona in personas:
            md_lines.extend([
                f"## {persona.get('persona_name', 'Unnamed Persona')}",
                "",
                f"**Persona ID**: {persona.get('persona_id', 'N/A')}",
                f"**Segment**: {persona.get('segment_id', 'N/A')}",
                "",
                f"### Demographics",
                f"{persona.get('demographics', 'Not specified')}",
                "",
                f"### Pain Points",
            ])
            
            pain_points = persona.get('pain_points', [])
            for pain in pain_points:
                md_lines.append(f"- {pain}")
            
            md_lines.extend([
                "",
                f"### Motivations",
            ])
            
            motivations = persona.get('motivations', [])
            for motivation in motivations:
                md_lines.append(f"- {motivation}")
            
            md_lines.extend([
                "",
                f"### Behavioral Patterns",
            ])
            
            patterns = persona.get('behavioral_patterns', [])
            for pattern in patterns:
                md_lines.append(f"- {pattern}")
            
            md_lines.extend([
                "",
                f"### Decision Criteria",
            ])
            
            criteria = persona.get('decision_criteria', [])
            for criterion in criteria:
                md_lines.append(f"- {criterion}")
            
            md_lines.extend([
                "",
                f"### Description",
                f"{persona.get('description', 'No description available')}",
                "",
                "---",
                ""
            ])
        
        return "\n".join(md_lines)

    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Укрупняет 10-15 сегментов и генерирует персоны на базе правил AJTBD.
        
        Вход:
        - artifacts/step_05_segments.json
        - prompts/guides/Segment_Hypotheses_B2C.md
        - (опц.) exports/jobs_longform/* для ссылок
        
        Выход:
        - artifacts/step_05b_segments_merged.json
        - artifacts/exports/personas.md
        """
        run_dir: Path = context.get("run_dir") or ensure_run_dir()
        project_dir: Optional[Path] = context.get("project_dir")
        
        # Загружаем входные данные
        segments_data = artifacts.get("step_05_segments", {})
        if not segments_data:
            return StepResult(
                score=0.0,
                notes="Missing required artifact: step_05_segments"
            )
        
        segments = segments_data.get("segments", [])
        if len(segments) < 3:
            return StepResult(
                score=0.3,
                notes=f"Too few segments to merge: {len(segments)}. Need at least 3."
            )
        
        # Загружаем гайд для генерации гипотез
        try:
            guide_text = load_guide_markdown("Segment_Hypotheses_B2C.md", project_dir)
        except Exception as e:
            return StepResult(
                score=0.0,
                notes=f"Could not load Segment_Hypotheses_B2C.md: {e}"
            )
        
        # Загружаем longform документы (опционально)
        longform_docs = _load_longform_exports(run_dir)
        
        # Объединяем сегменты и генерируем персоны
        merged_data = self._merge_segments(segments, longform_docs, guide_text, context)
        
        if not merged_data:
            return StepResult(
                score=0.0,
                notes="Failed to merge segments and generate personas"
            )
        
        # Сохраняем объединенные сегменты
        merged_segments = merged_data.get("merged_segments", [])
        personas = merged_data.get("personas", [])
        
        # Создаем директорию для экспорта
        exports_dir = run_dir / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем JSON с объединенными сегментами
        merged_json_path = run_dir / "step_05b_segments_merged.json"
        merged_json_path.write_text(
            json.dumps(merged_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # Генерируем и сохраняем Markdown с персонами
        personas_md = self._generate_personas_markdown(personas)
        personas_path = exports_dir / "personas.md"
        save_md(personas_path, personas_md)
        
        # Создаем отчет
        report_lines = [
            f"# Segments Merge Report",
            f"",
            f"**Original segments**: {len(segments)}",
            f"**Merged segments**: {len(merged_segments)}",
            f"**Personas created**: {len(personas)}",
            f"**Longform docs used**: {len(longform_docs)}",
            f"",
            f"## Merged Segments:",
        ]
        
        for segment in merged_segments:
            report_lines.append(f"- {segment.get('segment_name', 'Unnamed')} (Priority: {segment.get('priority', 'N/A')})")
        
        report_lines.extend([
            "",
            f"## Personas:",
        ])
        
        for persona in personas:
            report_lines.append(f"- {persona.get('persona_name', 'Unnamed')} (Segment: {persona.get('segment_id', 'N/A')})")
        
        report_content = "\n".join(report_lines)
        save_md(run_dir / "step_05b_report.md", report_content)
        
        # Оценка качества
        if merged_segments and personas:
            score = min(0.9, 0.6 + (len(merged_segments) / 5) * 0.3)
            notes = f"Merged {len(segments)} segments into {len(merged_segments)} segments, created {len(personas)} personas"
        else:
            score = 0.0
            notes = "Failed to merge segments or create personas"
        
        return StepResult(
            data={
                "merged_segments": merged_segments,
                "personas": personas,
                "original_segments_count": len(segments),
                "longform_docs_used": len(longform_docs)
            },
            score=score,
            notes=notes
        )
