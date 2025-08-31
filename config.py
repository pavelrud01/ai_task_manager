import os
from dotenv import load_dotenv

load_dotenv()

# --- Core Settings ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# --- Workflow Control ---
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", 0.75))
MAX_REFLECTION_LOOPS = int(os.getenv("MAX_REFLECTION_LOOPS", 1))

# --- Workflow Definition ---
WORKFLOW_STEPS = [
    "step_00_compliance_check",
    "step_02_extract",
    "step_02b_initial_classification",
    "step_03_interview_collect",
    "step_04_jtbd",
    "step_05_segments",
    "step_06_decision_mapping",
    "step_10_synthesis",
    "step_11_tasks",
]
