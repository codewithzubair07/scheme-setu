import chromadb

from certificates_data import CERTIFICATES
from schemes_data import SCHEMES


client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="schemes")


def _bootstrap_collection() -> None:
    existing_count = collection.count()
    if existing_count == 10:
        return

    if existing_count > 0:
        all_items = collection.get()
        ids = all_items.get("ids", [])
        if ids:
            collection.delete(ids=ids)

    documents = []
    metadatas = []
    ids = []

    for scheme in SCHEMES:
        document = (
            f"name: {scheme['name']}; category: {scheme['category']}; "
            f"purpose: {scheme['purpose']}; state: {scheme['state']}; "
            f"eligibility: {scheme['eligibility_text']}"
        )
        metadata = {
            "id": scheme["id"],
            "name": scheme["name"],
            "category": scheme["category"],
            "income_limit_lakh": "None"
            if scheme["income_limit_lakh"] is None
            else str(scheme["income_limit_lakh"]),
            "purpose": scheme["purpose"],
            "state": scheme["state"],
            "eligibility_text": scheme["eligibility_text"],
            "documents_required": "||".join(scheme["documents_required"]),
            "how_to_apply": scheme["how_to_apply"],
        }
        documents.append(document)
        metadatas.append(metadata)
        ids.append(scheme["id"])

    collection.add(ids=ids, documents=documents, metadatas=metadatas)


def _metadata_to_scheme(metadata: dict) -> dict:
    income_str = metadata.get("income_limit_lakh")
    income_limit = None if income_str in (None, "None") else float(income_str)
    docs = metadata.get("documents_required", "")
    docs_list = docs.split("||") if docs else []
    return {
        "id": metadata.get("id"),
        "name": metadata.get("name"),
        "category": metadata.get("category"),
        "income_limit_lakh": income_limit,
        "purpose": metadata.get("purpose"),
        "state": metadata.get("state"),
        "eligibility_text": metadata.get("eligibility_text"),
        "documents_required": docs_list,
        "how_to_apply": metadata.get("how_to_apply"),
    }


_bootstrap_collection()


def find_best_match(
    extracted_fields: dict, n_results: int = 3, max_distance: float = 1.2
) -> list[dict]:
    """Return schemes that are actually close to the query.

    max_distance filters out weak/irrelevant matches so an out-of-scope
    query returns an empty list instead of forcing the nearest-but-wrong
    scheme. Chroma's default distance is smaller = closer; tune
    max_distance for this dataset if real queries show it's too strict
    or too loose.
    """
    category = extracted_fields.get("category")
    income_lakh = extracted_fields.get("income_lakh")
    purpose = extracted_fields.get("purpose")
    state = extracted_fields.get("state")

    query = (
        f"category: {category}, income: {income_lakh} lakh, "
        f"purpose: {purpose}, state: {state}"
    )
    result = collection.query(query_texts=[query], n_results=n_results)
    metadatas = result.get("metadatas", [[]])
    distances = result.get("distances", [[]])
    if not metadatas or not metadatas[0]:
        return []

    matches = []
    for metadata, distance in zip(metadatas[0], distances[0]):
        if distance <= max_distance:
            matches.append(_metadata_to_scheme(metadata))
    return matches


def missing_certificates(scheme: dict, held: list[str]) -> list[dict]:
    required_docs = [str(doc).lower() for doc in (scheme.get("documents_required") or [])]
    held_normalized = {item.strip().lower() for item in (held or []) if item}

    missing = []
    for certificate in CERTIFICATES:
        cert_name = certificate.get("name", "").lower()
        cert_id = certificate.get("id", "").lower()
        if any(cert_name in doc or cert_id.replace("_", " ") in doc for doc in required_docs):
            if cert_name not in held_normalized and cert_id not in held_normalized:
                missing.append(certificate)
    return missing
