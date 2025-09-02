import json, subprocess, sys, pathlib, shlex

def run_legacy_interview(task_path: str, out_dir: str, cmd: str, timeout_sec: int) -> None:
    """
    task_path: artifacts/<run_id>/02_interview/<segment_id>/interview_task.json
    out_dir:   artifacts/<run_id>/02_interview/<segment_id>/
    cmd:       из configs/ajtd.yaml (interview.legacy.cmd)
    side-effects: создает interview_raw.md и interview.json в out_dir
    """
    pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
    # Запускаем ваш CLI как вы делали в cmd:
    full_cmd = f'{cmd} --input {shlex.quote(task_path)} --outdir {shlex.quote(out_dir)}'
    try:
        subprocess.run(full_cmd, shell=True, check=True, timeout=timeout_sec)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Legacy CLI failed: {e}") from e

    # Проверяем выходы:
    iraw = pathlib.Path(out_dir, "interview_raw.md")
    ij = pathlib.Path(out_dir, "interview.json")
    if not iraw.exists() or not ij.exists():
        raise FileNotFoundError("Legacy CLI did not produce interview_raw.md and/or interview.json")
    # Базовая валидация JSON (схема проверяется в шаге):
    json.loads(ij.read_text(encoding="utf-8"))
