import argparse
import json
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from utils.io import ensure_run_dir


# Импортируем все переменные из конфига
from config import *
from memory.memory import Memory
from utils.io import (append_lesson, confirm_action, ensure_run_dir,
                    save_artifact, save_md)
from validators.standards_loader import (load_contract_schemas,
                                       load_md_standards,
                                       load_organizational_context,
                                       summarize_understanding)
# Валидатор теперь будет принимать run_id для логирования инцидентов
from validators.validate import validate_artifact
from workflow.registry import load_step


def main():
    if not OPENAI_API_KEY:
        print("FATAL: OPENAI_API_KEY is not set in your .env file.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="AI Marketing Agent")
    parser.add_argument("--input", required=True, help="Path to input JSON")
    parser.add_argument("--project-dir", required=False, help="Path to project/scenario dir")
    args = parser.parse_args()

    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"FATAL: Input file not found at: {input_path}")
        sys.exit(1)

    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
    run_dir = ensure_run_dir(run_id)
    print(f"🚀 Starting run: {run_id}. Artifacts will be saved in: {run_dir}")

    with input_path.open("r", encoding="utf-8") as f:
        input_payload = json.load(f)

    # Собираем весь контекст для прогона
    md_standards = load_md_standards()
    schemas = load_contract_schemas()
    org_context = load_organizational_context()

    context = {
        "run_id": run_id,
        "input": input_payload,
        "md_standards": md_standards,
        "schemas": schemas,
        "org_context": org_context
    }
    
    save_md(run_dir / "step_00_understanding.md", summarize_understanding(context))
    print("✅ STEP-0: Context, standards, and schemas loaded.")

    mem = Memory(run_dir)
    artifacts = {}
    step_index = 0

    while step_index < len(WORKFLOW_STEPS):
        step_name = WORKFLOW_STEPS[step_index]
        print(f"\n--- Running step ({step_index + 1}/{len(WORKFLOW_STEPS)}): {step_name} ---")
        
        try:
            step = load_step(step_name)
        except Exception as e:
            print(f"FATAL: Could not load step '{step_name}'. Error: {e}")
            print("Skipping to next step...")
            step_index += 1
            continue

        start_time = time.monotonic()
        
        context["current_standard_text"] = context["md_standards"].get(step_name, "")
        context["current_schema"] = context["schemas"].get(step_name, {})
        context.pop("reflection_notes", None)

        # Цикл попыток с рефлексией
        for attempt in range(MAX_REFLECTION_LOOPS + 1):
            try:
                result = step.run(context, artifacts)
                
                # Валидация результата
                schema_score, checklist_score, validation_notes = validate_artifact(
                    step_name, result.data, context["schemas"]
                )
                final_score = min(schema_score, checklist_score, result.score)
                
                # Проверяем тригеры для HITL
                hitl_triggered = False
                trigger_reason = ""
                
                # Высокая неопределенность - просим пользователя вмешаться
                if result.uncertainty > UNCERTAINTY_THRESHOLD_ASK:
                    hitl_triggered = True
                    trigger_reason = f"High uncertainty: {result.uncertainty:.2f} > {UNCERTAINTY_THRESHOLD_ASK}"
                # Средняя неопределенность - запрашиваем подтверждение
                elif result.uncertainty > HITL_UNCERTAINTY_TRIGGER:
                    hitl_triggered = True
                    trigger_reason = f"Moderate uncertainty: {result.uncertainty:.2f} > {HITL_UNCERTAINTY_TRIGGER}"
                # Критический шаг - всегда требует подтверждения
                elif step_name in CRITICAL_STEPS_FOR_HITL:
                    hitl_triggered = True
                    trigger_reason = f"Critical step requiring approval: {step_name}"
                # Низкая оценка качества - требует подтверждения
                elif final_score < (QUALITY_THRESHOLD + HITL_SCORE_BUFFER):
                    hitl_triggered = True
                    trigger_reason = f"Score near threshold: {final_score:.2f} < {QUALITY_THRESHOLD + HITL_SCORE_BUFFER}"

                # Обработка HITL
                if hitl_triggered:
                    print(f"🕹️ [HITL] Approval required: {trigger_reason}.")
                    print(json.dumps(result.data, indent=2, ensure_ascii=False))
                    if not confirm_action("Approve this result?"):
                        user_feedback = input("   Please provide brief feedback for reflection: ")
                        context["reflection_notes"] = f"User rejected the output. Feedback: '{user_feedback}'. Self-critique was: {result.notes}"
                        print("   User rejected. Triggering reflection...")
                        continue

                # Проверяем качество результата
                if final_score >= QUALITY_THRESHOLD:
                    artifacts[step_name] = result.data
                    save_artifact(run_dir, step_name, result, time.monotonic() - start_time)
                    mem.log_event(f"{step_name}_SUCCESS", result.model_dump())
                    step_index += 1
                    break
                else:
                    notes = f"Score {final_score:.2f} < {QUALITY_THRESHOLD}. {validation_notes}. Self-critique: {result.notes}"
                    if attempt < MAX_REFLECTION_LOOPS:
                        print(f"🤔 [REFLECT] {notes}. Retrying (attempt {attempt + 2}/{MAX_REFLECTION_LOOPS + 1})...")
                        context["reflection_notes"] = notes
                        append_lesson(f"Lesson from {step_name} (reflection): {notes}")
                    else:
                        print(f"❌ [FAIL] Max reflections reached. {notes}.")
                        print("   Saving failed artifact and moving to the next step.")
                        artifacts[step_name] = result.data
                        save_artifact(run_dir, f"{step_name}_FAILED", result, time.monotonic() - start_time)
                        mem.log_event(f"{step_name}_FAIL", result.model_dump())
                        step_index += 1
                        break
                        
            except Exception as e:
                print(f"❌ [ERROR] Step {step_name} failed with exception: {e}")
                mem.log_event(f"{step_name}_ERROR", {"error": str(e), "attempt": attempt})
                if attempt >= MAX_REFLECTION_LOOPS:
                    print("   Max attempts reached. Moving to next step.")
                    step_index += 1
                    break

    print(f"\n✅ Workflow finished. Artifacts saved in: {run_dir}")

if __name__ == "__main__":
    main()