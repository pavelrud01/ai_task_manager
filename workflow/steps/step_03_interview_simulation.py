from .base import BaseStep, StepResult
from collectors.interview_simulator import run_simulation
from validators.standards_loader import get_standard_for_step

class Step(BaseStep):
    name = "step_03_interview_simulation"

    def run(self, context: dict, artifacts: dict) -> StepResult:
        analysis_type = context.get("input", {}).get("analysis_type", "frequency")
        all_standards = context.get("md_standards", {}) # Загрузчик теперь возвращает словарь всех стандартов
        
        standard_text = get_standard_for_step(self.name, analysis_type, all_standards)
        if not standard_text:
            return StepResult(score=0.0, notes=f"Standard for step '{self.name}' with type '{analysis_type}' not found.")

        personas = context.get("input", {}).get("personas")
        if not personas:
            return StepResult(score=0.0, notes="No 'personas' defined in input file for interview simulation.")

        org_context_text = "\n".join(context.get("org_context", {}).values())
        simulation_data = run_simulation(standard_text, personas, org_context_text)

        score = 1.0 if simulation_data.get("transcripts") else 0.1
        notes = f"Interview simulation completed for {len(personas)} personas."
        
        return StepResult(data=simulation_data, score=score, notes=notes)