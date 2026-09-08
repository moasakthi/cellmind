"""Azure OpenAI-backed reasoning layer for CellMind.

Owns all interaction with Azure OpenAI. The classifier in ml/predict.py
(via ml_bridge.py) answers "what defect is this" from an image; this module
answers "why did this happen" and "what should we do about it" from the
structured data the rest of the backend already computes.

Both public functions raise AIUnavailableError on any failure (timeout,
auth, content filter, malformed response) — callers turn that into a 503,
matching the existing BR-11 fail-open pattern used elsewhere in main.py.
"""
import json
import os

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

_client = None


class AIUnavailableError(Exception):
    pass


def _get_client():
    global _client
    if _client is None:
        try:
            _client = AzureOpenAI(
                api_key=os.environ["AZURE_API_KEY"].strip().strip('"'),
                azure_endpoint=os.environ["AZURE_ENDPOINT"].strip().strip('"'),
                api_version=os.environ["AZURE_VERSION"].strip().strip('"'),
            )
        except KeyError as e:
            raise AIUnavailableError(f"Missing Azure OpenAI configuration: {e}") from e
    return _client


def _deployment():
    return os.environ.get("AZURE_DEPLOYMENT", "").strip().strip('"')


def current_model() -> str:
    return _deployment() or "unknown"


def _chat_json(system_prompt: str, user_payload: dict) -> dict:
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=_deployment(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, default=str)},
            ],
            response_format={"type": "json_object"},
            timeout=20,
        )
    except Exception as e:
        raise AIUnavailableError(f"Azure OpenAI request failed: {e}") from e

    content = (response.choices[0].message.content or "").strip()
    try:
        return json.loads(content)
    except (json.JSONDecodeError, IndexError) as e:
        raise AIUnavailableError(f"Azure OpenAI returned a non-JSON response: {e}") from e


INSIGHTS_SYSTEM_PROMPT = """You are CellMind's Insights & Reasoning agent for a solar-cell \
manufacturing quality platform. You are given a JSON snapshot of current plant telemetry \
(batches, risk distribution, equipment defect shares, camera fleet health, recent activity). \
Produce a concise, evidence-grounded analysis for quality/process engineers.

Rules:
- Every finding must cite at least one piece of evidence drawn from the given data (a batch id, \
equipment id, percentage, or count) — never state a finding you cannot ground in the data.
- Use cautious, qualified language ("appears to", "may indicate") — never assert a cause as certain.
- Produce 3 to 5 findings, ordered by severity (HIGH first).
- Respond with ONLY a JSON object matching exactly this shape, no other text:
{
  "summary": "2-3 sentence plant-health narrative",
  "confidenceBand": "HIGH" | "MEDIUM" | "LOW",
  "findings": [
    {
      "title": "short finding title",
      "severity": "LOW" | "MEDIUM" | "HIGH",
      "reasoning": "1-3 sentences explaining the finding, grounded in the provided data",
      "evidence": ["short evidence bullet", "another evidence bullet"],
      "recommendedFocus": "one sentence: what to look at or do next"
    }
  ]
}"""

RECOMMENDATION_SYSTEM_PROMPT = """You are CellMind's RootCause & Optimization reasoning agent for \
a solar-cell manufacturing quality platform. You are given the agent pipeline results for one \
investigation (inspection, process, context, root-cause findings and their evidence), the batch \
summary, an optional defect-taxonomy suggested action, and stats for any referenced equipment.

Rules:
- Ground every action in the given evidence — do not invent causes or data not present in the input.
- If the root cause is "Insufficient data", lower your confidence and lean toward general \
process-review actions rather than inventing a specific cause.
- Propose 2 to 4 corrective actions, ranked with the most impactful first.
- expectedImprovementPct is a defect-rate-reduction estimate in percentage points (0-10 range is typical).
- riskScore is 0.0 (no risk) to 1.0 (high risk) of the action itself causing a problem.
- Respond with ONLY a JSON object matching exactly this shape, no other text:
{
  "rootCauseNarrative": "2-4 sentence explanation of the probable root cause, grounded in the evidence",
  "actions": [
    {
      "title": "short action title",
      "cost": "Low" | "Medium" | "High",
      "expectedImprovementPct": number,
      "downtimeHours": number,
      "riskScore": number,
      "rationale": "1-2 sentences on why this action addresses the root cause"
    }
  ]
}"""


def generate_dashboard_insights(context: dict) -> dict:
    return _chat_json(INSIGHTS_SYSTEM_PROMPT, context)


def generate_recommendation(context: dict) -> dict:
    return _chat_json(RECOMMENDATION_SYSTEM_PROMPT, context)
