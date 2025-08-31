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

        system = "You are a market analyst. Follow the standard, self-check via checklist/red-flags, and return data validating the schema."
        user = (
            f"ORGANIZATIONAL CONTEXT:\n{org}\n\n"
            f"JTBD DATA:\n{jtbd}\n\n"
            f"OPTIONAL LP TEXT (for fear_amplifiers_on_lp):\n{lp_text[:3000]}\n\n"
            "Return only JSON with keys: data, score (0..1), notes, uncertainty (0..1).\n"
            "Ensure data fits 'step_05_segments' schema."
        )

        resp = self.llm.generate_json(system, user, str(org), md, context.get("reflection_notes",""))
        return StepResult(
            data=resp.get("data",{}),
            score=float(resp.get("score",0.7) or 0.7),
            notes=resp.get("notes",""),
            uncertainty=float(resp.get("uncertainty",0.3) or 0.3)
        )
