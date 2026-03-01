import re
import time
import json
from openai import OpenAI
from pdf_ingestion import extract_text_from_pdf, preprocess_text
from dotenv import load_dotenv
import os
from config import DATA_DIR

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
VALID_DOCUMENT_TYPES = ["notice", "lawsuit", "legal correspondence", "other"]

def extract_all_dates(text : str) -> list:
    '''Using regex to initially extract some information, this function does dates'''
    matches = re.findall(
        r"\b\d{1,2}(?:–\d{1,2})?\s(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}\b",
        text,
    )
    return list(set(matches)) if matches else ["Not Found"]

def extract_policy_numbers(text : str) -> list:
    matches = re.findall(r"PN\d{2}[A-Z]{2,}[A-Za-z0-9]+", text)
    return list(set(matches)) if matches else ["Not Found"]

def extract_case_reference_numbers(text : str) -> list:
    matches = re.findall(r"\b[A-Z]{4}-\d{4}-\d{6}(?:-[A-Z]{2})?\b", text)
    return list(set(matches)) if matches else ["Not Found"]

def extract_document_type(text : str) -> dict:
    """
    Classifies the document as one of: notice, lawsuit, legal correspondence, other.
    Returns a dict:
      - "value": Document label
      - "explanation": Quote of why the LLM chose that label
      - "reason": Used when other is picked to say why.
    """
    model = os.getenv("LLM_MODEL", "gpt-4o")

    prompt = f"""You are an expert legal document analyst working for Lloyd's of London.

Classify the document type. You MUST choose exactly one of these four values:
  - "notice"              – regulatory notices, warnings, formal notifications, coverage updates
  - "lawsuit"             – claims, judgments, court decisions, legal actions, court orders, scheduling orders
  - "legal correspondence" – letters, orders, and correspondence from legal parties, courts, or insurers
  - "other"               – documents that don't fit the above categories (e.g., brochures, marketing materials)

IMPORTANT: Be inclusive rather than exclusive. If a document relates to insurance, legal matters, or official business, classify it as one of the three main categories.

Examples:
  - Coverage position letter → "legal correspondence"
  - Court scheduling order → "lawsuit"
  - Insurance claim update → "notice"
  - Event brochure with no insurance/legal content → "other"

Return a JSON object with:
  "value"       – exactly one of the four values above (lowercase)
  "explanation" – the exact sentence or short phrase from the text that led you to this classification

If and only if value is "other", also include:
  "reason"      – a short explanation (preferably a direct quote from the document) of why
                  this document is not a notice, lawsuit, or legal correspondence

Return only the JSON object, no other text.

Document text:
{text}
"""

    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert legal document analyst. Always respond with valid JSON."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
        temperature=0, # low temperature for more deterministic output
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content.strip()) # Returns the first index as the API returns a list

    # Normalise value to lowercase changes and validate against allowed document types
    result["value"] = result.get("value", "other").lower()
    if result["value"] not in VALID_DOCUMENT_TYPES:
        result["value"] = "other"

    return result

def extract_with_llm(text, field, existing_data=None):
    """
    Extract or validate a single field via LLM.

    Returns a dict:
      - "value": the final extracted value
      - "changed": (only present when existing_data supplied) True if the LLM
                   corrected or changed the initial regex value
      - "explanation": the exact sentence/phrase from the text that supports
                       the chosen value (hallucination tracker)
    """
    model = os.getenv("LLM_MODEL", "gpt-4o")

    if existing_data:
        format_instruction = (
            'Return a JSON object with keys:\n'
            '  "value"       – the final extracted or validated value\n'
            '  "changed"     – true if you changed the provided existing value, false if you kept it\n'
            '  "explanation" – the exact sentence or short phrase from the text that led you to this value'
        )
        existing_line = f'Existing value (from regex): {existing_data}'
    else:
        format_instruction = (
            'Return a JSON object with keys:\n'
            '  "value"       – the extracted value, or "Not Found" if absent\n'
            '  "explanation" – the exact sentence or short phrase from the text that led you to this value'
        )
        existing_line = ''

    prompt = f"""You are an expert at extracting structured information from legal documents sent to Lloyd's of London.

Field to extract: {field}
{existing_line}

{format_instruction}
Return only the JSON object, no other text.

Document text:
{text}
"""

    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert legal document analyst. Always respond with valid JSON."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300, # low token limit as we expect short answers for each field, and this keeps costs down
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content.strip())




def rejected(doc_type_result : dict, elapsed : float) -> dict:
    """Builds the early-exit return value when a document type is 'other'."""
    reason = doc_type_result.get("reason") or doc_type_result.get("explanation", "No reason provided.") #Return reason unless its other so dosnt exist retunr explination
    return {
        "rejected": True,
        "message": f"This document isn't a notice, lawsuit or legal correspondence. Reason: {reason}",
        "elapsed_seconds": round(elapsed, 3),
    }




def extract_metadata_multi_call(text : str) -> dict:
    """
    Does one API call per field, with some initial regex extraction for certain fields to guide the LLM.
    Used to see the impact of multiple calls with more focused prompts and regex guidance vs a single all-in-one call.
    """
    start = time.perf_counter()

    doc_type = extract_document_type(text)
    if doc_type["value"] == "other":
        return rejected(doc_type, time.perf_counter() - start) # Early exit if document type is other, no need to extract other fields

    policy_numbers = extract_policy_numbers(text)
    case_reference_numbers = extract_case_reference_numbers(text)
    all_dates = extract_all_dates(text)

    metadata = {
        "Document Type": doc_type,
        "Policy Numbers": extract_with_llm(text, "Policy Numbers", existing_data=", ".join(policy_numbers)),
        "Case Reference Numbers": extract_with_llm(text, "Case Reference Numbers", existing_data=", ".join(case_reference_numbers)),
        "Date Of Loss": extract_with_llm(text, "Date Of Loss", existing_data=", ".join(all_dates)),
        "Recipient": extract_with_llm(text, "Recipient"),
        "Claimant": extract_with_llm(text, "Claimant"),
        "Defendant": extract_with_llm(text, "Defendant"),
    }

    elapsed = time.perf_counter() - start
    return {"metadata": metadata, "elapsed_seconds": round(elapsed, 3)}




def extract_metadata_single_call(text : str) -> dict:
    """
    All fields in a single API call, but with regex guidance for certain fields.
    This is more cost effective than multi_call and faster, while still providing
    good accuracy through regex pre-extraction.
    """
    model = os.getenv("LLM_MODEL", "gpt-4o")
    start = time.perf_counter()

    policy_numbers = extract_policy_numbers(text)
    case_reference_numbers = extract_case_reference_numbers(text)
    all_dates = extract_all_dates(text)

    prompt = f"""You are an expert at extracting structured information from legal documents sent to Lloyd's of London.

Extract all of the fields below from the document text and return a single JSON object.

Each field value must be a JSON object with:
  "value"       – the extracted value, or "Not Found" if absent
  "explanation" – the exact sentence or short phrase from the text that led you to this value

For "Document Type" specifically:
  - "value" MUST be exactly one of: "notice", "lawsuit", "legal correspondence", "other"
  - If "other", also include "reason": a short explanation or direct quote from the document
    explaining why it is not a notice, lawsuit, or legal correspondence

For fields with regex pre-extraction (see below), you MUST also include:
  - "changed": true if you changed/refined the regex value, false if you kept it as-is

Fields with regex pre-extraction:
  - Policy Numbers (regex value: {", ".join(policy_numbers)})
  - Case Reference Numbers (regex value: {", ".join(case_reference_numbers)})
  - Date Of Loss (regex value: {", ".join(all_dates)})

Other fields (no regex pre-extraction):
  - Recipient
  - Claimant
  - Defendant

Fields to extract:
  - Document Type
  - Policy Numbers
  - Case Reference Numbers
  - Date Of Loss
  - Recipient
  - Claimant
  - Defendant

Return only the JSON object, no other text.

Document text:
{text}
"""

    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert legal document analyst. Always respond with valid JSON."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=900,
        temperature=0,
        response_format={"type": "json_object"},
    )

    elapsed = time.perf_counter() - start
    metadata = json.loads(response.choices[0].message.content.strip())

    # Normalise document type value
    doc_type = metadata.get("Document Type", {})
    doc_type["value"] = doc_type.get("value", "other").lower()
    if doc_type["value"] not in VALID_DOCUMENT_TYPES:
        doc_type["value"] = "other"

    if doc_type["value"] == "other":
        return rejected(doc_type, elapsed)

    return {"metadata": metadata, "elapsed_seconds": round(elapsed, 3)}

if __name__ == "__main__":
    SAMPLE_PDF = DATA_DIR / "4 - First Notice of Loss – Water Escape at Sunbeam Apartments.pdf"

    if not SAMPLE_PDF.exists():
        print(f"Sample PDF not found at {SAMPLE_PDF}")
    else:
        raw_text = extract_text_from_pdf(SAMPLE_PDF)
        clean_text = preprocess_text(raw_text)

        print("=== Multi-call extraction ===")
        result = extract_metadata_multi_call(clean_text)
        print(f"Time: {result['elapsed_seconds']}s")
        if result.get("rejected"):
            print(result["message"])
        else:
            print(json.dumps(result["metadata"], indent=2))

        print("\n=== Single-call extraction ===")
        result = extract_metadata_single_call(clean_text)
        print(f"Time: {result['elapsed_seconds']}s")
        if result.get("rejected"):
            print(result["message"])
        else:
            print(json.dumps(result["metadata"], indent=2))
