# validators/validate.py
from __future__ import annotations
from pathlib import Path
from typing import Tuple, Dict
import json

from jsonschema import validate, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = REPO_ROOT / "contracts"

# ---- Общие утилиты ----

def _load_schema(schema_path: Path) -> dict:
    try:
        return json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to read schema {schema_path}: {e}")

def validate_with_schema_path(schema_path: Path, data: dict) -> tuple[float, str]:
    """
    Валидация произвольного объекта по указанной схеме (для гайдов и т.п.)
    Возвращает (schema_score, notes).
    """
    if not schema_path.exists():
        return 1.0, f"Schema file not found: {schema_path.name} (skipped)"
    try:
        schema = _load_schema(schema_path)
        validate(instance=data, schema=schema)
        return 1.0, "Schema OK"
    except ValidationError as e:
        return 0.0, f"Schema failed: {e.message}"
    except Exception as e:
        return 0.0, f"Schema error: {e}"

def _schema_for_step(step_name: str) -> Path:
    return CONTRACTS_DIR / f"{step_name}.schema.json"

# ---- Основной валидатор артефактов шага ----

def validate_artifact(step_name: str, data: dict, standards: Dict[str, str]) -> Tuple[float, float, str]:
    """
    Возвращает (schema_score, checklist_score, notes)
    - schema_score: 0..1 по JSON-схеме из /contracts/{step_name}.schema.json
    - checklist_score: 0..1 простые sanity-checks по ключам
    """
    schema_path = _schema_for_step(step_name)
    schema_score, schema_notes = validate_with_schema_path(schema_path, data)

    # Простые чеклисты на ключевых шагах (расширяйте по мере необходимости)
    checklist_score = 1.0
    checklist_notes = "OK"

    if step_name == "step_04_jtbd":
        # ожидаем наличие корневых узлов
        required = ["big_jobs", "medium_jobs", "small_jobs", "evidence"]
        missing = [k for k in required if k not in data]
        if missing:
            checklist_score = 0.4
            checklist_notes = f"Missing keys: {missing}"
        else:
            # минимальные требования к количеству Big Jobs
            if isinstance(data.get("big_jobs"), list) and len(data["big_jobs"]) < 2:
                checklist_score = 0.7
                checklist_notes = "Too few big_jobs (<2)."

    if step_name == "step_05_segments":
        if not isinstance(data.get("segments"), list) or not data["segments"]:
            checklist_score = 0.4
            checklist_notes = "No segments generated."

    notes = f"Schema: {schema_notes} | Checklist: {checklist_notes}"
    return schema_score, checklist_score, notes
import json
from pathlib import Path
from jsonschema import validate

def validate_with_schema_path(schema_path: Path, obj) -> tuple[float, str]:
    """Возвращает (schema_score, schema_notes)"""
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as e:
        return 0.5, f"No/invalid schema: {e}"
    try:
        validate(instance=obj, schema=schema)
        return 1.0, "Schema OK"
    except Exception as e:
        return 0.0, f"Schema failed: {e}"
