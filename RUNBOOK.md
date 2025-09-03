# RUNBOOK: AI Marketing Agent

## Обзор

Этот runbook содержит пошаговые инструкции для запуска AI Marketing Agent с готовыми сценариями. Система позволяет владельцу продукта "принести гайд/вводные → нажать Старт → получить все артефакты".

## Предварительные требования

1. **Python 3.12+** установлен в системе
2. **API ключ LLM** настроен в `config.py` или переменных окружения
3. **Проектная структура** создана (см. раздел "Структура проектов")

## Структура проектов

```
projects/
├── CaseA/          # Сценарий A: simulate
├── CaseB/          # Сценарий B: ingest → follow-ups  
└── CaseC/          # Сценарий C: seed-snippets → full run
```

Каждый проект содержит:
- `input.json` - входные данные
- `guides/` - (опционально) проектные гайды
- `context/` - (опционально) организационный контекст

## Сценарий A: Simulate (Симуляция интервью)

**Назначение**: Быстрый запуск с симуляцией интервью для тестирования workflow.

### Шаги:

1. **Подготовьте гайд**:
   - Положите гайд в `prompts/guides/[v3.3] Гайд AJTBD-интервью для B2C-продуктов.md`
   - Или в `projects/CaseA/guides/` (приоритет над глобальными)

2. **Отредактируйте входные данные**:
   ```bash
   # Откройте и отредактируйте
   projects/CaseA/input.json
   ```
   
   Обязательные поля:
   - `company_name`: название компании
   - `landing_url`: URL сайта продукта
   - `products`: описание продуктов
   - `interview_mode`: "simulate"

3. **Запустите сценарий**:
   ```bash
   # Windows
   scripts\run_caseA.ps1
   
   # Unix/Linux/macOS
   scripts/run_caseA.sh
   ```

4. **Проверьте результаты**:
   - Откройте `artifacts/<run_id>/`
   - Проверьте артефакты по чек-листу (см. раздел "Чек-лист артефактов")

### Ожидаемые артефакты:
- `step_03_interview_collect.json` - симулированные интервью
- `step_04_jtbd.json` - Jobs to be Done
- `step_05_segments.json` - сегменты рынка
- `step_06_decision_mapping.json` - карты решений
- `exports/` - экспортированные документы

---

## Сценарий B: Ingest → Follow-ups (Загрузка данных)

**Назначение**: Загрузка существующих данных интервью с последующими follow-up интервью.

### Шаги:

1. **Подготовьте данные**:
   - Положите существующие интервью в `projects/CaseB/data/`
   - Форматы: `.jsonl`, `.csv`, `.json`
   - Подготовьте гайд (см. Сценарий A, шаг 1)

2. **Настройте входные данные**:
   ```bash
   # Откройте и отредактируйте
   projects/CaseB/input.json
   ```
   
   Обязательные поля:
   - `company_name`, `landing_url`, `products`
   - `interview_mode`: "ingest"
   - `data_sources`: пути к файлам данных

3. **Запустите сценарий**:
   ```bash
   # Windows
   scripts\run_caseB.ps1
   
   # Unix/Linux/macOS
   scripts/run_caseB.sh
   ```

4. **Проверьте результаты**:
   - Проверьте загруженные данные в `artifacts/<run_id>/interviews/`
   - Убедитесь в качестве follow-up интервью
   - Проверьте финальные артефакты

### Ожидаемые артефакты:
- `interviews/ingest.jsonl` - загруженные данные
- `interviews/after_ingest.jsonl` - follow-up интервью
- Все артефакты из Сценария A

---

## Сценарий C: Seed-snippets → Full Run (Полный запуск)

**Назначение**: Запуск с начальными гипотезами и полным циклом анализа.

### Шаги:

1. **Подготовьте seed-данные**:
   - Создайте `projects/CaseC/data/jtbd_seeds.json` с начальными гипотезами
   - Подготовьте гайд и контекстные файлы
   - Добавьте любые дополнительные данные

2. **Настройте входные данные**:
   ```bash
   # Откройте и отредактируйте
   projects/CaseC/input.json
   ```
   
   Обязательные поля:
   - `company_name`, `landing_url`, `products`
   - `interview_mode`: "both" (simulate + ingest)
   - `seed_data`: пути к seed-файлам

3. **Запустите сценарий**:
   ```bash
   # Windows
   scripts\run_caseC.ps1
   
   # Unix/Linux/macOS
   scripts/run_caseC.sh
   ```

4. **Проверьте результаты**:
   - Проверьте все этапы workflow
   - Убедитесь в качестве финальных артефактов
   - Проверьте экспортированные документы

### Ожидаемые артефакты:
- Все артефакты из Сценариев A и B
- `exports/jobs_longform/` - детальные описания работ
- `exports/personas.md` - персоны для сегментов
- `step_05b_segments_merged.json` - объединенные сегменты

---

## Чек-лист артефактов

### Обязательные артефакты (все сценарии):
- [ ] `step_00_compliance_check.json` - проверка входных данных
- [ ] `step_02_extract.json` - извлечение контекста
- [ ] `step_03_interview_collect.json` - сбор интервью
- [ ] `step_04_jtbd.json` - Jobs to be Done
- [ ] `step_05_segments.json` - сегменты рынка
- [ ] `step_06_decision_mapping.json` - карты решений

### Дополнительные артефакты (Сценарий C):
- [ ] `step_04b_segments_merged.json` - объединенные сегменты
- [ ] `exports/jobs_longform/*.md` - детальные описания работ
- [ ] `exports/personas.md` - персоны
- [ ] `exports/` - другие экспортированные документы

### Критерии качества:
- [ ] Все JSON файлы валидны
- [ ] Evidence references присутствуют в ключевых артефактах
- [ ] Сегменты содержат минимум 3 Core Jobs
- [ ] Decision mapping содержит CTAs и метрики
- [ ] Экспортированные документы читаемы и структурированы

---

## Альтернативный запуск

### Единый CLI-хелпер:
```bash
# Запуск любого сценария
python scripts/run.py --case A
python scripts/run.py --case B  
python scripts/run.py --case C

# С дополнительными параметрами
python scripts/run.py --case A --project-dir projects/CustomCase
python scripts/run.py --case B --input custom_input.json
```

### Прямой запуск main.py:
```bash
# Сценарий A
python main.py --input projects/CaseA/input.json --project-dir projects/CaseA

# Сценарий B
python main.py --input projects/CaseB/input.json --project-dir projects/CaseB

# Сценарий C
python main.py --input projects/CaseC/input.json --project-dir projects/CaseC
```

---

## FAQ

### Q: Как изменить API ключ LLM?
A: Отредактируйте `config.py` или установите переменную окружения `OPENAI_API_KEY`.

### Q: Где найти результаты запуска?
A: После запуска система выведет:
```
RUN ID: run_20240115_143022_abc123
ARTIFACTS: artifacts/run_20240115_143022_abc123
```

### Q: Как добавить собственный гайд?
A: Положите файл в `projects/<Case>/guides/` - он будет иметь приоритет над глобальными гайдами.

### Q: Что делать, если шаг завершился с ошибкой?
A: Проверьте логи в консоли, убедитесь в корректности входных данных и наличии всех зависимостей.

### Q: Как изменить последовательность шагов?
A: Отредактируйте `config.py`, секция `WORKFLOW_STEPS`.

### Q: Можно ли запустить только определенные шаги?
A: Да, используйте параметр `--steps` в main.py:
```bash
python main.py --input input.json --steps step_03,step_04
```

---

## Поддержка

При возникновении проблем:
1. Проверьте этот runbook
2. Убедитесь в корректности входных данных
3. Проверьте логи выполнения
4. Обратитесь к документации в `prompts/guides/` и `prompts/standards/`

---

*Последнее обновление: 2024-01-15*


