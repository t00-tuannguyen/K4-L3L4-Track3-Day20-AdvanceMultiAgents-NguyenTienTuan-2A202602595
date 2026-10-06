"""Phần 6e - Lặp để đo nhiễu: tổng hợp nhiều lần chạy của mỗi điều kiện trên tác vụ đánh giá.

Lần 1 = kết quả chính thức trong results/; lần 2, 3 = results_6e/rep2, results_6e/rep3
(tạo bằng `python -m lab.runner --condition <c> --tasks eval --results results_6e/<rep>`).

Chạy: python extension/aggregate_6e.py > report/extension_6e.md
"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPS = {"rep1": ROOT / "results", "rep2": ROOT / "results_6e" / "rep2", "rep3": ROOT / "results_6e" / "rep3"}
CONDITIONS = ["baseline", "subagents", "skills-auto"]
TASKS = ["code-eval", "data-eval", "logs-eval"]


def load(rep_dir: Path, condition: str, task: str) -> dict | None:
    f = rep_dir / condition / task / "run.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def spread(values: list[float], fmt: str = "{:.2f}") -> str:
    if not values:
        return "-"
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return f"{fmt.format(mean)} ± {fmt.format(sd)} [{fmt.format(min(values))}–{fmt.format(max(values))}]"


def main() -> None:
    runs = {(c, t, rep): load(d, c, t) for c in CONDITIONS for t in TASKS for rep, d in REPS.items()}
    missing = [k for k, v in runs.items() if v is None]
    if missing:
        print(f"WARNING: missing runs: {missing}", file=sys.stderr)
    errors = [(k, v["error"]) for k, v in runs.items() if v and v.get("error")]

    out = ["### Điểm từng lần chạy (passed/total)", "",
           "| Điều kiện | Tác vụ | " + " | ".join(REPS) + " | TB ± độ lệch chuẩn [min–max] |",
           "|---|---|" + "---|" * len(REPS) + "---|"]
    for c in CONDITIONS:
        for t in TASKS:
            rs = [runs[(c, t, rep)] for rep in REPS]
            cells = [f"{r['passed']}/{r['total']}" if r else "-" for r in rs]
            scores = [r["score"] for r in rs if r]
            out.append(f"| {c} | {t} | " + " | ".join(cells) + f" | {spread(scores)} |")

    out += ["", "### Tổng hợp theo điều kiện (mỗi lần lặp = trung bình 3 tác vụ đánh giá)", "",
            "| Điều kiện | Điểm TB mỗi lần lặp | Điểm TB ± SD [min–max] | Check `rule_` đạt mỗi lần lặp | "
            "Check kỹ thuật đạt mỗi lần lặp | Token TB/lần chạy ± SD [min–max] | Lần chạy đọc skill |",
            "|---|---|---|---|---|---|---|"]
    for c in CONDITIONS:
        rep_scores, rules, techs, tokens, read = [], [], [], [], 0
        for rep in REPS:
            rs = [runs[(c, t, rep)] for t in TASKS if runs[(c, t, rep)]]
            if not rs:
                continue
            rep_scores.append(statistics.mean(r["score"] for r in rs))
            checks = [ch for r in rs for ch in r["checks"]]
            rule = [ch for ch in checks if ch["name"].startswith("rule_")]
            tech = [ch for ch in checks if not ch["name"].startswith("rule_")]
            rules.append(f"{sum(ch['passed'] for ch in rule)}/{len(rule)}")
            techs.append(f"{sum(ch['passed'] for ch in tech)}/{len(tech)}")
            tokens += [r["tokens"]["total"] for r in rs]
            read += sum(r["skills_read"] > 0 for r in rs)
        n = sum(1 for rep in REPS for t in TASKS if runs[(c, t, rep)])
        out.append(f"| {c} | " + ", ".join(f"{s:.2f}" for s in rep_scores) + f" | {spread(rep_scores)} | "
                   + ", ".join(rules) + " | " + ", ".join(techs) + f" | {spread(tokens, '{:,.0f}')} | {read}/{n} |")

    out += ["", "### Check thất bại theo số lần (trên tổng số lần lặp)", "",
            "| Điều kiện | Tác vụ | Check thất bại (số lần) |", "|---|---|---|"]
    for c in CONDITIONS:
        for t in TASKS:
            fails: dict[str, int] = {}
            for rep in REPS:
                r = runs[(c, t, rep)]
                for ch in (r["checks"] if r else []):
                    if not ch["passed"]:
                        fails[ch["name"]] = fails.get(ch["name"], 0) + 1
            out.append(f"| {c} | {t} | " + ", ".join(f"`{k}` ({v})" for k, v in sorted(fails.items())) + " |")

    out += ["", f"Lần chạy có `error`: {errors if errors else 'không có'}."]
    print("\n".join(out))


if __name__ == "__main__":
    main()
