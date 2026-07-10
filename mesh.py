import json
import os

from openai import OpenAI


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _client() -> OpenAI:
    return OpenAI(
        api_key=_required_env("MESH_API_KEY"),
        base_url=_required_env("MESH_BASE_URL"),
    )


def _mesh_model() -> str:
    return os.getenv("MESH_MODEL", "openai/gpt-4o-mini")


def _extract_json(content: str) -> dict:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def extract_fields(transcript: str, prior_context: dict | None = None) -> dict:
    """Returns dict: category, income_lakh, purpose, state, raw_summary.
    If prior_context given, merge/update rather than starting fresh.
    System prompt instructs: output ONLY valid JSON.
    """
    fallback = {
        "category": None,
        "income_lakh": None,
        "purpose": None,
        "state": None,
        "raw_summary": transcript[:300],
    }
    try:
        client = _client()
        prompt = {
            "transcript": transcript,
            "prior_context": prior_context,
            "required_fields": ["category", "income_lakh", "purpose", "state", "raw_summary"],
            "instructions": "Merge with prior_context if present. Unknown values must be null.",
        }
        response = client.chat.completions.create(
            model=_mesh_model(),
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract user facts for Indian welfare-scheme matching. "
                        "Output ONLY valid JSON with keys: category, income_lakh, purpose, state, raw_summary. "
                        "No markdown fences, no prose, no extra keys. Use null for unknown values."
                    ),
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
        )
        print(f"[Mesh] extract_fields routed model: {getattr(response, 'model', 'unknown')}")
        raw = response.choices[0].message.content or "{}"
        parsed = _extract_json(raw)
        return {
            "category": parsed.get("category"),
            "income_lakh": parsed.get("income_lakh"),
            "purpose": parsed.get("purpose"),
            "state": parsed.get("state"),
            "raw_summary": parsed.get("raw_summary") or transcript[:300],
        }
    except Exception as exc:
        print(f"[Mesh] extract_fields failed: {exc}")
        return fallback


def reason_eligibility(extracted_fields: dict, matched_schemes: list[dict]) -> str:
    """Reason over extracted fields and matched schemes and return plain-language guidance."""
    fallback = (
        "Mujhe thoda issue aa gaya details process karne mein. "
        "Aap dobara voice note bhejiye aur category, income, state, aur purpose clear boliye."
    )
    try:
        client = _client()
        payload = {
            "user_fields": extracted_fields,
            "candidate_schemes": matched_schemes,
        }
        response = client.chat.completions.create(
            model=_mesh_model(),
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a scheme eligibility assistant. Reason step by step internally. "
                        "Filter out schemes whose state is incompatible with the user's state, "
                        "except schemes marked 'All India'. Then pick best match(es), explain eligibility "
                        "in simple plain English suitable for text-to-speech, and list required documents. "
                        "Return 3-5 sentences, no markdown."
                    ),
                },
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        )
        print(f"[Mesh] reason_eligibility routed model: {getattr(response, 'model', 'unknown')}")
        result = (response.choices[0].message.content or "").strip()
        return result if result else fallback
    except Exception as exc:
        print(f"[Mesh] reason_eligibility failed: {exc}")
        return fallback