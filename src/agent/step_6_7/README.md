# Step 6/7: Deficiency Scoring & Ranking

## Overview

This directory contains the **post-processing scoring system** that ranks deficiencies detected in Step 4/5.

**Purpose**: Take the raw deficiencies from detection and score them by severity, impact, urgency, and complexity to prioritize the top N for human review.

---

## Workflow

```
Step 4/5 Output          Step 6/7 Hybrid Processing          Step 6/7 Output
┌─────────────────┐      ┌──────────────────────────┐       ┌─────────────────┐
│ All Deficiencies│  →   │ 1. Empirical Confidence  │   →   │ Top N Ranked    │
│ (detected)      │      │    - Evidence quality     │       │ Deficiencies    │
│                 │      │    - Deficiency count     │       │                 │
│ - Condition A   │      │    - Field specificity    │       │ 1. Condition C  │
│ - Condition B   │      │    - Evidence type        │       │    Priority: 0.95│
│ - Condition C   │      │                          │       │    Confidence: 0.65│
│ - ...           │      │ 2. LLM Priority Score    │       │                 │
└─────────────────┘      │    • Severity            │       │ 2. Condition A  │
                         │    • Impact              │       │    Priority: 0.87│
                         │    • Urgency             │       │    Confidence: 0.82│
                         │    • Complexity          │       │                 │
                         │                          │       │ 3. Condition B  │
                         │ 3. Rank by Priority      │       │    Priority: 0.73│
                         └──────────────────────────┘       │    Confidence: 0.55│
                                                             └─────────────────┘
```

---

## Input Format

Expects JSON output from Step 4/5 deficiency detection:

```json
{
  "results": [
    {
      "condition_id": "Tax Return Completeness",
      "status": "deficient",
      "deficiencies": [
        {
          "requirement": "Schedule K-1 must be included",
          "issue": "Schedule K-1 not found in document",
          "field_checked": "schedules.k1",
          "evidence": "Field is null"
        }
      ],
      "reasoning": "Document is missing required Schedule K-1",
      "checked_fields": ["schedules.k1"]
    }
  ]
}
```

---

## Quick Start

### 1. Install Dependencies

Already installed from Step 4/5 (anthropic, pandas, python-dotenv).

### 2. Run Test

```bash
cd step_6_7
python test_scorer.py
```

This will:
- Load deficiencies from `../step_4_5/test_results.json`
- Calculate detection confidence (empirical)
- Evaluate priority using Claude (LLM)
- Rank and display top N deficiencies

### 3. Use in Your Code

```python
from step_6_7.deficiency_scorer import DeficiencyScorer

# Initialize
scorer = DeficiencyScorer(config_path="step_6_7/scoring_config.json")

# Score deficiencies
results = scorer.score_deficiencies(
    detection_results="../step_4_5/test_results.json",
    top_n=10,
    verbose=True
)

# Access scored results
for deficiency in results["top_n"]:
    print(f"{deficiency['condition_id']}")
    print(f"  Priority: {deficiency['priority_score']:.3f}")
    print(f"  Confidence: {deficiency['detection_confidence']:.3f}")
```

---

## Two-Score System

### Detection Confidence (Empirical)
Calculated from evidence quality metrics:
- **Evidence completeness**: Are all required fields present?
- **Deficiency count**: More deficiencies = higher confidence
- **Field specificity**: Specific paths vs vague references
- **Evidence type**: Wrong data (high) vs missing data (lower)
- **Reasoning quality**: Length and structure of reasoning

### Priority Score (LLM-Based)
Used for ranking, evaluated by Claude:
- **Severity**: How critical to loan approval?
- **Impact**: Consequences if not resolved?
- **Urgency**: Timeline sensitivity?
- **Complexity**: Remediation difficulty? (inverted in final score)

**Key Design**: Detection confidence tells us "how sure are we this is deficient?" while priority score tells us "how important is this deficiency?" We rank by priority, not confidence.

---

## Scoring Dimensions

Each deficiency will be scored on multiple dimensions:

### 1. **Severity** (0.0-1.0)
- How critical is this deficiency to the loan decision?
- Examples:
  - **High (0.9+)**: Missing signatures, invalid dates, regulatory violations
  - **Medium (0.5-0.8)**: Incomplete documentation, minor discrepancies
  - **Low (<0.5)**: Formatting issues, non-critical missing data

### 2. **Impact** (0.0-1.0)
- What are the consequences if not resolved?
- Examples:
  - **High (0.9+)**: Deal cannot close, legal risk
  - **Medium (0.5-0.8)**: Delays, additional verification needed
  - **Low (<0.5)**: Convenience, best practices

### 3. **Urgency** (0.0-1.0)
- How quickly must this be resolved?
- Examples:
  - **High (0.9+)**: Immediate blocker
  - **Medium (0.5-0.8)**: Needed before closing
  - **Low (<0.5)**: Post-closing acceptable

### 4. **Complexity** (0.0-1.0)
- How difficult is remediation?
- Examples:
  - **Low (0.0-0.3)**: Easy fix, quick request
  - **Medium (0.4-0.7)**: Requires coordination
  - **High (0.8+)**: Complex, time-consuming

---

## Output Format

```json
{
  "scored_deficiencies": [
    {
      "condition_id": "Income: Business tax returns to be signed and dated",
      "status": "deficient",
      "detection_confidence": 0.687,
      "confidence_breakdown": {
        "evidence_completeness": 1.0,
        "deficiency_count_score": 0.8,
        "field_specificity": 0.85,
        "evidence_type": 0.5,
        "reasoning_quality": 0.714
      },
      "priority_score": 0.892,
      "priority_dimensions": {
        "severity": 0.95,
        "impact": 0.90,
        "urgency": 0.90,
        "complexity": 0.25,
        "explanation": "Missing signatures on tax returns is a critical regulatory requirement that blocks loan approval"
      },
      "related_documents": "1120 Corporate Tax Return, Form 1120S Scorp, Form 1065",
      "original_deficiency": { /* full deficiency from Step 4/5 */ }
    }
  ],
  "top_n": [
    /* Top N deficiencies sorted by priority_score */
  ],
  "summary": {
    "total_deficiencies_evaluated": 4,
    "average_detection_confidence": 0.674,
    "average_priority_score": 0.856,
    "high_priority_count": 3,
    "medium_priority_count": 1,
    "low_priority_count": 0
  }
}
```

---

## Implementation Status

### Phase 1: Basic Scoring ✅ COMPLETE
- ✅ Load deficiency results from Step 4/5
- ✅ Implement hybrid scoring system (empirical + LLM)
- ✅ Generate scores for detection confidence
- ✅ Generate scores for priority dimensions
- ✅ Calculate overall priority score (weighted combination)
- ✅ Rank deficiencies by priority score

### Phase 2: Enhanced Features 🚧 IN PROGRESS
- ✅ Map to related documents (already in Step 4/5 output)
- ✅ Support custom scoring weights (via JSON config)
- ⏳ Add remediation suggestions (in LLM explanation, can be enhanced)
- ⏳ Generate resolution time estimates
- ⏳ Add business rule overrides

### Phase 3: Optimization ⏳ PLANNED
- ⏳ Batch scoring for efficiency (currently sequential)
- ⏳ Cache common scoring patterns
- ⏳ A/B test different scoring approaches
- ⏳ Tune weights based on feedback

---

## Scoring Algorithms

### Detection Confidence (Empirical)
```python
detection_confidence = weighted_average(
    evidence_completeness: 0.30,    # All fields present?
    deficiency_count: 0.20,         # More deficiencies = higher confidence
    field_specificity: 0.20,        # Specific paths vs vague
    evidence_type: 0.20,            # Wrong (0.9) vs missing (0.5) data
    reasoning_quality: 0.10         # Length and structure
)
```

### Priority Score (LLM + Weighted)
```python
priority_score = weighted_average(
    severity: 0.40,                 # Most important
    impact: 0.30,                   # Second most important
    urgency: 0.20,                  # Time sensitivity
    (1 - complexity): 0.10          # Ease of fix (inverted)
)
```

**Note**: All weights configurable in `scoring_config.json`

---

## Files

### Core Implementation
- **`deficiency_scorer.py`** - Main DeficiencyScorer class, orchestrates scoring
- **`confidence_calculator.py`** - Empirical confidence calculation
- **`priority_evaluator.py`** - LLM-based priority evaluation with prompts
- **`scoring_config.json`** - Configurable weights and thresholds

### Testing
- **`test_scorer.py`** - Test script with step_4_5 results
- **`test_scored_results_top*.json`** - Output from test runs (gitignored)

### Documentation
- **`README.md`** - This file

---

## Design Principles

1. **Transparent**: Scores should be explainable
2. **Consistent**: Same deficiency should get similar scores
3. **Tunable**: Weights and rules should be adjustable
4. **Efficient**: Should handle hundreds of deficiencies quickly
5. **Actionable**: Should provide clear next steps

---

## Status

✅ **IMPLEMENTED** - Hybrid scoring system with empirical confidence + LLM priority

See usage instructions below.

