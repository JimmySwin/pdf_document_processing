# AI-Assisted Document Processing Pipeline

## Overview

This proof of concept demonstrates an AI-enabled workflow for processing incoming insurance and legal PDF documents in a structured and auditable manner. The objective was to develop an automated system that was capable of document classification and key metadata extraction, whilst being suitable for use in a regulated environment like insurance.

This solution combines Regular Expressions (Regex) and Large Language Models (LLMs) for interpreting document type and retrieving metadata from unstructured PDF documents that are ingested. The result is a workflow that illustrates how LLMs can be implemented into these systems responsibly by prioritising guardrails and transparency.

## Features

- **Hybrid Regex + LLM Extraction** - Structured fields via regex (policy numbers, dates, case references), semantic fields via GPT-4o (document type, parties, ect)
- **Multi-Method Processing** - Configurable extraction methods (multi_call for accuracy, single_call for speed)
- **Document Classification** - Four predefined categories: notice, lawsuit, legal correspondence, other
- **Audit Trail & Observability** - Unique request IDs, processing timestamps, latency tracking, SQLite database
- **Structured Metadata Extraction** - Policy numbers, dates of loss, case references, recipients, claimants, defendants, document types
- **Draft Email Generation** - Produces ready-to-customise email notifications with extracted metadata
- **Error Handling** - Explicit rejection path for unsupported document types with clear reasoning
- **Comprehensive Testing** - 17 unit tests covering extraction, edge cases, and validation

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate  # On Mac/Linux
# venv\Scripts\activate   # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 5. Process PDFs
python app/main.py                                    # Default: multi_call method
python app/main.py --method single_call               # Faster processing
python app/main.py --input-dir /path/to/folder        # Custom folder

# 6. Run tests
pytest tests/ -v

# 7. Check results
# Outputs saved to: audit.db (SQLite), logs/ (processing logs)
```

## How It Works

The pipeline processes legal documents through a four-stage workflow:

**PDF Input → PDF Extraction → Regex + LLM Extraction → Validation → SQLite DB → Email Draft**

### Stage 1: PDF Ingestion Layer

Once a PDF is submitted to the pipeline, the raw text is the first thing to be extracted using PyPDF2, and it is normalised (stripped of extra whitespaces) to handle inconsistent formatting.

### Stage 2: Hybrid Extraction Layer

A hybrid extraction approach is then used to separate out the metadata required:

1. **Document Classification via LLM** - An LLM is used to classify the document into one of four categories (notice, lawsuit, legal correspondence and other). If "other" is selected, then an early exit occurs, and the document is rejected.

2. **Structured Field Extraction via Regex** - Regex is then used to pull out the structured fields that have known patterns: policy numbers, dates and case reference numbers. This guarantees precision as long as those values appear with the correct format within the document.

3. **Semantic Field Extraction via Multi-Call LLM** - Multiple API calls occur to both verify the Regex data and extract the other, less structured data types (recipient, claimant, defendant).

### Stage 3: Validation & Storage

Whilst all of this is going on, the pipeline is constantly keeping track of important logs (time taken, when started) and saving important information (metadata, unique request id) to an SQLite database to act as an audit trail. Validation checks occur to make sure all data is present, and if not fills in the gaps.

### Stage 4: Output Generation

A draft email is then created with all the metadata provided. This email comes from a structured draft and not an LLM, thus mitigating hallucinations at this stage.

**This modular design enables independent scaling of each component and clear separation of concerns.**

## Architecture

The system is organised into four modular components that work sequentially to process legal documents end-to-end:

1. **PDF Ingestion Layer** - Text extraction and preprocessing from PDF files
2. **Hybrid Extraction Layer** - Regex for structured fields, LLM for semantic fields  
3. **Validation & Storage Layer** - Completeness checks, SQLite audit trail with request IDs
4. **Output Layer** - Draft emails with extracted metadata for human review

## Technical Choices

### 1. Hybrid Regex + LLM Approach

**Structured fields have predictable patterns and can be easily extracted using a regex approach.** This works better than using LLMs, as Regex is much faster, whilst also being 100% accurate to the pattern given and free. Minimising the risks of hallucination is ideal in these regulated environments. However, semantic fields require LLM interaction to work out what the correct data to extract is.

**Trade-off:** Hybrid approach requires field validation logic, but eliminates false positives on structured fields and reduces API costs by ~60% vs full-LLM extraction.

### 2. Multi-Call vs Single-Call Extraction

Research was done on both methods:
- **Multi-call:** Separate API call for each metadata field (7 API calls) → ~10.7s average
- **Single-call:** One combined call extracting all metadata → ~7.9s average

**Decision: Multi-call method chosen despite 35% slower speed.**

After extensive testing, it was decided to go with multi-call. On average single call took 73% of the time that multi call took, along with it being 7 times cheaper; however, it more often than not rejected an extra document it shouldn't. On top of this, it on average missed 0.33 metadata fields per run. **In such a regulated industry where high accuracy is of the utmost importance, the accuracy outweighs the costs of a single call.**

**Trade-off:** Higher latency and cost, but 5% higher accuracy and better operational visibility (per-field error handling, cleaner audit trail).

### 3. Model Selection: GPT-4o

**Temperature set to 0 (deterministic):** As legal documents require reproducible extraction, the same input PDF should produce identical results for audit compliance.

Three GPT-4 models were tested:
- GPT-4.1-nano
- GPT-4o-mini  
- GPT-4o

After testing, both GPT-4.1 and GPT-4o-mini wrongly rejected more documents and surprisingly were slower than GPT-4o. **Therefore, GPT-4o was chosen as the model of choice.**

**Trade-off:** Higher cost per document, but perfect classification accuracy and deterministic results essential for legal domain.

### 4. SQLite Audit Trail

**Structured metadata stored with timestamps, request IDs, processing latency, and rejection reasons.** Enables regulatory compliance and performance analysis.

**Trade-off:** Sufficient for proof-of-concept, but production would use PostgreSQL for concurrent access and time-series DB for analytics.

## Processing Performance

```
6 PDFs processed with multi_call method:

Total documents processed:    6
Accepted:                     5
Rejected:                     1 (Conference Brochure - out of scope)
Acceptance rate:              83.3%

Total time:                   38.38s
Avg time per document:        6.40s
```

| Document | Time | Status |
|----------|------|--------|
| Coverage Position Letter | 10.67s | ✓ Accepted |
| First Notice of Loss | 7.89s | ✓ Accepted |
| Settlement Offer | 5.88s | ✓ Accepted |
| Court Scheduling Order | 5.19s | ✓ Accepted |
| Regulatory Inquiry Notice | 7.95s | ✓ Accepted |
| Conference Brochure | 0.81s | ✗ Rejected |

## Email Draft Example

```
To: oakview.broker@brokerage.test
Subject: Legal Correspondence Received - PN25PROP005431

Dear oakview.broker@brokerage.test,

Please find below a summary of the document processed through our 
AI-assisted document processing system.

DOCUMENT INFORMATION
────────────────────
Document Type:          legal correspondence
Source File:            Coverage Position Letter – Storm Damage at Oakview Farm.pdf
Processing Request ID:  18364d9f-463c-4d4c-9541-f60ae788e1f5

IMPORTANT DETAILS
────────────────────
Policy Number:          PN25PROP005431
Date of Loss:           18 October 2025
Case Reference:         PN25PROP005431

PARTIES INVOLVED
────────────────────
Claimant:               Oakview Farm
Defendant:              Not specified

ACTION REQUIRED
────────────────────
Please review the above information and take appropriate action as required 
by Lloyd's of London procedures.

Best regards,
Lloyd's of London Document Processing System

---
[AUTO-GENERATED EMAIL DRAFT]
Request ID: 18364d9f-463c-4d4c-9541-f60ae788e1f5
```

## Database Schema

**documents table:**
```sql
CREATE TABLE documents (
    id                 INTEGER PRIMARY KEY,
    request_id         TEXT NOT NULL,
    filename           TEXT NOT NULL,
    processed_at       TEXT NOT NULL,
    extraction_method  TEXT NOT NULL,
    elapsed_seconds    REAL NOT NULL,
    rejected           INTEGER NOT NULL DEFAULT 0,
    rejection_message  TEXT
);
```

**extracted_fields table:**
```sql
CREATE TABLE extracted_fields (
    id           INTEGER PRIMARY KEY,
    document_id  INTEGER NOT NULL REFERENCES documents(id),
    field_name   TEXT NOT NULL,
    value        TEXT,
    changed      INTEGER,
    explanation  TEXT
);
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_pipeline.py::TestPolicyNumberExtraction -v
```

**Test Coverage:** 17 unit tests covering:
- Policy number extraction (regex)
- Case reference extraction (regex)
- Date extraction (regex + edge cases)
- Edge cases (empty text, whitespace, case sensitivity)
- Mixed content extraction

**Results:** 17/17 passing

## Assumptions & Trade-offs

### Key Assumptions

The following assumptions were made to scope the proof-of-concept within the time constraints:

1. **PDF Format:** All input documents are in PDF form and thus need no OCR (or other methods) to extract text. Adding this is quite easy, however, as the code is modular.

2. **Data Consistency:**
   - All policy numbers follow the pattern `PN-XX-YY-(other alphanumeric characters)` with X representing numbers and Y representing letters
   - Case Reference numbers follow the pattern `YYYY-XXXX-XXXXXX`, with X representing numbers and Y representing letters
   - All dates are provided in the format of `DD Month YYYY` (e.g. 28 November 2025)

3. **Document Scope:**
   - Each PDF contains a single document
   - All important information within each document is written in English
   - All legal documents are standard legal document types

4. **Validation:** Labels like recipient and Policy Numbers are not cross-checked against an already existing database and can be taken verbatim.

### What Was Simplified Due to Time Constraints

To deliver a functional proof-of-concept in the allocated timeframe, the following features were intentionally deferred:

1. **Single-Threading Processing:** Currently, all PDFs are processed sequentially, which could really slow down production. Especially if all current PDF's were ingested at launch to build up a database. Production would make use of message queues (Celery, for example) to allow for parallel processing across nodes.

2. **Limited Guardrails:**
   - Human in the loop for rejected documents - After a document is rejected, it could be added to a list of documents that a human needs to check to make sure it's void
   - Date checks - DOL can't be in the future, for example
   - LLM output transparency - Can improve this to use another LLM as a peer reviewer to check, or random human checks

3. **Minimal UI:** No webapp or dashboard for a team to use, just CLI input and output. Could also include performance metrics, as well as being easier to use.

4. **Testing and Error Handling:** Added some of each for proof of concept, but would need more for production.

5. **Confidence Scoring:** Add probabilities for each extracted field (e.g., "77% confident this is the claimant name"). Use this to auto-route low-confidence documents to the human review queue.

## Project Structure

```
pdf_document_processing/
├── conftest.py               # Pytest configuration
├── app/
│   ├── main.py              # Entry point, CLI argument parsing
│   ├── config.py            # Path and API key configuration
│   ├── pdf_ingestion.py     # PDF text extraction & preprocessing
│   ├── extractor.py         # Regex + LLM metadata extraction
│   ├── db.py                # SQLite schema and operations
│   ├── email_drafter.py     # Email draft generation
│   ├── logger.py            # Structured logging
│   └── models.py            # Data models
├── tests/
│   ├── test_pipeline.py     # 17 unit tests
│   └── __init__.py
├── data/                    # Input PDFs (6 mock documents)
├── logs/                    # Processing logs (auto-generated)
├── audit.db                 # SQLite database (auto-generated)
├── requirements.txt         # Dependencies
├── .env.example             # Template for environment variables
└── README.md                # This file
```

## Enterprise-Grade Architecture: Scaling to 15,000 Docs/Year

### Ingestion Layer

Documents arrive via multiple channels and are deposited in a large cloud storage (Azure blob storage). Ingestion is also extended to handle multiple types of documents, such as email.

### Hybrid Extraction Layer

Instead of using Python's single-threaded system, leverage Databricks' distributed computing so that extraction logic can run in parallel, speeding up the multi-call method massively. 

**Additional Enhancements:**
- If any documents are rejected, then add them to a human-in-the-loop validation pile so that they don't get missed
- Cross-check all valid fields (policy number, for example) with the Lloyds database to make sure the extraction was correct
- Could use another LLM to check over all results at the end and flag any strange outputs to a human, hopefully reducing errors
- Instead of direct OpenAI API calls, use Azure OpenAI Service (deployed in-region for data residency) with retry logic, rate limiting, and caching
- Batch API endpoints can process multiple documents in parallel

### Logging and Storage

Extracted metadata flows to Azure Synapse SQL pool (data warehouse) for querying and analytics. Raw documents and processing logs are stored in Azure Blob Storage with 7-year retention for audit compliance.

### Output Layer

Add different templates for different file types, could also provide a generic template along with AI generated one. This template will have the context of the initial document, so it will be tailored to the issue and likely ready to send.

### Monitoring and Compliance

**Observability Stack** uses Azure Monitor and Application Insights to track:
- Processing latency
- LLM token usage and costs
- Acceptance rate and rejection reasons
- Extraction accuracy vs human verification

**Security & Compliance** implemented via:
- Azure Key Vault for API key management
- Audit logging in Azure Table Storage
- Encryption at rest and in transit
- Role-based access control (RBAC)
- Data residency compliance per jurisdiction

## Troubleshooting

**OpenAI API error: "Invalid API key"**
```bash
cat .env | grep OPENAI_API_KEY
export OPENAI_API_KEY=sk-...
# Or recreate .env from template:
cp .env.example .env
```

**PDF extraction returns empty text**
```bash
# Verify the PDF has extractable text (not image-only):
python -c "from app.pdf_ingestion import extract_text_from_pdf; print(extract_text_from_pdf('path/to/pdf.pdf')[:500])"
```

**Database locked error**
```bash
rm audit.db
python app/main.py
```

## Requirements

- Python 3.11+
- OpenAI API key (GPT-4o model)
- See `requirements.txt` for dependencies

## Future Enhancements

### Short-term (1-2 months)
- OCR & multi-format support (Word, email, scanned documents)
- Validation guardrails (policy number validation, date sanity checks)
- Performance dashboard for operations team
- Confidence scoring for extracted fields

### Medium-term (3-6 months)
- Human feedback loop for continuous improvement
- Peer review via second LLM
- Azure Databricks integration for distributed processing
- PostgreSQL migration for production scale

### Long-term (6+ months)
- Full Databricks + Azure enterprise deployment
- Multi-jurisdiction support with compliance rules
- Advanced analytics and trend detection
- Agentic workflows for complex documents

