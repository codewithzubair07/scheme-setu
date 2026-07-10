import chromadb

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


def find_best_match(extracted_fields: dict, n_results: int = 3) -> list[dict]:
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
    if not metadatas or not metadatas[0]:
        return []
    return [_metadata_to_scheme(item) for item in metadatas[0]]