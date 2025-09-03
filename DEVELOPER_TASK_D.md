# ТЗ для разработчика: Доработка пайплайна до интервью

## D1. Включить два шага до интервью

### D1.1. step_00a_llm_preflight

**Файл**: `workflow/steps/step_00a_llm_preflight.py`

**Статус**: ✅ УЖЕ РЕАЛИЗОВАН

**Проверить**:
- [ ] Файл существует и содержит код-скелет
- [ ] Добавлен в `WORKFLOW_STEPS` в `config.py` сразу после `step_00_compliance_check`
- [ ] Тестируется загрузка: `python -c 'from workflow.registry import load_step; s=load_step("step_00a_llm_preflight"); print(f"Step loaded: {s.name}")'`

### D1.2. step_02a_guide_compile

**Файл**: `workflow/steps/step_02a_guide_compile.py`

**Статус**: ❌ ТРЕБУЕТ РЕАЛИЗАЦИИ

**Схема**: `contracts/step_02a_guide_compile.schema.json` (уже существует)

**Вход**:
```python
# Из context["input"]["guide"] - путь к гайду
guide_path = context["input"]["guide"]  # например: "prompts/guides/[v3.3] Гайд AJTBD-интервью для B2C-продуктов.md"
```

**Действие**:
1. **Загрузить гайд**: `load_guide_markdown(guide_path)`
2. **Распарсить MD**: `parse_guide_markdown(guide_md)` (функция уже есть в `validators/standards_loader.py`)
3. **Нормализовать секции**: привести к структуре из схемы
4. **Проверить по схеме**: `validate_artifact(data, "step_02a_guide_compile")`
5. **Зафиксировать метаданные**:
   - `standard_id`: имя файла гайда
   - `source_path`: полный путь к файлу
   - `fingerprint`: SHA256 содержимого

**Выход**:
- `artifacts/step_02a_guide_compile.json` - структурированные данные по схеме
- `step_02a_guide_compile_HUMAN_READABLE.md` - человеко-читаемая версия

**Код-скелет**:
```python
# workflow/steps/step_02a_guide_compile.py
from .base import BaseStep, StepResult
from pathlib import Path
import hashlib
from validators.standards_loader import load_guide_markdown, parse_guide_markdown
from validators.validate import validate_artifact
from utils.standard_tracking import add_standard_metadata

class Step(BaseStep):
    name = "step_02a_guide_compile"
    
    def run(self, context: dict, artifacts: dict) -> StepResult:
        # 1. Получить путь к гайду
        guide_path = context["input"]["guide"]
        
        # 2. Загрузить и распарсить
        guide_md = load_guide_markdown(guide_path)
        meta, sections = parse_guide_markdown(guide_md)
        
        # 3. Нормализовать под схему
        data = {
            "meta": meta,
            "sections": sections,
            "sources": [{
                "path": guide_path,
                "sha256": hashlib.sha256(guide_md.encode()).hexdigest()
            }],
            "markdown": guide_md
        }
        
        # 4. Валидация
        validation_result = validate_artifact(data, "step_02a_guide_compile")
        if not validation_result["valid"]:
            return StepResult(score=0.0, notes=f"Validation failed: {validation_result['errors']}")
        
        # 5. Добавить метаданные стандарта
        data = add_standard_metadata(
            data, 
            self.name, 
            guide_md, 
            Path(guide_path), 
            context
        )
        
        return StepResult(
            data=data,
            score=1.0,
            notes="Guide compiled successfully",
            uncertainty=0.0
        )
```

**Интеграция**:
- [ ] Добавить в `WORKFLOW_STEPS` в `config.py` перед `step_03_interview_collect`
- [ ] Обновить `step_03_interview_collect.py` чтобы он использовал скомпилированный гайд из артефактов

## D2. Жёсткая привязка стандартов

### D2.1. Расширить validators/standards_loader.py

**Статус**: ✅ ЧАСТИЧНО РЕАЛИЗОВАНО (Knowledge Bank уже добавлен)

**Добавить функцию**:
```python
def standard_fingerprint(text: str) -> str:
    """Вычисляет SHA256 отпечаток текста стандарта."""
    import hashlib
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
```

**Обновить load_organizational_context()**:
```python
def load_organizational_context() -> Dict[str, str]:
    # ... существующий код ...
    
    # Добавить сканирование prompts/context/knowledge/**
    knowledge_bank = load_knowledge_bank()  # ✅ УЖЕ РЕАЛИЗОВАНО
    result.update(knowledge_bank)
    
    return result
```

### D2.2. Добавить метаданные стандартов в каждый шаг

**Где добавлять**:
- `step_02a_guide_compile` - для гайдов
- `step_03_interview_collect` - для стандартов интервью
- `step_04_jtbd` - для стандартов JTBD
- `step_05_segments` - для стандартов сегментации
- `step_06_decision_mapping` - для стандартов карт решений

**Структура метаданных**:
```python
"standard": {
    "id": "<имя файла>",           # например: "interview_ajtbd.md"
    "path": "<полный путь>",       # например: "prompts/standards/interview_ajtbd.md"
    "fingerprint": "<sha256>"      # например: "a1b2c3d4e5f6..."
}
```

**Использование утилиты**:
```python
from utils.standard_tracking import add_standard_metadata

# В каждом шаге
data = add_standard_metadata(
    data, 
    step_name, 
    standard_text, 
    standard_path, 
    context
)
```

## D3. Порядок выполнения

**Текущий порядок** (в `config.py`):
```python
WORKFLOW_STEPS = [
    "step_00_compliance_check",
    "step_00a_llm_preflight",        # ✅ УЖЕ ДОБАВЛЕН
    "step_02_extract",
    "step_02a_guide_compile",        # ❌ ДОБАВИТЬ
    "step_02b_initial_classification",
    "step_03_interview_collect",
    # ... остальные шаги
]
```

## D4. Тестирование

**Команды для проверки**:
```powershell
# 1. Проверить загрузку step_00a_llm_preflight
& .\.venv\Scripts\python.exe -c 'from workflow.registry import load_step; s=load_step("step_00a_llm_preflight"); print(f"Step loaded: {s.name}")'

# 2. Проверить загрузку step_02a_guide_compile (после реализации)
& .\.venv\Scripts\python.exe -c 'from workflow.registry import load_step; s=load_step("step_02a_guide_compile"); print(f"Step loaded: {s.name}")'

# 3. Проверить Knowledge Bank
& .\.venv\Scripts\python.exe -c 'from validators.standards_loader import load_organizational_context; ctx=load_organizational_context(); print("Files:", len(ctx))'

# 4. Проверить полный пайплайн
& .\.venv\Scripts\python.exe scripts/run.py Reading
```

## D5. Критерии готовности

- [ ] `step_00a_llm_preflight` загружается без ошибок
- [ ] `step_02a_guide_compile` реализован и загружается без ошибок
- [ ] Оба шага добавлены в `WORKFLOW_STEPS` в правильном порядке
- [ ] Knowledge Bank загружается (7 файлов: 3 базовых + 4 из ajtbd/)
- [ ] Функция `standard_fingerprint()` добавлена в `standards_loader.py`
- [ ] Метаданные стандартов добавляются в артефакты ключевых шагов
- [ ] Полный пайплайн запускается без ошибок

## D3. Экспорт человеко-читаемых отчётов

**Статус**: ❌ ТРЕБУЕТ РЕАЛИЗАЦИИ

**Цель**: После каждого JSON артефакта создавать `*_HUMAN_READABLE.md` с резюме и метаданными.

**Где реализовать**:
- `step_03_interview_collect` - после сохранения JSON артефакта
- `step_04_jtbd` - после сохранения JSON артефакта  
- `step_05_segments` - после сохранения JSON артефакта
- `step_06_decision_mapping` - после сохранения JSON артефакта

**Использовать**: `utils/io.save_md()` (уже существует)

**Структура human-readable файла**:
```markdown
# [STEP_NAME] - Human Readable Report

## Резюме
[Краткое описание результатов шага]

## Использованный стандарт
- **ID**: [standard_id]
- **Путь**: [source_path]  
- **Fingerprint**: [fingerprint]

## Источники данных
[Список evidence_refs[] с цитатами]

## Red Flags / Coverage Checklist
- [ ] [Проверка 1]
- [ ] [Проверка 2]
- [ ] [Проверка 3]

## Детальные данные
[Структурированное представление ключевых данных]
```

**Код-шаблон**:
```python
# В каждом шаге после сохранения JSON артефакта
from utils.io import save_md

def _create_human_readable_report(step_name: str, data: dict, run_dir: Path) -> None:
    """Создает human-readable версию артефакта."""
    
    # Извлекаем метаданные
    metadata = data.get("__metadata", {})
    standard_id = metadata.get("standard_id", "N/A")
    source_path = metadata.get("source_path", "N/A")
    fingerprint = metadata.get("fingerprint", "N/A")[:16] + "..."
    
    # Создаем контент
    content = f"""# {step_name.upper()} - Human Readable Report

## Резюме
{_generate_summary(data, step_name)}

## Использованный стандарт
- **ID**: {standard_id}
- **Путь**: {source_path}
- **Fingerprint**: {fingerprint}

## Источники данных
{_format_evidence_refs(data)}

## Red Flags / Coverage Checklist
{_generate_checklist(data, step_name)}

## Детальные данные
{_format_detailed_data(data, step_name)}
"""
    
    # Сохраняем
    md_path = run_dir / f"{step_name}_HUMAN_READABLE.md"
    save_md(md_path, content)
```

## D4. Обязательные поля longform

### D4.1. USER TEMPLATE

**Файл**: `prompts/standards/user_template.md`

**Статус**: ✅ УЖЕ РЕАЛИЗОВАН

**Проверить**: Файл содержит полную структуру для маппинга интервью → longform

### D4.2. Обязательные поля в step_04_jtbd

**Файл**: `workflow/steps/step_04_jtbd.py`

**Статус**: ❌ ТРЕБУЕТ ДОРАБОТКИ

**Обязательные поля для каждого job**:
```python
{
    "level": "Big|Core|Medium|Small|Micro",           # согласно jtbd_levels.md
    "level_rationale": "Обоснование выбора уровня",   # объяснение классификации
    "evidence_refs": [
        {
            "quote": "Прямая цитата из интервью",     # точная цитата
            "confidence": 0.8,                        # уверенность 0-1
            "tags": ["source:interview", "phase:problem", "strength:strong"]  # канонические теги
        }
    ]
}
```

**Проблема**: Код падает без корпуса интервью

**Решение**: Добавить fallback-логику для случаев без интервью:
```python
# В step_04_jtbd.py
if not interview_corpus:
    # Fallback: создать базовые jobs на основе input данных
    fallback_jobs = _create_fallback_jobs(context)
    return StepResult(data={"jobs": fallback_jobs}, ...)

def _create_fallback_jobs(context: dict) -> List[dict]:
    """Создает базовые jobs когда нет интервью."""
    return [
        {
            "id": "fallback_job_1",
            "title": "Основная задача пользователя",
            "level": "Core",
            "level_rationale": "Создано на основе анализа продукта",
            "evidence_refs": [],
            "description": f"Пользователи {context['input'].get('product', 'продукта')} решают основную задачу"
        }
    ]
```

## D5. Порядок выполнения

**Текущий порядок** (в `config.py`):
```python
WORKFLOW_STEPS = [
    "step_00_compliance_check",
    "step_00a_llm_preflight",        # ✅ УЖЕ ДОБАВЛЕН
    "step_02_extract",
    "step_02a_guide_compile",        # ❌ ДОБАВИТЬ
    "step_02b_initial_classification",
    "step_03_interview_collect",     # ❌ ДОБАВИТЬ human-readable
    "step_04_jtbd",                  # ❌ ДОБАВИТЬ human-readable + обязательные поля
    "step_05_segments",              # ❌ ДОБАВИТЬ human-readable
    "step_06_decision_mapping",      # ❌ ДОБАВИТЬ human-readable
    # ... остальные шаги
]
```

## D6. Тестирование

**Команды для проверки**:
```powershell
# 1. Проверить загрузку step_00a_llm_preflight
& .\.venv\Scripts\python.exe -c 'from workflow.registry import load_step; s=load_step("step_00a_llm_preflight"); print(f"Step loaded: {s.name}")'

# 2. Проверить загрузку step_02a_guide_compile (после реализации)
& .\.venv\Scripts\python.exe -c 'from workflow.registry import load_step; s=load_step("step_02a_guide_compile"); print(f"Step loaded: {s.name}")'

# 3. Проверить Knowledge Bank
& .\.venv\Scripts\python.exe -c 'from validators.standards_loader import load_organizational_context; ctx=load_organizational_context(); print("Files:", len(ctx))'

# 4. Проверить USER TEMPLATE
& .\.venv\Scripts\python.exe -c 'from validators.standards_loader import load_md_standards; std=load_md_standards(); print("USER TEMPLATE loaded:", "user_template.md" in std)'

# 5. Проверить полный пайплайн
& .\.venv\Scripts\python.exe scripts/run.py Reading
```

## D7. Критерии готовности

- [ ] `step_00a_llm_preflight` загружается без ошибок
- [ ] `step_02a_guide_compile` реализован и загружается без ошибок
- [ ] Оба шага добавлены в `WORKFLOW_STEPS` в правильном порядке
- [ ] Knowledge Bank загружается (7 файлов: 3 базовых + 4 из ajtbd/)
- [ ] Функция `standard_fingerprint()` добавлена в `standards_loader.py`
- [ ] Метаданные стандартов добавляются в артефакты ключевых шагов
- [ ] Human-readable отчеты создаются для step_03, step_04, step_05, step_06
- [ ] USER TEMPLATE загружается как стандарт
- [ ] step_04_jtbd содержит обязательные поля (level, level_rationale, evidence_refs)
- [ ] step_04_jtbd работает без корпуса интервью (fallback-логика)
- [ ] Полный пайплайн запускается без ошибок

## D8. Файлы для изменения

1. **Создать**: `workflow/steps/step_02a_guide_compile.py`
2. **Изменить**: `config.py` (добавить в WORKFLOW_STEPS)
3. **Изменить**: `validators/standards_loader.py` (добавить standard_fingerprint)
4. **Изменить**: `workflow/steps/step_03_interview_collect.py` (использовать скомпилированный гайд + human-readable)
5. **Изменить**: `workflow/steps/step_04_jtbd.py` (обязательные поля + fallback + human-readable)
6. **Изменить**: `workflow/steps/step_05_segments.py` (human-readable)
7. **Изменить**: `workflow/steps/step_06_decision_mapping.py` (human-readable)
8. **Проверить**: `prompts/standards/user_template.md` (уже существует)

---

**Приоритет**: Высокий
**Время**: 4-6 часов
**Зависимости**: Knowledge Bank уже реализован, USER TEMPLATE уже существует
