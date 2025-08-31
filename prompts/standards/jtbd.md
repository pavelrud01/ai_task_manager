# AJTBD Standard (Core v1.1)

type: standard
updated: 31 Aug 2025, Europe/Berlin
version: 1.1
status: Active
owner: Marketing Research / JTBD
applies_to: Workflows [A: no data (simulate interviews), B: semi-structured notes, C: rich VOC/CRM]
based_on: [AJTBD Interview Guide]
dependencies: []
contracts: [step_04_jtbd.schema.json]
tags: [ajtbd, research, tdd, reflection]

---

## 0) Purpose & Scope
Цель — извлечь и структурировать **рабочие задачи пользователей (Jobs-to-be-Done)** по трёхуровневой схеме **Big → Medium → Small**, промаркировать их по **Functional / Emotional / Social**, привязать к источникам и выдать один артефакт `step_04_jtbd.json` по контракту.

> Этот стандарт **не** включает сегментацию/decision-journey/лендинг. Они выполняются отдельными стандартами.

---

## STEP-0 — Compliance & Understanding (обязательно)
1. Прочитай стандарт полностью.  
2. Сформируй **Compliance-чеклист** (обязательные поля контракта и проверки качества).  
3. Сделай **Understanding-рефлексию**: что делаем/не делаем; какие входы обязательны.  
4. Если **uncertainty > 0.3** — задай уточняющие вопросы и приостанови выполнение до ответа.

**Acceptance:** краткий конспект понимания + перечень входов/выходов.

---

## Process

### 1) Inputs — входные данные
**Обязательные:**
- **personas**: список целевых ролей/аудиторий (можно черновой).
- **data_availability**: режим `A|B|C`  
  A — данных нет → симулируем интервью;  
  B — есть заметки/цитаты;  
  C — богатый VOC/CRM массив (обзоры, тикеты, чаты).
- **analysis_mode**: `frequency` и/или `impact`.

**Опциональные:**
- **n_interviews** (для A), **files/links** (для B/C), **locales**, **constraints**.

**Acceptance:** входы зафиксированы в `_inputs.json` артефакта запуска.

---

### 2) Preprocessing — подготовка корпуса
- Очистить тексты (язык/мусор/шум), нормализовать.  
- Дедуплицировать повторяющиеся формулировки.  
- Привязать цитаты к источнику/персоне/каналу.  
- Составить мини-словарь доменной лексики.

**Выход:** `preprocessed_corpus.json` со строками вида:
```json
{"source":"interview|crm|review","persona":"...","quote":"...","normalized_text":"...","tags":["..."]}
```

---

### 3) Core — построение графа работ

#### 3.1 Big JTBD (3–7 шт.)

**Формат:**
«Когда я **[контекст]**, я хочу **[действие/мотивация]**, чтобы **[результат/ценность]**»

**Для каждого Big:**
- Применить **5 Whys** → добраться до корневой причины/ценности.
- Проставить тип: `functional`, `emotional`, `social` (одно или несколько).
- **Evidence**: ссылки на цитаты/файлы/источники.
- **Coverage_pct**: какой процент корпуса покрыт Big-узлами в сумме.

#### 3.2 Medium JTBD

Для каждого Big — **2–6 Medium** шагов (этапы/препятствия/критерии успеха):
- Краткая формулировка «что нужно сделать/понять/достичь».
- Тип: F/E/S.
- Evidence.

#### 3.3 Small JTBD

Для каждого Big — **3–10 Small** задач (микро-шаги, проверки, вводы):
- Короткое действие/проверка/микро-цель.
- Тип: F/E/S.
- Evidence.

#### 3.4 Anti-JTBD фильтр

- Отсеять формулировки-«фичи»/решения («купить Х», «использовать Y»).
- JTBD описывает задачу/прогресс, а не продукт/функцию.

---

## JSON Contract Hints

Ключевые поля артефакта `step_04_jtbd.json` (см. `contracts/step_04_jtbd.schema.json`):

- **big_jtbd[]**: список Big-узлов.
  - **id**: string
  - **statement**: string (шаблон «Когда я…, я хочу…, чтобы…»)
  - **type**: array<functional|emotional|social> (≥1)
  - **whys**: string[≥3]
  - **medium[]**: объекты {id, statement, type, evidence[]}
  - **small[]**: объекты {id, statement, type, evidence[]}
  - **evidence[]**: string[] (цитаты/файлы/URL)
- **coverage_pct**: number [0..1]

---

## 4) Output — контракт артефакта

**Место:** `artifacts/<run>/step_04_jtbd.json`  
**Схема:** `contracts/step_04_jtbd.schema.json`

**Пример структуры** (должен валидироваться схемой):

```json
{
  "big_jtbd": [
    {
      "id": "B1",
      "statement": "Когда я …, я хочу …, чтобы …",
      "type": ["functional","emotional","social"],
      "whys": ["почему1","почему2","почему3","почему4","почему5"],
      "medium": [
        {"id":"M1","statement":"…","type":"functional","evidence":["..."]},
        {"id":"M2","statement":"…","type":"emotional","evidence":["..."]}
      ],
      "small": [
        {"id":"S1","statement":"…","type":"functional","evidence":["..."]}
      ],
      "evidence": ["цитата/URL/источник"]
    }
  ],
  "coverage_pct": 0.0
}
```

---

## 5) Quality Checklist (TDD)

- [ ] **3–7 Big JTBD**, не «фичи» и не лозунги.
- [ ] Для каждого Big применены **5 Whys**.
- [ ] Есть **Medium** и **Small** уровни; иерархия логична.
- [ ] Проставлены типы **F/E/S** для всех узлов.
- [ ] Присутствует **evidence** у ключевых узлов.
- [ ] Указан **coverage_pct**.
- [ ] Артефакт валиден по **JSON-схеме**.

---

## 6) Red Flags

- **JTBD = фича/решение** («Хочу использовать AI-аналитику»).
- **>7 Big JTBD** или, наоборот, 1–2 размытых.
- **Нет уровня Medium/Small** (плоский список).
- **Только функциональные** мотивы (игнор эмоций/социального).
- **Нет привязки к источникам**.
- **Слишком общие** формулировки («хочу быть успешным»).

---

## 7) Scoring & Reflection

- **Итоговый балл шага:** min(self_score, schema_score, checklist_score).
- **Порог прохождения:** ≥ QUALITY_THRESHOLD.
- **При фейле** — reflection-loop до MAX_REFLECTION_LOOPS с учётом self-critique.
- **Uncertainty Gate:** если uncertainty > 0.3, остановиться и запросить данные/уточнения.

---

## 8) Examples

**✅ Хорошо (B2B):**
«Когда я масштабирую команду, я хочу быстро вводить новичков в контекст, чтобы они становились продуктивными за 1–2 недели».
- Тип: Functional + Emotional; понятная ценность.

**❌ Плохо:**
«Хочу использовать вашу CRM». 
- Это решение/фича, а не работа пользователя.

---

## 9) Changelog

**v1.1 (2025-08-31):** Приведён к структуре «Мастер-промта»: добавлены заголовок **Process** и секция **JSON Contract Hints**.

**v1.0 (2025-08-30):** Чистый AJTBD-стандарт: только извлечение и структура работ (Big/Medium/Small, F/E/S, 5 Whys, evidence, coverage). Сегментация/карта решений вынесены в отдельные стандарты.

---

### (Опционально) Проверь наличие контракта
Файл `contracts/step_04_jtbd.schema.json` должен существовать. Если его нет, создай и вставь минимальную схему. Если нужно — запроси схему отдельно.