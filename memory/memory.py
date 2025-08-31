"""
Модуль памяти для логирования прогонов workflow
"""

import json
from pathlib import Path
from datetime import datetime

class Memory:
    def __init__(self, run_dir: Path):
        self.log_file = run_dir / "run_log.jsonl"

    def log_event(self, event_type: str, data: dict):
        """Записывает событие в лог-файл в формате JSON Lines."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        }
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
