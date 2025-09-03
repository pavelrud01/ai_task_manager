"""
STEP: Human Readable Export
Автоматический экспорт human-readable версий артефактов
"""

from .base import BaseStep, StepResult
from pathlib import Path
from typing import Dict, Any, List
from utils.human_readable_exporter import export_multiple_human_readable, create_human_readable_index


class Step(BaseStep):
    name = "step_export_human_readable"
    
    def __init__(self):
        pass
    
    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Создает human-readable версии всех артефактов.
        
        Вход:
        - artifacts/* (все артефакты из предыдущих шагов)
        
        Выход:
        - artifacts/exports/human_readable/*_HUMAN_READABLE.md
        - artifacts/exports/human_readable/HUMAN_READABLE_INDEX.md
        """
        run_dir: Path = context.get("run_dir")
        if not run_dir:
            return StepResult(
                score=0.0,
                notes="No run_dir in context"
            )
        
        # Создаем директорию для экспорта
        exports_dir = run_dir / "exports" / "human_readable"
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        # Определяем ключевые шаги для экспорта
        key_steps = [
            "step_03_interview_collect",
            "step_04_jtbd", 
            "step_05_segments",
            "step_06_decision_mapping"
        ]
        
        # Собираем артефакты для экспорта
        artifacts_to_export = {}
        for step_name in key_steps:
            if step_name in artifacts:
                artifacts_to_export[step_name] = artifacts[step_name]
        
        if not artifacts_to_export:
            return StepResult(
                score=0.3,
                notes="No key artifacts found for human-readable export"
            )
        
        try:
            # Создаем метаданные
            metadata = {
                "run_id": context.get("run_id", ""),
                "project_id": context.get("project_id", ""),
                "model_name": context.get("MODEL_NAME", ""),
                "export_timestamp": context.get("timestamp", "")
            }
            
            # Экспортируем human-readable версии
            created_files = export_multiple_human_readable(
                artifacts_to_export, exports_dir, metadata
            )
            
            # Создаем индексный файл
            index_file = create_human_readable_index(created_files, exports_dir)
            
            # Подготавливаем результат
            result_data = {
                "exported_steps": list(artifacts_to_export.keys()),
                "created_files": [str(f) for f in created_files],
                "index_file": str(index_file),
                "export_dir": str(exports_dir)
            }
            
            return StepResult(
                data=result_data,
                score=1.0,
                notes=f"Successfully exported {len(created_files)} human-readable files",
                uncertainty=0.0
            )
            
        except Exception as e:
            return StepResult(
                score=0.0,
                notes=f"Error creating human-readable exports: {str(e)}",
                uncertainty=1.0
            )

