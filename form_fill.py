import html
import uuid
from pathlib import Path


def _annual_income_text(user_data: dict) -> str:
    income_lakh = user_data.get("income_lakh")
    if isinstance(income_lakh, (int, float)):
        return str(int(float(income_lakh) * 100000))
    return "Not Specified"


def _documents_html(target: dict) -> str:
    items = target.get("documents_required") or []
    if not items:
        return "<li>No specific document listed</li>"
    return "".join(f"<li>{html.escape(str(item))}</li>" for item in items)


def render_form(user_data: dict, target: dict) -> str:
    template_path = Path(__file__).with_name("mock_form.html")
    rendered = template_path.read_text(encoding="utf-8")

    replacements = {
        "full_name": str(user_data.get("full_name", "Applicant Name")),
        "aadhaar_number": str(user_data.get("aadhaar_number", "0000-0000-0000")),
        "category": str(user_data.get("category") or target.get("category") or "Any"),
        "annual_income": _annual_income_text(user_data),
        "state": str(user_data.get("state") or "Not Specified"),
        "scheme_name": str(target.get("name") or "No scheme matched"),
        "how_to_apply": str(target.get("how_to_apply") or ""),
        "documents_html": _documents_html(target),
    }

    for key, value in replacements.items():
        safe_value = value if key == "documents_html" else html.escape(value)
        rendered = rendered.replace(f"{{{{{key}}}}}", safe_value)

    output_dir = Path(__file__).with_name("generated")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"form_{uuid.uuid4().hex}.html"
    output_path.write_text(rendered, encoding="utf-8")
    return str(output_path)
