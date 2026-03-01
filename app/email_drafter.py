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
        return field_metadata
    
    # Sets all of the metadata vairables
    recipient_name = get_metadata(metadata.get("Recipient", {}), "Relevant Party")
    doc_type = get_metadata(metadata.get("Document Type", {}))
    policy_number = get_metadata(metadata.get("Policy Numbers", {}))
    date_of_loss = get_metadata(metadata.get("Date Of Loss", {}))
    claimant_name = get_metadata(metadata.get("Claimant", {}))
    defendant_name = get_metadata(metadata.get("Defendant", {}))
    case_ref_number = get_metadata(metadata.get("Case Reference Numbers", {}))
    
    subject_map = { #Subject is decided based on document type
        "notice": "Regulatory Notice Received",
        "lawsuit": "Legal Action Documentation",
        "legal correspondence": "Legal Correspondence Received",
        "other": "Document Processing Notification"
    }
    subject = subject_map.get(doc_type, "Document Processing Notification")
    
    # Build the email draft
    email_draft = f"""To: {recipient_name}
Subject: {subject} - {policy_number}

Dear {recipient_name},

Please find below a summary of the document processed through our AI-assisted document processing system.

DOCUMENT INFORMATION
────────────────────
Document Type:          {doc_type}
Source File:            {filename}
Processing Request ID:  {request_id}

IMPORTANT DETAILS
────────────────────
Policy Number:          {policy_number}
Date of Loss:           {date_of_loss}
Case Reference:         {case_ref_number}

PARTIES INVOLVED
────────────────────
Claimant:               {claimant_name}
Defendant:              {defendant_name}

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
    
    return email_draft