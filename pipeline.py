import re
import uuid
from pathlib import Path

import form_fill
import memory
import mesh
import rag
import tts




def _safe_token(value: str) -> str:
    token = re.sub(r"[^a-zA-Z0-9_-]", "_", value)
    return token[:64] or "user"


def _default_scheme(extracted_fields: dict) -> dict:
    return {
        "id": "no_confident_match",
        "name": "No confident match",
        "category": extracted_fields.get("category") or "Any",
        "documents_required": [],
        "how_to_apply": "Share more details to get a better match.",
    }


def _build_user_data(user_id: str, extracted_fields: dict) -> dict:
    return {
        "full_name": f"Applicant {user_id}",
        "aadhaar_number": "0000-0000-0000",
        "category": extracted_fields.get("category"),
        "income_lakh": extracted_fields.get("income_lakh"),
        "state": extracted_fields.get("state"),
    }


async def run_turn(user_id: str, transcript: str) -> dict:
    prior_fields = await memory.get_last_fields(user_id)
    extracted_fields = mesh.extract_fields(transcript, prior_fields)

    matched_schemes = rag.find_best_match(extracted_fields)
    held_certificates = extracted_fields.get("held_certificates") or []
    if not matched_schemes:
        best_scheme = _default_scheme(extracted_fields)
        missing = []
        response_text = (
            "I couldn't find a government scheme matching that in my current dataset. "
            "Try describing your situation more specifically — your category "
            "(SC/ST/OBC/General/Minority), approximate family income, and what "
            "the support is for (education, health, housing, etc.)."
        )
    else:
        best_scheme = matched_schemes[0]
        missing = rag.missing_certificates(best_scheme, held_certificates)
        response_text = mesh.reason_eligibility(
            extracted_fields,
            matched_schemes,
            missing_certificates=missing,
        )
    await memory.save_turn(user_id, transcript, extracted_fields, response_text)

    output_dir = Path(__file__).with_name("generated")
    output_dir.mkdir(exist_ok=True)
    turn_id = uuid.uuid4().hex
    safe_user_id = _safe_token(user_id)

    audio_path = str(output_dir / f"reply_{safe_user_id}_{turn_id}.mp3")
    tts_path = tts.synthesize(response_text, audio_path)

    user_data = _build_user_data(user_id, extracted_fields)
    form_target = best_scheme
    if missing:
        first_missing = missing[0]
        form_target = {
            "id": first_missing.get("id"),
            "name": f"Prerequisite: {first_missing.get('name', 'Certificate')}",
            "category": extracted_fields.get("category") or "Any",
            "documents_required": first_missing.get("documents_required", []),
            "how_to_apply": first_missing.get("how_to_apply", ""),
        }

    form_path = form_fill.render_form(user_data, form_target)

    return {
        "reply_text": response_text,
        "reply_audio_path": tts_path,
        "form_html_path": form_path,
    }
