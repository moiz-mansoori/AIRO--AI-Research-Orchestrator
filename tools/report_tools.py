"""
AIRO — tools/report_tools.py
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from jinja2 import Environment, BaseLoader
from loguru import logger
from orchestrator.state import AIROState, CriticVerdict

# Markdown template 
REPORT_TEMPLATE = """
# AIRO Experiment Report
**Experiment ID:** {{ state.experiment_id }}
**Generated:** {{ generated_at }}
**Task:** {{ state.task_type | upper }}  ·  **Dataset:** {{ state.dataset_path | replace('\\', '/') | split('/') | last }}

---

## 1. Executive Summary
{{ executive_summary }}

---

## 2. Dataset Overview

| Property | Value |
|---|---|
| Rows | {{ state.quality_report.row_count }} |
| Features | {{ state.quality_report.feature_count }} |
| Duplicate rows removed | {{ state.quality_report.duplicate_rows }} |
| Train / Val / Test | {{ state.split_sizes.get('train', 0) }} / {{ state.split_sizes.get('val', 0) }} / {{ state.split_sizes.get('test', 0) }} |
{% if state.quality_report.imbalance_ratio %}| Class imbalance ratio | {{ state.quality_report.imbalance_ratio }} |{% endif %}

{% if state.quality_report.warnings %}
**Warnings:**
{% for w in state.quality_report.warnings %}
- {{ w }}
{% endfor %}
{% endif %}

---

## 3. Experiment Setup

- **Configs tested:** {{ state.configs | length }}
- **Model families:** {{ model_families | join(', ') }}
- **Primary metric:** {{ state.primary_metric_name() }}
- **Parallel workers:** {{ parallel_workers }}

---

## 4. Results Leaderboard

| Rank | Model | {{ metric_name | upper }} | Verdict |
|---|---|---|---|
{% for entry in state.leaderboard %}
| {{ entry.rank }} | {{ entry.model_type }} | {{ "%.4f" | format(entry.primary_metric) }} | {{ entry.verdict }} |
{% endfor %}

---

## 5. Best Model Analysis

**Selected model:** {{ state.best_model_type }}
**Run ID:** {{ state.best_run_id }}
**Improvement over baseline:** {{ "%.1f" | format(state.improvement_over_baseline_pct) }}%

**Why this model was selected:**
{{ state.selection_reasoning }}

{% if top_features %}
**Top-10 SHAP Features:**

| Rank | Feature | Importance |
|---|---|---|
{% for i, f in enumerate(top_features) %}
| {{ i+1 }} | {{ f.feature }} | {{ "%.4f" | format(f.importance) }} |
{% endfor %}
{% endif %}

---

## 6. Critic Audit Summary

| Rank | Model | Verdict | Issues | Recommendation |
|---|---|---|---|---|
{% for entry in state.leaderboard %}
{% set critic = state.critic_results | selectattr('run_id', 'eq', entry.run_id) | first %}
| {{ entry.rank }} | {{ entry.model_type }} | {{ critic.verdict if critic else 'N/A' }} | {{ critic.issues | join('; ') if critic and critic.issues else 'None' }} | {{ critic.recommendations[0] if critic and critic.recommendations else '—' }} |
{% endfor %}

---

## 7. What to Try Next

{% for rec in recommendations %}
{{ loop.index }}. {{ rec }}
{% endfor %}

---

## 8. Reproducibility

| Item | Value |
|---|---|
| MLflow experiment | {{ mlflow_uri }} |
| DVC artifact hash | {{ dvc_hash }} |
| Random seeds | {{ seeds | join(', ') }} |
| AIRO version | 0.1.0 |
| Generated | {{ generated_at }} |
"""

# Render
def render_markdown(
    state: AIROState,
    executive_summary: str,
    top_features: list[dict],
    recommendations: list[str],
    dvc_hash: str = "N/A",
) -> str:
    """Render the full experiment report as a Markdown string."""
    import os

    env = Environment(loader=BaseLoader())
    env.globals["enumerate"] = enumerate

    template = env.from_string(REPORT_TEMPLATE)

    model_families = list({c.model_type for c in state.configs})
    seeds = list({c.random_seed for c in state.configs})
    metric_name = state.primary_metric_name()

    return template.render(
        state=state,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        executive_summary=executive_summary,
        top_features=top_features,
        recommendations=recommendations,
        model_families=model_families,
        seeds=seeds,
        metric_name=metric_name,
        parallel_workers=os.getenv("AIRO_PARALLEL_WORKERS", "4"),
        mlflow_uri=os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"),
        dvc_hash=dvc_hash,
    )


def save_markdown(content: str, path: str) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding="utf-8")
    logger.info(f"Markdown report saved: {path}")
    return path


def render_pdf(md_path: str, pdf_path: str) -> str:
    """Convert Markdown → HTML → PDF via WeasyPrint."""
    try:
        import markdown as md_lib
        from weasyprint import HTML, CSS

        md_content = Path(md_path).read_text(encoding="utf-8")
        html_body  = md_lib.markdown(md_content, extensions=["tables", "fenced_code"])

        html_full = f"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; font-size: 13px; line-height: 1.6;
          max-width: 900px; margin: 40px auto; color: #1f2937; }}
  h1   {{ color: #1e1b4b; border-bottom: 3px solid #4f46e5; padding-bottom: 6px; }}
  h2   {{ color: #1e1b4b; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; }}
  h3   {{ color: #0f766e; }}
  table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
  th   {{ background: #1e1b4b; color: white; padding: 8px 12px; text-align: left; }}
  td   {{ border: 1px solid #e5e7eb; padding: 7px 12px; }}
  tr:nth-child(even) td {{ background: #f9fafb; }}
  code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 4px; font-size: 12px; }}
  pre  {{ background: #1e1b4b; color: #e0e7ff; padding: 16px; border-radius: 6px; overflow-x: auto; }}
  .page-header {{ color: #6b7280; font-size: 11px; margin-bottom: 32px; }}
</style></head>
<body>
<div class="page-header">AIRO — AI Research Orchestrator · Experiment Report</div>
{html_body}
</body></html>"""

        Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)
        HTML(string=html_full).write_pdf(
            pdf_path,
            stylesheets=[CSS(string="@page { margin: 2cm; }")]
        )
        logger.info(f"PDF report saved: {pdf_path}")

    except (ImportError, OSError) as e:
        logger.warning(f"PDF generation failed/skipped — missing system dependency: {e}")
        logger.info("Falling back to Markdown report only.")

    return pdf_path


def save_leaderboard_csv(state: AIROState, path: str) -> str:
    import csv
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["rank", "run_id", "model_type", "primary_metric", "verdict"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in state.leaderboard:
            writer.writerow({
                "rank":           entry.rank,
                "run_id":         entry.run_id,
                "model_type":     entry.model_type,
                "primary_metric": entry.primary_metric,
                "verdict":        entry.verdict,
            })
    logger.info(f"Leaderboard CSV saved: {path}")
    return path
