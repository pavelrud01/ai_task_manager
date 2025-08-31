from .base import BaseStep, StepResult

class Step(BaseStep):
    name = "step_10_new_offers"

    def run(self, context: dict, artifacts: dict) -> StepResult:
        return StepResult(data={"status": f"placeholder for {self.name}"})


