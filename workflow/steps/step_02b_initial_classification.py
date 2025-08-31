from .base import BaseStep, StepResult

class Step(BaseStep):
    name = "step_02b_initial_classification"

    def run(self, context: dict, artifacts: dict) -> StepResult:
        return StepResult(data={"status": f"placeholder for {self.name}"})
