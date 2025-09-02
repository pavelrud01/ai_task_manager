from .base import BaseStep, StepResult
from llm.client import LLM
from validators.standards_loader import get_standard_for_step

class Step(BaseStep):
    name = "step_06_decision_mapping"
    def __init__(self): self.llm = LLM()

    def run(self, context: dict, artifacts: dict) -> StepResult:
        md = get_standard_for_step(self.name, None, context.get("md_standards", {}))
        org = context.get("org_context", {})
        segs = artifacts.get("step_05_segments", {})

        system = "You are a journey planner. Build Decision Maps per segment with CTA/metrics and no content gaps. Include evidence_refs with quotes and canonical tags for all decision points."
        user = (
            f"ORG:\n{org}\n\nSEGMENTS:\n{segs}\n\n"
            "REQUIREMENTS:\n"
            "1) For EVERY decision point include at least ONE evidence_ref with: id (E-...), source_type, quote, confidence, and tags[]\n"
            "2) Use canonical tags from Evidence Tags guide\n"
            "3) Output MUST validate against step_06_decision_mapping.schema.json\n\n"
            "Return only JSON {data, score, notes, uncertainty} where data fits 'step_06_decision_mapping' schema."
        )

        schema = (context.get("schemas") or {}).get("step_06_decision_mapping", {})
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
