import json
from datetime import datetime
from pathlib import Path
from typing import Any

PROMPTS_CONTEXT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "context"

def ensure_run_dir(run_id: str) -> Path:
    base = Path("artifacts") / run_id
    base.mkdir(parents=True, exist_ok=True)
    return base

def save_artifact(run_dir: Path, step_name: str, result: Any, duration: float):
    path = run_dir / f"{step_name}.json"
    data_to_save = result.model_dump()
    data_to_save['meta'] = {'duration_sec': round(duration, 2)}
    with path.open("w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)

def save_json(path: Path, data: dict):
    """Простая утилита для сохранения любого словаря в JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_md(path: Path, text: str):
    path.write_text(text, encoding="utf-8")

def confirm_action(prompt: str) -> bool:
    while True:
        resp = input(f"{prompt} [y/n]: ").lower().strip()
        if resp in ["y", "yes"]: return True
        if resp in ["n", "no"]: return False

def append_lesson(lesson: str):
    lessons_path = PROMPTS_CONTEXT_PATH / "Lessons.md"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    with lessons_path.open("a", encoding="utf-8") as f:
        f.write(f"\n\n---\n**Lesson learned at {timestamp}:**\n{lesson}\n")
