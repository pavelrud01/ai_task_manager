from pathlib import Path
import json
import time
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, Union

def promote_guide_artifacts(artifact: Dict[str, Any], promote_to_path: str, run_dir: Path) -> None:
    """
    Копирует финальный guide (markdown) в проектные стандарты и создаёт .index.json рядом.
    """
    md = artifact.get("markdown", "")
    meta = artifact.get("meta", {})
    sections = artifact.get("sections", {})
    sources = artifact.get("sources", [])

    out_md = Path(promote_to_path)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md, encoding="utf-8")

    index_path = out_md.with_suffix(".index.json")
    index_obj = {
        "meta": meta,
        "sections": list(sections.keys()),
        "sources": sources
    }
    index_path.write_text(json.dumps(index_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    # копии в artifacts/run_dir для трассировки
    (run_dir / out_md.name).write_text(md, encoding="utf-8")
    (run_dir / index_path.name).write_text(json.dumps(index_obj, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_run_dir(run_id: str = None) -> Path:
    """
    Создает директорию для запуска и возвращает путь к ней.
    Если run_id не указан, генерирует автоматически.
    """
    if not run_id:
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 10000}"
    
    run_dir = Path("artifacts") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_md(path: Path, content: str) -> None:
    """
    Сохраняет Markdown контент в файл.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def save_artifact(run_dir: Path, step_name: str, result: Any, execution_time: float) -> None:
    """
    Сохраняет артефакт шага в JSON формате.
    """
    artifact_path = run_dir / f"{step_name}.json"
    
    artifact_data = {
        "step_name": step_name,
        "timestamp": datetime.now().isoformat(),
        "execution_time": execution_time,
        "score": getattr(result, 'score', 0.0),
        "uncertainty": getattr(result, 'uncertainty', 0.0),
        "notes": getattr(result, 'notes', ''),
        "data": getattr(result, 'data', {})
    }
    
    artifact_path.write_text(json.dumps(artifact_data, ensure_ascii=False, indent=2), encoding="utf-8")


def confirm_action(prompt: str) -> bool:
    """
    Запрашивает подтверждение действия у пользователя.
    Возвращает True если пользователь подтвердил, False если отказался.
    """
    while True:
        response = input(f"{prompt} (y/n): ").lower().strip()
        if response in ['y', 'yes', 'да', 'д']:
            return True
        elif response in ['n', 'no', 'нет', 'н']:
            return False
        else:
            print("Please answer 'y' or 'n'")


def append_lesson(lesson: str) -> None:
    """
    Добавляет урок в файл lessons.md в корне проекта.
    """
    lessons_file = Path("lessons.md")
    
    if lessons_file.exists():
        content = lessons_file.read_text(encoding="utf-8")
    else:
        content = "# Lessons Learned\n\n"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_lesson = f"\n## {timestamp}\n{lesson}\n"
    
    lessons_file.write_text(content + new_lesson, encoding="utf-8")


def new_run_id() -> str:
    """Generate new run ID with timestamp format"""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def make_run_dirs(artifacts_root: str, run_id: str) -> Dict[str, str]:
    """Create run directory structure and return paths"""
    base = Path(artifacts_root, run_id)
    sub = ["00_ingest", "01_standard", "02_interview", "03_ljd", "04_refine", "05_cluster", "_meta"]
    for s in sub: 
        (base / s).mkdir(parents=True, exist_ok=True)
    return {k: str(base / k) for k in sub}


def write_manifest(artifacts_root: str, run_id: str, update: Dict[str, Any]) -> None:
    """Write or update manifest.json for the run"""
    path = Path(artifacts_root, run_id, "_meta", "manifest.json")
    data = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    # Мерджим простым способом:
    data.update(update)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def symlink_latest(artifacts_root: str, run_id: str) -> None:
    """Create symlink 'latest' pointing to current run"""
    latest = Path(artifacts_root, "latest")
    target = Path(artifacts_root, run_id)
    # На Windows, если симлинк недоступен — делаем копию или используем junction по вашей политике:
    if latest.exists() or latest.is_symlink():
        try:
            latest.unlink()
        except Exception:
            shutil.rmtree(latest, ignore_errors=True)
    try:
        latest.symlink_to(target, target_is_directory=True)
    except Exception:
        # fallback: копия (если допустимо)
        shutil.copytree(target, latest)
