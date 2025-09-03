"""
Система логирования для AI Marketing Agent.
Обеспечивает трассировку событий и сохранение в events.jsonl.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum


class LogLevel(Enum):
    """Уровни логирования"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventLogger:
    """Логгер событий для сохранения в events.jsonl"""
    
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.events_file = run_dir / "events.jsonl"
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Настройка стандартного Python логгера"""
        log_file = self.run_dir / "memory.log"
        
        # Создаем логгер
        self.logger = logging.getLogger(f"ai_agent_{self.run_dir.name}")
        self.logger.setLevel(logging.DEBUG)
        
        # Очищаем существующие обработчики
        self.logger.handlers.clear()
        
        # Создаем обработчик для файла
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        
        # Создаем обработчик для консоли
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Формат логов
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Добавляем обработчики
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_event(self, event_type: str, data: Dict[str, Any], level: LogLevel = LogLevel.INFO) -> None:
        """Логирует событие в events.jsonl и memory.log"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "level": level.value,
            "data": data
        }
        
        # Записываем в events.jsonl
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        # Логируем в стандартный логгер
        message = f"{event_type}: {json.dumps(data, ensure_ascii=False)}"
        if level == LogLevel.DEBUG:
            self.logger.debug(message)
        elif level == LogLevel.INFO:
            self.logger.info(message)
        elif level == LogLevel.WARNING:
            self.logger.warning(message)
        elif level == LogLevel.ERROR:
            self.logger.error(message)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(message)
    
    def log_step_start(self, step_name: str, context: Dict[str, Any]) -> None:
        """Логирует начало выполнения шага"""
        self.log_event("step_start", {
            "step_name": step_name,
            "context_keys": list(context.keys())
        })
    
    def log_step_end(self, step_name: str, result: Dict[str, Any], execution_time: float) -> None:
        """Логирует завершение выполнения шага"""
        self.log_event("step_end", {
            "step_name": step_name,
            "score": result.get("score", 0.0),
            "execution_time": execution_time,
            "notes": result.get("notes", "")
        })
    
    def log_llm_call(self, step_name: str, prompt_length: int, response_length: int, tokens_used: Optional[int] = None) -> None:
        """Логирует вызов LLM"""
        self.log_event("llm_call", {
            "step_name": step_name,
            "prompt_length": prompt_length,
            "response_length": response_length,
            "tokens_used": tokens_used
        })
    
    def log_validation(self, step_name: str, schema_score: float, checklist_score: float, evidence_score: float, notes: str) -> None:
        """Логирует результат валидации"""
        self.log_event("validation", {
            "step_name": step_name,
            "schema_score": schema_score,
            "checklist_score": checklist_score,
            "evidence_score": evidence_score,
            "notes": notes
        })
    
    def log_hitl_trigger(self, step_name: str, reason: str, uncertainty: float) -> None:
        """Логирует срабатывание Human-in-the-Loop"""
        self.log_event("hitl_trigger", {
            "step_name": step_name,
            "reason": reason,
            "uncertainty": uncertainty
        }, LogLevel.WARNING)
    
    def log_error(self, step_name: str, error: str, traceback: Optional[str] = None) -> None:
        """Логирует ошибку"""
        self.log_event("error", {
            "step_name": step_name,
            "error": error,
            "traceback": traceback
        }, LogLevel.ERROR)


def get_logger(run_dir: Path) -> EventLogger:
    """Получить логгер для указанной директории запуска"""
    return EventLogger(run_dir)


