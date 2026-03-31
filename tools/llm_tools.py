"""
AIRO — tools/llm_tools.py
Groq API wrapper for agent reasoning calls.
"""
from __future__ import annotations

import os
from pathlib import Path

import groq
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

_client: groq.Groq | None = None

def get_client() -> groq.Groq:
    global _client
    if _client is None:
        _client = groq.Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client

def load_prompt(name: str) -> str:
    """Load a prompt template from prompts/{name}.txt"""
    path = Path("prompts") / f"{name}.txt"
    return path.read_text(encoding="utf-8")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_llm(
    user_message: str,
    system_message: str | None = None,
    model: str | None = None,
    max_tokens: int = 1000,
    expect_json: bool = False,
) -> str:
    """
    Single Groq API call. Retries up to 3× on transient errors.

    Args:
        user_message:   The user turn content.
        system_message: Optional system prompt override.
        model:          Defaults to AIRO_MODEL env var.
        max_tokens:     Max response tokens.
        expect_json:    If True, strips markdown fences from response.

    Returns raw text response.
    """
    if system_message is None:
        system_message = load_prompt("system_prompt")

    model = model or os.getenv("AIRO_MODEL", "llama-3.3-70b-versatile")

    logger.debug(f"LLM call → {model} (max_tokens={max_tokens})")

    response = get_client().chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
    )

    text = response.choices[0].message.content

    if expect_json:
        text = _strip_json_fences(text)

    return text


def call_llm_for_configs(
    feature_schema: dict[str, str],
    task_type: str,
    n_configs: int,
) -> str:
    """Specialised call to generate experiment configs as JSON."""
    prompt = f"""
You are generating {n_configs} ML experiment configurations.

Dataset feature schema (column → dtype):
{feature_schema}

Task type: {task_type}
Number of configs to generate: {n_configs}

Generate a JSON array of {n_configs} experiment configs.
Config #0 MUST be a naive baseline (default sklearn params).
Use at least 3 different model families.

Each config must have these exact keys:
  config_id, model_type, hyperparams (dict), feature_subset ("all" or list), random_seed (int), notes (str)

Allowed model_type values:
  LogisticRegression, RandomForestClassifier, RandomForestRegressor,
  XGBClassifier, XGBRegressor, MLPClassifier, MLPRegressor

Respond with ONLY the JSON array. No prose, no markdown fences.
"""
    return call_llm(prompt, max_tokens=2000, expect_json=True)


def call_llm_for_selection_reasoning(
    best_model: str,
    metric_name: str,
    metric_value: float,
    improvement_pct: float,
    leaderboard_summary: str,
) -> str:
    """Generate 3-sentence reasoning for best model selection."""
    prompt = f"""
Write exactly 3 sentences explaining why {best_model} was selected as the best model.

Context:
- Primary metric: {metric_name} = {metric_value:.4f}
- Improvement over baseline: {improvement_pct:+.1f}%
- Leaderboard summary:
{leaderboard_summary}

Be specific and data-driven. No fluff.
"""
    return call_llm(prompt, max_tokens=200)


def call_llm_for_report_narrative(
    section: str,
    context: dict,
) -> str:
    """Generate a specific report section narrative."""
    if section == 'executive_summary':
        prompt = f"""
Write the executive summary of an ML experiment report in exactly 3 sentences.

Context:
  Best model: {context.get('best_model', 'N/A')}
  Primary metric ({context.get('metric', 'N/A')}): {context.get('metric_value', 'N/A')}
  Improvement over baseline: {context.get('improvement', 0)}
  Number of experiments: {context.get('n_experiments', 0)}
  Task type: {context.get('task_type', 'N/A')}

Rules:
  - 3 sentences maximum. No more.
  - Every sentence must reference a specific number from the context above.
  - Do not use phrases like: "suggests its suitability", "strong performance",
    "solid foundation", "demonstrates the effectiveness", "key findings",
    "experimental approach", or any other generic filler.
  - Write like a data scientist reporting to a colleague. Terse and precise.
  - State the best model name, its exact metric value, and the improvement
    over baseline explicitly.
"""
    else:
        prompt = f"""
Write the '{section}' section of an ML experiment report.

Context data:
{context}

Rules:
- Be concise and precise.
- Every claim must reference the provided data.
- No fabricated numbers.
- Aim for 100-200 words.
"""
    return call_llm(prompt, max_tokens=400)

# Helpers
def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
    return text.strip()
