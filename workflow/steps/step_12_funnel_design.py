from .base import BaseStep, StepResult
from llm.client import LLM
from validators.standards_loader import get_standard_for_step

class Step(BaseStep):
    name = "step_12_funnel_design"
    def __init__(self): self.llm = LLM()

    def run(self, context: dict, artifacts: dict) -> StepResult:
        md = get_standard_for_step(self.name, None, context.get("md_standards", {}))
        org = context.get("org_context", {})
        segs = artifacts.get("step_05_segments", {})
        dmap = artifacts.get("step_06_decision_mapping", {})
        channels = context["input"].get("channels", ["paid","seo","email"])

        system = "You are a funnel architect. Design AAARRR/AIDA funnels per segment×channel with experiments."
        user = (
            f"ORG:\n{org}\n\nSEGMENTS:\n{segs}\n\nDECISION MAP:\n{dmap}\n\nCHANNELS: {channels}\n\n"
            "Return only JSON {data, score, notes, uncertainty} where data fits 'step_12_funnel_design' schema."
        )

        resp = self.llm.generate_json(system, user, str(org), md, context.get("reflection_notes",""))
        return StepResult(
            data=resp.get("data",{}),
            score=float(resp.get("score",0.7) or 0.7),
            notes=resp.get("notes",""),
            uncertainty=float(resp.get("uncertainty",0.3) or 0.3)
        )
