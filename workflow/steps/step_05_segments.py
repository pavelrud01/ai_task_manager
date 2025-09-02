from .base import BaseStep, StepResult
from llm.client import LLM
from validators.standards_loader import get_standard_for_step

class Step(BaseStep):
    name = "step_05_segments"
    def __init__(self): self.llm = LLM()

    def run(self, context: dict, artifacts: dict) -> StepResult:
        md = get_standard_for_step(self.name, None, context.get("md_standards", {}))
        org = context.get("org_context", {})
        jtbd = artifacts.get("step_04_jtbd", {})
        lp_text = artifacts.get("step_02_extract", {}).get("full_text","")

        system = "You are a market analyst. Follow the standard, self-check via checklist/red-flags, and return data validating the schema. Include evidence_refs with quotes and canonical tags for all segments."
        user = (
            f"ORGANIZATIONAL CONTEXT:\n{org}\n\n"
            f"JTBD DATA:\n{jtbd}\n\n"
            f"OPTIONAL LP TEXT (for fear_amplifiers_on_lp):\n{lp_text[:3000]}\n\n"
            "REQUIREMENTS:\n"
            "1) For EVERY segment include at least ONE evidence_ref with: id (E-...), source_type, quote, confidence, and tags[]\n"
            "2) Use canonical tags from Evidence Tags guide\n"
            "3) Output MUST validate against step_05_segments.schema.json\n\n"
            "Return only JSON with keys: data, score (0..1), notes, uncertainty (0..1).\n"
            "Ensure data fits 'step_05_segments' schema."
        )

        schema = (context.get("schemas") or {}).get("step_05_segments", {})
        resp = self.llm.generate_json(
            system_prompt=system,
            user_prompt=user,
            org_context=str(org),
            standard_schema=schema,
            standard_text=md,
            reflection_notes=context.get("reflection_notes","")
        )
        return StepResult(
            data=resp.get("data",{}),
            score=float(resp.get("score",0.7) or 0.7),
            notes=resp.get("notes",""),
            uncertainty=float(resp.get("uncertainty",0.3) or 0.3)
        )
