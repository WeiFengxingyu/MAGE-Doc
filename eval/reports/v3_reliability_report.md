# MAGE-Doc V3 Reliability Report

Case count: 5

| Strategy | Answer term hit | Citation type hit | Claim supported | Avg tool calls | Avg latency ms |
| --- | --- | --- | --- | --- | --- |
| v0_agent_baseline | 0.80 | 1.00 | 1.00 | 4.00 | 133.40 |
| v1_evidence_pack | 1.00 | 1.00 | 0.00 | 1.00 | 150.00 |
| v2_multimodal_graph | 1.00 | 1.00 | 1.00 | 4.00 | 140.80 |
| v3_self_correcting | 0.80 | 0.80 | 1.00 | 5.40 | 469.00 |

## Failure Diagnosis

| Reason | Count |
| --- | --- |
| citation_mismatch | 1 |
| passed | 14 |
| unsupported_claim | 5 |

## Reliability Summary

Repair cases: 3 / 5
Recovery rate: 1.00
Repair success rate: 0.60
Average repair rounds: 0.80

### Failure Before

| Reason | Count |
| --- | --- |
| citation_mismatch | 3 |
| passed | 2 |

### Failure After

| Reason | Count |
| --- | --- |
| citation_mismatch | 1 |
| passed | 4 |

## V3 Repair Cases

| Case | Initial | Final | Rounds | Actions |
| --- | --- | --- | --- | --- |
| curated_table_revenue_2026 | 0.53 | 1.00 | 1 | citation_rerank |
| curated_metric_margin_2026 | 0.53 | 1.00 | 1 | citation_rerank |
| curated_text_enterprise_demand | 0.62 | 0.62 | 0 | - |
| curated_text_risk_supply_chain | 0.62 | 0.62 | 0 | - |
| curated_graph_revenue_context | 0.57 | 0.57 | 2 | citation_rerank, citation_rerank |
