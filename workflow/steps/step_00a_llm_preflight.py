from .base import BaseStep, StepResult
from llm.client import LLM
import config

class Step(BaseStep):
    name = "step_00a_llm_preflight"
    
    def __init__(self):
        self.llm = LLM()
    
    def run(self, context, artifacts):
        """
        Выполняет минимальную проверку доступности LLM перед основными шагами.
        Делает крошечный запрос (1-2 токена) для проверки подключения.
        """
        try:
            # Получаем модель из контекста или используем дефолтную
            model_name = context.get("MODEL_NAME") or config.MODEL_NAME
            
            # Самый короткий вызов для проверки доступности
            resp = self.llm.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "pong"}],
                max_tokens=1
            )
            
            # Успешный результат
            data = {
                "provider": "openai",
                "model": model_name,
                "ok": True
            }
            
            return StepResult(
                data=data, 
                score=1.0, 
                notes="LLM preflight check passed", 
                uncertainty=0.0
            )
            
        except Exception as e:
            # Ошибка подключения
            data = {
                "provider": "openai",
                "model": context.get("MODEL_NAME") or config.MODEL_NAME,
                "ok": False,
                "error": str(e)
            }
            
            return StepResult(
                data=data,
                score=0.0, 
                notes="LLM preflight check failed", 
                uncertainty=1.0
            )

