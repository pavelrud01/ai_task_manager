import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Core Settings ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# --- Workflow Control ---
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", 0.75))
MAX_REFLECTION_LOOPS = int(os.getenv("MAX_REFLECTION_LOOPS", 2))

# --- Human-in-the-Loop Triggers ---
UNCERTAINTY_THRESHOLD_ASK = float(os.getenv("UNCERTAINTY_THRESHOLD_ASK", 0.6))
HITL_UNCERTAINTY_TRIGGER = float(os.getenv("HITL_UNCERTAINTY_TRIGGER", 0.3))
HITL_SCORE_BUFFER = float(os.getenv("HITL_SCORE_BUFFER", 0.05))
STD_STEP0_UNCERTAINTY_MAX = float(os.getenv("STD_STEP0_UNCERTAINTY_MAX", 0.10))
CRITICAL_STEPS_FOR_HITL = ["step_13_tasks"]

# --- Workflow Definition: AJTBD Discovery from Scratch ---
WORKFLOW_STEPS = [
    WORKFLOW_STEPS = [
    "step_00_compliance_check",           # если используете
    "step_02a_guide_compile",            # ⬅ новый шаг
    "step_03_interview_collect",
    "step_04_jtbd",
    "step_05_segments",
    "step_06_decision_mapping",
    "step_12_funnel_design",   # пока можно оставить как заглушку или временно убрать
    "step_10_synthesis",       # синтез (схема уже есть)
    "step_11_tasks"            # задачи (схема уже есть)
]
