# Segmentation Standard (JTBD-led)

## 1) Purpose & Scope
Цель — определить 3–5 ключевых сегментов на основе их JTBD, страхов/желаний и поведения. Сегментация должна быть **действенной** (actionable) и позволять приоритизировать маркетинговые усилия.

## 2) Process
1) **Анализ JTBD:** сгруппируй пользователей по схожим Big JTBD (используй jobs[].criteria/trigger/emotions/importance/frequency/evidence).
2) **Страхи и желания:** для каждой группы определи **Primary Fear** и **Desire**.
3) **Формирование сегментов:** опиши: характеристики, болевые точки, лексика, связанные JTBD/работы.
4) **Приоритизация:** оцени **LTV proxy / Value / Size / Accessibility**; поставь **priority 1–5** и объясни почему.
5) **Каналы и барьеры:** предполагаемые каналы, барьеры, **fear_amplifiers_on_lp** (фразы/блоки текущих LP, усиливающие страх).
6) **Связь с JTBD:** добавь `jtbd_links` (id работ), на основании которых построен сегмент.

## 3) Quality Checklist
- [ ] 3–5 чётких сегментов (не >7).
- [ ] У каждого: `name`, `priority(1–5)`, `primary_fear`, `desire`.
- [ ] Основаны на поведении/психографике, не только демографии.
- [ ] Приоритизация обоснована (`value_note/size_note/accessibility_note`).
- [ ] Для каждого: ≥1 `trigger`, ≥1 `channel`, ≥1 `evidence` quote.
- [ ] Для каждого: `jtbd_links` присутствуют и валидны.
- [ ] Указаны `fear_amplifiers_on_lp`, если есть текст LP.

## 4) Red Flags
- **Сегмент = демография только:** “мужчины 25–35”. Нужны поведенческие/эмоциональные признаки.
- **>7 сегментов:** потеря фокуса.
- **Слишком общие страхи/желания:** “боится неудачи”, “хочет больше денег”.
- **Нет связи с JTBD:** отсутствуют `jtbd_links`.

## 5) Examples & Anti-examples
- **Хороший:** “Проф. реселлеры (Priority 5/5): Primary Fear — потеря конкурентного преимущества; Desire — масштаб без роста времени. Каналы: affiliate/paid search; jtbd_links: ['job_1','job_3']”
- **Плохой:** “Пользователи из Европы”.

## 6) JSON Contract Hints
Ключи `contracts/step_05_segments.schema.json`: 
`segments[].{ id, name, priority, primary_fear, desire, jtbd_links[], triggers[], pains[], gains[], vocabulary[], primary_jobs[], channels[], barriers[], fear_amplifiers_on_lp[], size_note, value_note, accessibility_note, wtp_note, evidence[] }`.
