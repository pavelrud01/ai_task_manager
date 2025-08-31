from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Any, Optional

class StepResult(BaseModel):
    """
    Стандартизированный результат выполнения шага, совместимый с llm.client и main.py.
    """
    data: dict[str, Any] = Field(default_factory=dict, description="Основные данные, результат работы шага (артефакт).")
    score: float = Field(default=1.0, description="Оценка качества результата от 0.0 до 1.0, сгенерированная LLM или самим шагом.")
    uncertainty: float = Field(default=0.0, description="Оценка неопределенности от 0.0 до 1.0. Высокое значение требует HITL.")
    notes: str = Field(default="", description="Заметки, самокритика или пояснения от LLM/шага.")
    rollback_to: Optional[str] = Field(default=None, description="Если указано, оркестратор должен откатиться к этому шагу.")

class BaseStep(ABC):
    """
    Базовый абстрактный класс для всех шагов workflow.
    Определяет единый интерфейс 'run'.
    """
    name: str = "base_step"

    def __init__(self):
        # В дочерних классах здесь можно инициализировать LLM-клиент или другие ресурсы
        pass

    @abstractmethod
    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Основной метод выполнения шага.
        
        Args:
            context (dict): Общий контекст выполнения (стандарты, схемы, инпут, org_context).
            artifacts (dict): Словарь с `data` из результатов предыдущих успешных шагов.
            
        Returns:
            StepResult: Структурированный результат выполнения шага.
        """
        pass