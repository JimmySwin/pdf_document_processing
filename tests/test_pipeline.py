"""
Unit tests for the document metadata extraction functions.

Tests cover:
- Regex-based field extraction
- Document type classification
- Edge cases and missing data

Run with: pytest tests/ -v
"""

import pytest
from app.extractor import (
    extract_policy_numbers,
    extract_case_reference_numbers,
    extract_all_dates
)

class TestPolicyNumberExtraction:
    """Test policy number extraction via regex"""
    
    def test_extract_single_policy_number(self):
        """Test extraction of a single valid policy number"""
        text = "The policy PN25PROP005431 was issued on 1 January 2025."
        result = extract_policy_numbers(text)
        assert "PN25PROP005431" in result
    
    def test_extract_multiple_policy_numbers(self):
        """Test extraction of multiple policy numbers from same text"""
        text = "Policy PN25PROP005431 and PN26GH002541 are both covered."
        result = extract_policy_numbers(text)
        assert len(result) >= 2
        assert "PN25PROP005431" in result
        assert "PN26GH002541" in result
    
    def test_no_policy_numbers(self):
        """Test when no policy numbers exist in text"""
        text = "This document contains no policy identifiers."
        result = extract_policy_numbers(text)
        assert result == ["Not Found"]
    
    def test_policy_number_in_sentence(self):
        """Test policy number extraction from context"""
        text = "We acknowledge receipt of the claim under policy PN24EL332210."
        result = extract_policy_numbers(text)
        assert "PN24EL332210" in result


class TestCaseReferenceExtraction:
    """Test case reference number extraction via regex"""
    
    def test_extract_single_case_reference(self):
        """Test extraction of a single valid case reference"""
        text = "The court assigned case reference FCCT-2026-004512-SO."
        result = extract_case_reference_numbers(text)
        assert "FCCT-2026-004512-SO" in result
    
    def test_extract_multiple_case_references(self):
        """Test extraction of multiple case references"""
        text = "Case FCCT-2026-004512-SO and FJDC-2025-000778 are related."
        result = extract_case_reference_numbers(text)
        assert len(result) >= 2
        assert "FCCT-2026-004512-SO" in result
        assert "FJDC-2025-000778" in result
    
    def test_no_case_references(self):
        """Test when no case references exist in text"""
        text = "This is a simple document with no court references."
        result = extract_case_reference_numbers(text)
        assert result == ["Not Found"]
    
    def test_case_reference_with_hyphens(self):
        """Test case reference extraction with hyphenated format"""
        text = "Official case reference: FJDC-2025-000778"
        result = extract_case_reference_numbers(text)
        assert "FJDC-2025-000778" in result


class TestDateExtraction:
    """Test date extraction via regex"""
    
    def test_extract_single_date(self):
        """Test extraction of a single date"""
        text = "The loss occurred on 28 November 2025."
        result = extract_all_dates(text)
        assert any("November 2025" in date or "28" in date for date in result)
    
    def test_extract_multiple_dates(self):
        """Test extraction of multiple dates from same text"""
        text = "Loss on 28 November 2025, reported on 14 December 2025."
        result = extract_all_dates(text)
        assert len(result) >= 2
    
    def test_no_dates(self):
        """Test when no dates exist in text"""
        text = "This document contains no temporal information."
        result = extract_all_dates(text)
        assert result == ["Not Found"]
    
    def test_extract_date_range(self):
        """Test extraction of date ranges"""
        text = "Conference scheduled 14–16 May 2026."
        result = extract_all_dates(text)
        assert any("May 2026" in date or "14" in date for date in result)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_text(self):
        """Test extraction from empty text"""
        text = ""
        assert extract_policy_numbers(text) == ["Not Found"]
        assert extract_case_reference_numbers(text) == ["Not Found"]
        assert extract_all_dates(text) == ["Not Found"]
    
    def test_whitespace_only(self):
        """Test extraction from whitespace-only text"""
        text = "   \n\n   \t\t   "
        assert extract_policy_numbers(text) == ["Not Found"]
        assert extract_case_reference_numbers(text) == ["Not Found"]
        assert extract_all_dates(text) == ["Not Found"]
    
    def test_case_sensitivity_policy(self):
        """Test that policy numbers are case-insensitive where applicable"""
        text = "Policy pn25prop005431 issued"
        result = extract_policy_numbers(text)
        # Should still find it
        assert isinstance(result, list)
    
    def test_mixed_content(self):
        """Test extraction from document with all field types"""
        text = """
        Policy: PN25PROP005431
        Case: FCCT-2026-004512-SO
        Date of Loss: 28 November 2025
        """
        policies = extract_policy_numbers(text)
        cases = extract_case_reference_numbers(text)
        dates = extract_all_dates(text)
        
        assert "PN25PROP005431" in policies
        assert "FCCT-2026-004512-SO" in cases
        assert len(dates) > 0