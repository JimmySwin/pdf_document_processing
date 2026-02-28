"""
Email Draft Generator
Designed to be taken and customised before sending.
"""

def generate_email_draft(metadata: dict, request_id: str, filename: str) -> str:
    """
    Generates a draft email from extracted metadata.
    """
    
    def get_metadata(field, fallback="Not specified"):
        """Extract the 'metadata' from a field dict, or return fallback if 'Not Found'
        Gives all fields a value to avoid issues in the email template, and makes it clear when something was not extracted."""
        field_metadata = field.get("value", fallback)
        return fallback if field_metadata == "Not Found" else field_metadata
    
    # get the metadata values 
    recipient_value = get_metadata(metadata.get("Recipient", {}), "Relevant Party")
    doc_type_value = get_metadata(metadata.get("Document Type", {}))
    policy_value = get_metadata(metadata.get("Policy Numbers", {}))
    date_value = get_metadata(metadata.get("Date Of Loss", {}))
    claimant_value = get_metadata(metadata.get("Claimant", {}))
    defendant_value = get_metadata(metadata.get("Defendant", {}))
    case_ref_value = get_metadata(metadata.get("Case Reference Numbers", {}))
    
    subject_map = { #Subject is decided based on document type
        "notice": "Regulatory Notice Received",
        "lawsuit": "Legal Action Documentation",
        "legal correspondence": "Legal Correspondence Received",
        "other": "Document Processing Notification"
    }
    subject = subject_map.get(doc_type_value, "Document Processing Notification")
    
    # Build the email draft
    email_draft = f"""To: {recipient_value}
Subject: {subject}

Dear {recipient_value},

Please find below a summary of the document processed through our AI-assisted document processing system.

DOCUMENT INFORMATION
────────────────────
Document Type:          {doc_type_value}
Source File:            {filename}
Processing Request ID:  {request_id}

IMPORTANT DETAILS
────────────────────
Policy Number:          {policy_value}
Date of Loss:           {date_value}
Case Reference:         {case_ref_value}

PARTIES INVOLVED
────────────────────
Claimant:               {claimant_value}
Defendant:              {defendant_value}

ACTION REQUIRED
────────────────────
Please review the above information and take appropriate action as required by Lloyd's of London procedures.

If you have any questions or require clarification on any of the extracted information, please reference the Request ID above.

Best regards,
Lloyd's of London Document Processing System

---
[AUTO-GENERATED EMAIL DRAFT]
This is an automated draft generated for your review. Please customise as needed before sending.
Request ID: {request_id}
"""
    
    return email_draft.strip()