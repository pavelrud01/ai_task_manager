# Funnel Design Standard (AAARRR / AIDA)

## Inputs
Segments + Decision Map + Company/Market context

## For each Segment × Channel (paid|seo|email|affiliate|smm|ugc|crm)
stages[]:
- name (Awareness/Interest/Consideration/Conversion/Retention/Referral)
- message (job-centric)
- asset (ad, LP, email, content, UGC, …)
- offer / lead_magnet (если применимо)
- risk_reducer
- next_action
- kpi { ctr?, lead_rate?, cvr?, ltv_proxy? }

experiments[]:
- H, metric, target_delta, success, priority(H/M/L)

assets_required[]:
- LPs, flows, creatives

## DoD
- ≥1 канал на топ-сегмент
- ≥1 эксперимент/канал
- На Conversion есть offer или risk_reducer
