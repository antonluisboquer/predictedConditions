"""
Empirical Confidence Calculator for Deficiency Detection

Calculates detection confidence based on evidence quality metrics:
- Evidence completeness
- Deficiency count
- Field specificity
- Evidence type (missing vs wrong)
- Reasoning quality
"""

import json
from typing import Dict, Any, List


def calculate_detection_confidence(deficiency_result: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate empirical detection confidence for a deficiency.
    
    Args:
        deficiency_result: Single result from step_4_5 detection
        config: Configuration dict with weights and scoring rules
        
    Returns:
        Dict with overall confidence and breakdown of components
    """
    weights = config["detection_confidence_weights"]
    
    # Calculate each component
    evidence_comp = score_evidence_completeness(deficiency_result)
    deficiency_count = score_deficiency_count(deficiency_result, config)
    field_spec = score_field_specificity(deficiency_result)
    evidence_type = score_evidence_type(deficiency_result, config)
    reasoning_qual = score_reasoning_quality(deficiency_result)
    
    # Weighted average
    overall = (
        evidence_comp * weights["evidence_completeness"] +
        deficiency_count * weights["deficiency_count"] +
        field_spec * weights["field_specificity"] +
        evidence_type * weights["evidence_type"] +
        reasoning_qual * weights["reasoning_quality"]
    )
    
    return {
        "overall": round(overall, 3),
        "breakdown": {
            "evidence_completeness": round(evidence_comp, 3),
            "deficiency_count_score": round(deficiency_count, 3),
            "field_specificity": round(field_spec, 3),
            "evidence_type": round(evidence_type, 3),
            "reasoning_quality": round(reasoning_qual, 3)
        }
    }


def score_evidence_completeness(deficiency_result: Dict[str, Any]) -> float:
    """
    Check if all deficiencies have complete fields.
    
    Returns 1.0 if all deficiencies have requirement, issue, field_checked, and evidence.
    Returns proportional score if some are incomplete.
    """
    deficiencies = deficiency_result.get("deficiencies", [])
    
    if not deficiencies:
        # No deficiencies listed means incomplete evidence
        return 0.2
    
    required_fields = ["requirement", "issue", "field_checked", "evidence"]
    total_fields = len(deficiencies) * len(required_fields)
    present_fields = 0
    
    for deficiency in deficiencies:
        for field in required_fields:
            if field in deficiency and deficiency[field]:
                present_fields += 1
    
    return present_fields / total_fields if total_fields > 0 else 0.0


def score_deficiency_count(deficiency_result: Dict[str, Any], config: Dict[str, Any]) -> float:
    """
    More deficiencies found = higher confidence in the detection.
    
    Uses config for scoring thresholds (1: 0.5, 2: 0.8, 3+: 1.0)
    """
    deficiencies = deficiency_result.get("deficiencies", [])
    count = len(deficiencies)
    
    scores = config["deficiency_count_scores"]
    
    if count == 0:
        return 0.3  # Status is deficient but no specific deficiencies listed
    elif count == 1:
        return scores["1"]
    elif count == 2:
        return scores["2"]
    else:  # 3 or more
        return scores["3+"]


def score_field_specificity(deficiency_result: Dict[str, Any]) -> float:
    """
    Score based on how specific the field references are.
    
    Specific field paths (e.g., "scheduleGPartII[].percentageOwned") score higher
    than vague references (e.g., "document", "form").
    """
    checked_fields = deficiency_result.get("checked_fields", [])
    deficiencies = deficiency_result.get("deficiencies", [])
    
    if not checked_fields and not deficiencies:
        return 0.2
    
    # Count specific field paths
    specific_indicators = [".", "[", "]", "_", "line", "schedule", "form"]
    total_refs = len(checked_fields)
    specific_refs = 0
    
    for field in checked_fields:
        field_str = str(field).lower()
        if any(indicator in field_str for indicator in specific_indicators):
            specific_refs += 1
    
    # Also check field_checked in deficiencies
    for deficiency in deficiencies:
        field_checked = deficiency.get("field_checked", "")
        if field_checked:
            total_refs += 1
            field_str = str(field_checked).lower()
            if any(indicator in field_str for indicator in specific_indicators):
                specific_refs += 1
    
    if total_refs == 0:
        return 0.3
    
    specificity_ratio = specific_refs / total_refs
    
    # Scale: high specificity (>80%) = 1.0, medium (50-80%) = 0.7, low (<50%) = 0.4
    if specificity_ratio >= 0.8:
        return 1.0
    elif specificity_ratio >= 0.5:
        return 0.7
    else:
        return 0.4


def score_evidence_type(deficiency_result: Dict[str, Any], config: Dict[str, Any]) -> float:
    """
    Classify evidence as missing data (lower confidence) vs wrong data (higher confidence).
    
    Missing data: empty arrays, null values, not found
    Wrong data: invalid values, incorrect format, mismatches
    """
    deficiencies = deficiency_result.get("deficiencies", [])
    reasoning = deficiency_result.get("reasoning", "")
    
    if not deficiencies:
        return 0.3
    
    keywords_missing = config["evidence_type_keywords"]["missing"]
    keywords_wrong = config["evidence_type_keywords"]["wrong"]
    scores_map = config["evidence_type_scores"]
    
    evidence_scores = []
    
    for deficiency in deficiencies:
        issue = str(deficiency.get("issue", "")).lower()
        evidence = str(deficiency.get("evidence", "")).lower()
        combined_text = issue + " " + evidence
        
        # Check for missing keywords
        is_missing = any(keyword in combined_text for keyword in keywords_missing)
        is_wrong = any(keyword in keywords_wrong for keyword in keywords_wrong)
        
        if is_missing and "[]" in combined_text:
            evidence_scores.append(scores_map["empty_array"])
        elif is_missing:
            evidence_scores.append(scores_map["missing_required"])
        elif is_wrong:
            evidence_scores.append(scores_map["wrong_value"])
        else:
            # Default: assume it's about missing if we can't classify
            evidence_scores.append(scores_map["unclear"])
    
    # Also check reasoning for overall context
    reasoning_lower = reasoning.lower()
    if any(keyword in reasoning_lower for keyword in keywords_missing):
        # Bias slightly toward missing
        evidence_scores.append(scores_map["missing_required"])
    
    return sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.5


def score_reasoning_quality(deficiency_result: Dict[str, Any]) -> float:
    """
    Score based on length and structure of reasoning.
    
    Longer, more detailed reasoning = higher confidence in the detection.
    """
    reasoning = deficiency_result.get("reasoning", "")
    
    if not reasoning:
        return 0.1
    
    length = len(reasoning)
    
    # Length-based scoring
    if length < 50:
        length_score = 0.3
    elif length < 150:
        length_score = 0.5
    elif length < 300:
        length_score = 0.7
    else:
        length_score = 1.0
    
    # Check for structured reasoning indicators
    structure_indicators = ["because", "since", "therefore", "however", "should", "must", "would"]
    structure_count = sum(1 for indicator in structure_indicators if indicator in reasoning.lower())
    structure_score = min(structure_count / 3, 1.0)  # Cap at 1.0 with 3+ indicators
    
    # Combine length and structure (70% length, 30% structure)
    return (length_score * 0.7) + (structure_score * 0.3)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load scoring configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


# Example usage
if __name__ == "__main__":
    # Load config
    config = load_config("scoring_config.json")
    
    # Example deficiency result
    example_result = {
        "condition_id": "Test Condition",
        "status": "deficient",
        "deficiencies": [
            {
                "requirement": "Field must be present",
                "issue": "Field is missing",
                "field_checked": "scheduleGPartII[].percentageOwned",
                "evidence": "Array is empty []"
            },
            {
                "requirement": "Must have value",
                "issue": "Value not found",
                "field_checked": "form1125E[].percentStockOwned",
                "evidence": "Field is null"
            }
        ],
        "reasoning": "This is a detailed explanation of why this condition is deficient. The document lacks critical information needed to verify compliance.",
        "checked_fields": ["scheduleGPartII", "form1125E", "year"]
    }
    
    result = calculate_detection_confidence(example_result, config)
    print(json.dumps(result, indent=2))

