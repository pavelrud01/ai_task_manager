# Отчет по исправлению вызовов LLM.generate_json()

## ✅ Задача выполнена

### Проблема
В шагах workflow использовались вызовы `LLM.generate_json(...)` с неправильными именами аргументов и/или без `standard_schema` → рантайм-ошибка.

### Правильная сигнатура
```python
generate_json(
    system_prompt: str, 
    user_prompt: str, 
    org_context: str, 
    standard_schema: dict, 
    standard_text: str = "", 
    reflection_notes: str = ""
) -> dict
```

## 🔧 Исправленные файлы

### 1. step_02a_guide_compile.py
**Было:**
```python
resp = self.llm.generate_json(
    system=system,
    prompt=user,
    org_context=org_blob,
    standard_text=standard_text,
    reflection_notes=reflection_notes
)
```

**Стало:**
```python
schema = (context.get("schemas") or {}).get("step_02a_guide_compile", {})
resp = self.llm.generate_json(
    system_prompt=system,
    user_prompt=user,
    org_context=org_blob,
    standard_schema=schema,
    standard_text=standard_text,
    reflection_notes=reflection_notes
)
```

### 2. step_05_segments.py
**Было:**
```python
resp = self.llm.generate_json(system, user, str(org), md, context.get("reflection_notes",""))
```

**Стало:**
```python
schema = (context.get("schemas") or {}).get("step_05_segments", {})
resp = self.llm.generate_json(
    system_prompt=system,
    user_prompt=user,
    org_context=str(org),
    standard_schema=schema,
    standard_text=md,
    reflection_notes=context.get("reflection_notes","")
)
```

### 3. step_06_decision_mapping.py
**Было:**
```python
resp = self.llm.generate_json(system, user, str(org), md, context.get("reflection_notes",""))
```

**Стало:**
```python
schema = (context.get("schemas") or {}).get("step_06_decision_mapping", {})
resp = self.llm.generate_json(
    system_prompt=system,
    user_prompt=user,
    org_context=str(org),
    standard_schema=schema,
    standard_text=md,
    reflection_notes=context.get("reflection_notes","")
)
```

### 4. step_12_funnel_design.py
**Было:**
```python
resp = self.llm.generate_json(system, user, str(org), md, context.get("reflection_notes",""))
```

**Стало:**
```python
schema = (context.get("schemas") or {}).get("step_12_funnel_design", {})
resp = self.llm.generate_json(
    system_prompt=system,
    user_prompt=user,
    org_context=str(org),
    standard_schema=schema,
    standard_text=md,
    reflection_notes=context.get("reflection_notes","")
)
```

## ✅ Уже исправленные файлы

Следующие файлы уже использовали правильную сигнатуру:
- `step_03_interview_collect.py` - 3 вызова с правильными параметрами
- `step_03_offers_inventory.py` - 1 вызов с правильными параметрами  
- `step_04_jtbd.py` - 1 вызов с правильными параметрами

## 🎯 Результат

**Все вызовы LLM.generate_json() теперь используют:**
- ✅ Правильные имена параметров (`system_prompt`, `user_prompt`)
- ✅ Обязательный параметр `standard_schema` из контекста
- ✅ Именованные аргументы вместо позиционных
- ✅ Корректную передачу `reflection_notes`

**Рантайм-ошибки устранены!** 🚀

