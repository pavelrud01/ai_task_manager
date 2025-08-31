# Decision Mapping Standard (B2C Journey)

## Stages
problem → solution_possible → personal_relevance → feasibility → social_validation → risk_eval → urgency → action

## For each segment × stage
- content_existing[] / content_needed[]
- proof[] (соц.доказательства, данные)
- risk_reducers[] (гарантия, trial, FAQ)
- cta (следующее действие)
- metric (как измеряем)

## Deliverable (JSON)
`maps[].{ segment_id, stages[], gaps[] }`

## DoD
- Все стадии присутствуют
- На “слабых” стадиях есть content_needed/proof
- У каждой стадии есть CTA и metric
