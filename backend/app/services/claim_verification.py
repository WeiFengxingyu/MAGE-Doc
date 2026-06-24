import re
import time
from typing import Any

from sqlalchemy.orm import Session

from app.services.documents import get_document

NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?%?\b")
WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_%-]*|[\u4e00-\u9fff]{2,}")
TEMPLATE_PREFIXES = (
    "based on table evidence",
    "based on text evidence",
    "the most relevant row is",
)
STOPWORDS = {
    "based",
    "table",
    "text",
    "evidence",
    "page",
    "most",
    "relevant",
    "row",
    "the",
    "and",
    "or",
    "on",
    "in",
    "is",
    "was",
    "were",
    "what",
    "which",
    "this",
    "that",
    "with",
    "from",
    "because",
}


def _elapsed_ms(start: float) -> int:
    return max(0, int((time.perf_counter() - start) * 1000))


def _trace(tool_name: str, input_payload: dict[str, Any], output_summary: str, start: float) -> dict:
    return {
        "tool_name": tool_name,
        "input": input_payload,
        "output_summary": output_summary,
        "latency_ms": _elapsed_ms(start),
    }


def _normalize(value: str) -> str:
    return " ".join(value.lower().split())


def _split_claims(answer: str) -> list[str]:
    normalized = answer.replace("\n", " ")
    parts = re.split(r"(?<=[.!?。！？])\s+|[;；]", normalized)
    claims: list[str] = []
    for part in parts:
        clean = part.strip()
        if not clean:
            continue
        lower = clean.lower()
        for prefix in TEMPLATE_PREFIXES:
            if lower.startswith(prefix):
                clean = clean[len(prefix) :].strip(" :,.")
                lower = clean.lower()
        if len(clean) >= 8:
            claims.append(clean)
    return claims or ([answer.strip()] if answer.strip() else [])


def _numbers(value: str) -> list[str]:
    without_page_refs = re.sub(r"\bpage\s+\d+\b", " ", value, flags=re.IGNORECASE)
    return NUMBER_PATTERN.findall(without_page_refs)


def _keywords(value: str) -> list[str]:
    words = []
    for word in WORD_PATTERN.findall(value):
        lower = word.lower()
        if lower in STOPWORDS or lower.isdigit() or len(lower) < 3:
            continue
        words.append(lower)
    return list(dict.fromkeys(words))


def _citation_text(citations: list[dict]) -> str:
    return " ".join(str(citation.get("snippet") or "") for citation in citations)


def _citation_node_ids(citations: list[dict]) -> list[str]:
    return [str(citation.get("node_id")) for citation in citations if citation.get("node_id")]


def _citation_node_types(citations: list[dict]) -> set[str]:
    return {str(citation.get("node_type")) for citation in citations if citation.get("node_type")}


def _required_node_types(question_type: str, claim: str) -> list[str]:
    lower = claim.lower()
    if question_type == "table_lookup" or any(term in lower for term in ("table", "row", "metric table")):
        return ["table", "table_cell"]
    return []


def _verify_claim(claim: str, citations: list[dict], question_type: str) -> dict:
    citation_ids = _citation_node_ids(citations)
    required_types = _required_node_types(question_type, claim)
    if not citation_ids:
        return {
            "claim": claim,
            "status": "insufficient_evidence",
            "citation_node_ids": [],
            "reason": "No citations were provided for this claim.",
            "matched_terms": [],
            "missing_terms": _numbers(claim) + _keywords(claim)[:5],
            "required_node_types": required_types,
        }

    evidence_text = _normalize(_citation_text(citations))
    claim_numbers = _numbers(claim)
    claim_keywords = _keywords(claim)
    matched_numbers = [number for number in claim_numbers if number.lower() in evidence_text]
    missing_numbers = [number for number in claim_numbers if number.lower() not in evidence_text]
    matched_keywords = [keyword for keyword in claim_keywords if keyword in evidence_text]
    missing_keywords = [keyword for keyword in claim_keywords if keyword not in evidence_text]
    citation_types = _citation_node_types(citations)
    type_ok = not required_types or bool(citation_types & set(required_types))

    if missing_numbers:
        status = "partial" if matched_keywords or matched_numbers else "unsupported"
        reason = "Citation exists, but key numeric terms are missing from evidence."
    elif not type_ok:
        status = "partial"
        reason = "Citation exists, but the claim expects table-level evidence."
    elif matched_keywords or matched_numbers:
        status = "supported"
        reason = "Citation evidence contains the key claim terms."
    else:
        status = "unsupported"
        reason = "Citation evidence has little overlap with the claim."

    return {
        "claim": claim,
        "status": status,
        "citation_node_ids": citation_ids,
        "reason": reason,
        "matched_terms": [*matched_numbers, *matched_keywords],
        "missing_terms": [*missing_numbers, *missing_keywords[:5]],
        "required_node_types": required_types,
    }


def _overall_status(claims: list[dict]) -> str:
    if not claims:
        return "insufficient_evidence"
    statuses = {claim["status"] for claim in claims}
    if statuses == {"supported"}:
        return "supported"
    if "unsupported" in statuses:
        return "unsupported"
    if "partial" in statuses:
        return "partial"
    return "insufficient_evidence"


def verify_claims(
    db: Session,
    document_id: str,
    *,
    answer: str,
    citations: list[dict],
    question_type: str,
) -> dict:
    start = time.perf_counter()
    get_document(db, document_id)
    claims = [_verify_claim(claim, citations, question_type) for claim in _split_claims(answer)]
    counts = {
        "supported_count": sum(1 for claim in claims if claim["status"] == "supported"),
        "partial_count": sum(1 for claim in claims if claim["status"] == "partial"),
        "unsupported_count": sum(1 for claim in claims if claim["status"] == "unsupported"),
        "insufficient_evidence_count": sum(
            1 for claim in claims if claim["status"] == "insufficient_evidence"
        ),
    }
    status = _overall_status(claims)
    input_payload = {
        "answer_length": len(answer.strip()),
        "citation_count": len(citations),
        "question_type": question_type,
    }
    return {
        "status": status,
        "claim_count": len(claims),
        **counts,
        "claims": claims,
        "tool_trace": _trace("verify_claims", input_payload, f"{len(claims)} claims: {status}", start),
    }
