from .base import BaseStep, StepResult
from pathlib import Path
import hashlib
from llm.client import LLM

class Step(BaseStep):
    name = "step_02a_guide_compile"

    def __init__(self):
        self.llm = LLM()

    def _read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def _sha256(self, p: Path) -> str:
        try:
            b = p.read_bytes()
            return hashlib.sha256(b).hexdigest()
        except Exception:
            return ""

    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Ожидает в input:
        {
          "mode": "guide_compile",
          "project": "<name>",
          "raw_guide_path": "prompts/guides/AJTBD_Interview_Guide_B2C.md",
          "standard_path": "prompts/standards/guide_standard.md",
          "sources_glob": ["projects/<proj>/AJTBD_A/sources/*.txt"],
          "promote_to": "projects/<proj>/standards/AJTBD_Interview_Guide_B2C.md"
        }
        """
        inp = context.get("input", {})
        raw_guide_path = Path(inp.get("raw_guide_path", ""))
        standard_path = Path(inp.get("standard_path", "prompts/standards/guide_standard.md"))
        promote_to = Path(inp.get("promote_to", ""))

        raw_text = self._read_text(raw_guide_path)
        standard_text = self._read_text(standard_path)

        org_context = context.get("org_context", {})
        org_blob = "\n\n".join([v for v in org_context.values() if isinstance(v, str)])

        sources_paths = []
        for g in inp.get("sources_glob", []):
            for p in Path().glob(g):
                sources_paths.append(p)

        sources_digest = [
            {"path": str(p), "sha256": self._sha256(p)}
            for p in sources_paths
        ]

        system = (
            "You are a senior research editor. Compile a clean, production-ready AJTBD interview guide for B2C "
            "strictly following the provided Guide Standard. Include YAML front-matter, all required sections, "
            "and produce BOTH a structured JSON object (meta/sections/sources) and a complete Markdown document."
        )
        user = f"""
RAW GUIDE (noisy draft):
---
{raw_text[:20000]}
---

Build a canonical guide that passes the standard. Use these sources list (paths + sha256) for the index:
{sources_digest}
"""

        reflection_notes = context.get("reflection_notes", "")

        schema = (context.get("schemas") or {}).get("step_02a_guide_compile", {})
        resp = self.llm.generate_json(
            system_prompt=system,
            user_prompt=user,
            org_context=org_blob,
            standard_schema=schema,
            standard_text=standard_text,
            reflection_notes=reflection_notes
        )

        data = resp.get("data", {})
        score = float(resp.get("score", 0.0))
        notes = resp.get("notes", "")
        uncertainty = float(resp.get("uncertainty", 0.0))

        if promote_to:
            data["__promote_to"] = str(promote_to)
            data["__index_basename"] = Path(promote_to).with_suffix(".index.json").name

        return StepResult(data=data, score=score, notes=notes, uncertainty=uncertainty)
