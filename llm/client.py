import json
import time
from openai import OpenAI
from openai.types.chat import ChatCompletion
import config

class LLMError(Exception):
    """Кастомное исключение для ошибок LLM."""
    pass

class LLM:
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise LLMError("OPENAI_API_KEY is not configured")
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.max_retries = 3
        self.retry_delay = 2  # секунды
        
    def generate_json(self, system_prompt: str, user_prompt: str, org_context: str, 
                      standard_schema: dict, standard_text: str = "", reflection_notes: str = "") -> dict:
        """
        Генерирует JSON-ответ от LLM с учетом рефлексии и текстовых стандартов.
        Включает retry-логику и улучшенную обработку ошибок.
        """
        
        # Если есть заметки для рефлексии, добавляем их в промпт
        if reflection_notes:
            user_prompt += f"""

CRITICAL FEEDBACK ON PREVIOUS ATTEMPT:
---
{reflection_notes}
---
You MUST address this feedback in your new response.
"""

        full_system_prompt = self._build_system_prompt(
            system_prompt, org_context, standard_text, standard_schema
        )

        # Retry loop
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return self._make_api_call(full_system_prompt, user_prompt, attempt)
                
            except Exception as e:
                last_error = e
                print(f"🔄 [RETRY] Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    break
        
        # Если все попытки провалились
        error_message = f"LLM failed after {self.max_retries} attempts. Last error: {str(last_error)}"
        return {
            "data": {"error": error_message, "fallback_used": True},
            "score": 0.0,
            "uncertainty": 1.0,
            "notes": error_message
        }
    
    def _build_system_prompt(self, base_prompt: str, org_context: str, 
                           standard_text: str, standard_schema: dict) -> str:
        """Строит полный системный промпт."""
        return f"""
{base_prompt}

You MUST follow these instructions:
1. Think step-by-step to analyze the user request.
2. Your final output MUST be a single, valid JSON object. Do not include any text, explanations, or markdown formatting before or after the JSON.
3. Your output MUST strictly adhere to the provided JSON Schema (STANDARD section).
4. You MUST also consider the quality guidelines and checklists from the TEXTUAL STANDARD section to ensure the substance of your response is high quality.
5. Include these meta-fields in your JSON response for self-assessment:
   - "self_assessed_score": float between 0.0 and 1.0
   - "uncertainty_score": float between 0.0 and 1.0  
   - "reasoning": string with brief explanation of your approach

ORGANIZATIONAL CONTEXT (for background):
---
{org_context or "No organizational context provided."}
---

TEXTUAL STANDARD (Quality Guidelines):
---
{standard_text or "No textual standard provided."}
---

STANDARD (JSON Schema for output format):
---
{json.dumps(standard_schema, indent=2) if standard_schema else "No schema provided."}
---
"""

    def _make_api_call(self, system_prompt: str, user_prompt: str, attempt: int) -> dict:
        """Выполняет API вызов к OpenAI с обработкой ошибок."""
        try:
            completion = self.client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5 + (attempt * 0.1),  # Увеличиваем температуру при повторах
                max_tokens=4000,
                timeout=60
            )
            
            response_text = completion.choices[0].message.content
            if not response_text:
                raise LLMError("Empty response from LLM")
                
            data = json.loads(response_text)
            
            # Валидируем наличие базовых полей
            if not isinstance(data, dict):
                raise LLMError("Response is not a valid JSON object")
            
            # Извлекаем мета-поля и удаляем их из итоговых данных
            score = data.pop("self_assessed_score", 0.8) 
            uncertainty = data.pop("uncertainty_score", 0.2)
            notes = data.pop("reasoning", "No reasoning provided by LLM.")
            
            # Валидируем диапазоны мета-полей
            score = max(0.0, min(1.0, float(score)))
            uncertainty = max(0.0, min(1.0, float(uncertainty)))

            return {
                "data": data,
                "score": score,
                "uncertainty": uncertainty,
                "notes": notes
            }

        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid JSON in LLM response: {str(e)}. Response: {response_text[:200]}...")
        except Exception as e:
            if "rate limit" in str(e).lower():
                time.sleep(60)  # Ждем при превышении лимитов
                raise LLMError(f"Rate limit exceeded: {str(e)}")
            else:
                raise LLMError(f"API call failed: {str(e)}")
    
    def estimate_tokens(self, text: str) -> int:
        """Приблизительная оценка количества токенов в тексте."""
        return len(text.split()) * 1.3  # Грубая оценка