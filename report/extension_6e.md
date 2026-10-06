### Điểm từng lần chạy (passed/total)

| Điều kiện | Tác vụ | rep1 | rep2 | rep3 | TB ± độ lệch chuẩn [min–max] |
|---|---|---|---|---|---|
| baseline | code-eval | 7/11 | 7/11 | 7/11 | 0.64 ± 0.00 [0.64–0.64] |
| baseline | data-eval | 5/9 | 5/9 | 5/9 | 0.56 ± 0.00 [0.56–0.56] |
| baseline | logs-eval | 6/10 | 6/10 | 6/10 | 0.60 ± 0.00 [0.60–0.60] |
| subagents | code-eval | 7/11 | 7/11 | 7/11 | 0.64 ± 0.00 [0.64–0.64] |
| subagents | data-eval | 5/9 | 5/9 | 5/9 | 0.56 ± 0.00 [0.56–0.56] |
| subagents | logs-eval | 6/10 | 6/10 | 6/10 | 0.60 ± 0.00 [0.60–0.60] |
| skills-auto | code-eval | 10/11 | 10/11 | 10/11 | 0.91 ± 0.00 [0.91–0.91] |
| skills-auto | data-eval | 5/9 | 5/9 | 5/9 | 0.56 ± 0.00 [0.56–0.56] |
| skills-auto | logs-eval | 9/10 | 9/10 | 9/10 | 0.90 ± 0.00 [0.90–0.90] |

### Tổng hợp theo điều kiện (mỗi lần lặp = trung bình 3 tác vụ đánh giá)

| Điều kiện | Điểm TB mỗi lần lặp | Điểm TB ± SD [min–max] | Check `rule_` đạt mỗi lần lặp | Check kỹ thuật đạt mỗi lần lặp | Token TB/lần chạy ± SD [min–max] | Lần chạy đọc skill |
|---|---|---|---|---|---|---|
| baseline | 0.60, 0.60, 0.60 | 0.60 ± 0.00 [0.60–0.60] | 0/12, 0/12, 0/12 | 18/18, 18/18, 18/18 | 41,935 ± 19,373 [18,220–75,768] | 0/9 |
| subagents | 0.60, 0.60, 0.60 | 0.60 ± 0.00 [0.60–0.60] | 0/12, 0/12, 0/12 | 18/18, 18/18, 18/18 | 167,937 ± 90,593 [85,454–357,668] | 0/9 |
| skills-auto | 0.79, 0.79, 0.79 | 0.79 ± 0.00 [0.79–0.79] | 6/12, 6/12, 6/12 | 18/18, 18/18, 18/18 | 58,748 ± 31,855 [25,194–104,727] | 9/9 |

### Check thất bại theo số lần (trên tổng số lần lặp)

| Điều kiện | Tác vụ | Check thất bại (số lần) |
|---|---|---|
| baseline | code-eval | `rule_changelog` (3), `rule_regression_tests` (3), `rule_type_hints` (3), `rule_version_bump` (3) |
| baseline | data-eval | `rule_clean_csv` (3), `rule_meta_block` (3), `rule_money_in_cents` (3), `rule_sorted_keys_format` (3) |
| baseline | logs-eval | `rule_schema_header` (3), `rule_service_names` (3), `rule_sorted_errors` (3), `rule_source_line` (3) |
| subagents | code-eval | `rule_changelog` (3), `rule_regression_tests` (3), `rule_type_hints` (3), `rule_version_bump` (3) |
| subagents | data-eval | `rule_clean_csv` (3), `rule_meta_block` (3), `rule_money_in_cents` (3), `rule_sorted_keys_format` (3) |
| subagents | logs-eval | `rule_schema_header` (3), `rule_service_names` (3), `rule_sorted_errors` (3), `rule_source_line` (3) |
| skills-auto | code-eval | `rule_version_bump` (3) |
| skills-auto | data-eval | `rule_clean_csv` (3), `rule_meta_block` (3), `rule_money_in_cents` (3), `rule_sorted_keys_format` (3) |
| skills-auto | logs-eval | `rule_source_line` (3) |

Lần chạy có `error`: không có.
