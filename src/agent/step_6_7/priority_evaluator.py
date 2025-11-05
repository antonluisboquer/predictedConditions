"""
LLM-Based Priority Evaluator

Uses Claude to assess priority dimensions:
- Severity: How critical to loan approval?
- Impact: Consequences if not resolved?
- Urgency: Timeline sensitivity?
- Complexity: Remediation difficulty?
"""

import json
import os
from typing import Dict, Any, Optional
from anthropic import Anthropic


def evaluate_priority(
    deficiency_result: Dict[str, Any],
    detection_confidence: float,
    api_key: Optional[str],
    config: Dict[str, Any],
    model: str = "claude-haiku-4-5-20251001"  # Optimized: Haiku is 3-5x faster than Sonnet
) -> Dict[str, Any]:
    """
    Evaluate priority of a deficiency using Claude.
    
    Args:
        deficiency_result: Single result from step_4_5 detection
        detection_confidence: Calculated detection confidence (0-1)
        api_key: Anthropic API key (or None to use env var)
        config: Configuration dict with weights
        model: Claude model to use
        
    Returns:
        Dict with priority dimensions, overall score, and explanation
    """
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
    
    client = Anthropic(api_key=api_key)
    
    # Build prompt
    prompt = build_priority_prompt(deficiency_result, detection_confidence)
    
    # Call Claude
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        response_text = response.content[0].text
        
        # Parse JSON from response
        priority_dims = parse_priority_response(response_text)
        
        # Calculate overall priority score
        overall = calculate_overall_priority(priority_dims, config["priority_score_weights"])
        
        return {
            "severity": priority_dims["severity"],
            "impact": priority_dims["impact"],
            "urgency": priority_dims["urgency"],
            "complexity": priority_dims["complexity"],
            "explanation": priority_dims.get("explanation", ""),
            "overall_priority": round(overall, 3)
        }
        
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        # Return default medium priority on error
        return {
            "severity": 0.5,
            "impact": 0.5,
            "urgency": 0.5,
            "complexity": 0.5,
            "explanation": f"Error evaluating priority: {str(e)}",
            "overall_priority": 0.5
        }


def build_priority_prompt(deficiency_result: Dict[str, Any], detection_confidence: float) -> str:
    """
    Build prompt for Claude to evaluate priority.
    """
    condition_id = deficiency_result.get("condition_id", "Unknown")
    status = deficiency_result.get("status", "deficient")
    related_docs = deficiency_result.get("related_documents", "")
    reasoning = deficiency_result.get("reasoning", "")
    deficiencies = deficiency_result.get("deficiencies", [])
    
    # Format deficiencies
    deficiency_text = ""
    for i, deficiency in enumerate(deficiencies, 1):
        req = deficiency.get("requirement", "")
        issue = deficiency.get("issue", "")
        field = deficiency.get("field_checked", "")
        evidence = deficiency.get("evidence", "")
        
        deficiency_text += f"\n{i}. Requirement: {req}\n"
        deficiency_text += f"   Issue: {issue}\n"
        deficiency_text += f"   Field: {field}\n"
        deficiency_text += f"   Evidence: {evidence}\n"
    
    prompt = f"""Evaluate this loan underwriting deficiency for priority scoring.

DEFICIENCY INFORMATION:
Condition: {condition_id}
Status: {status}
Related Documents: {related_docs}

Detection Confidence: {detection_confidence:.2f} (0=uncertain, 1=certain)
This indicates how confident the detection system is that this is truly deficient.

DEFICIENCIES FOUND:{deficiency_text}

REASONING:
{reasoning}

SCORING INSTRUCTIONS:
Rate each dimension from 0.0 to 1.0 based on the loan underwriting context:

1. SEVERITY: How critical is this to loan approval?
   - 0.9-1.0: Deal cannot close, regulatory violation, legal requirement
   - 0.6-0.8: Significant risk, underwriting concern, delays likely
   - 0.3-0.5: Minor issue, can be resolved with documentation
   - 0.0-0.2: Trivial, best practice only, optional

2. IMPACT: What are the consequences if NOT resolved?
   - 0.9-1.0: Legal/regulatory risk, cannot fund loan, investor rejection
   - 0.6-0.8: Financial risk, requires additional verification, guideline violation
   - 0.3-0.5: Process delay, manual review needed
   - 0.0-0.2: Minor inconvenience, documentation preference

3. URGENCY: How time-sensitive is this?
   - 0.9-1.0: Immediate blocker, must resolve before proceeding
   - 0.6-0.8: Needed before closing, prior to funding
   - 0.3-0.5: Post-closing acceptable with conditions
   - 0.0-0.2: Can be deferred, no immediate timeline

4. COMPLEXITY: How difficult is remediation?
   - 0.9-1.0: Very difficult, requires multiple parties, lengthy process
   - 0.6-0.8: Moderate effort, coordination needed, multiple documents
   - 0.3-0.5: Straightforward, clear process, single request
   - 0.0-0.2: Easy fix, quick request, readily available

IMPORTANT CONTEXT:
- Missing signatures on tax returns = HIGH severity (required for loan approval)
- Ownership verification = HIGH-MEDIUM severity (guideline requirement)
- Missing optional documentation = LOW severity
- Empty arrays/missing data = Consider if it's required or optional

Return ONLY valid JSON in this exact format:
{{
  "severity": 0.0-1.0,
  "impact": 0.0-1.0,
  "urgency": 0.0-1.0,
  "complexity": 0.0-1.0,
  "explanation": "1-2 sentence explanation of the priority assessment"
}}

Do NOT include markdown formatting or any text outside the JSON."""
    
    return prompt


def parse_priority_response(response_text: str) -> Dict[str, Any]:
    """
    Parse Claude's JSON response into priority dimensions.
    """
    # Try to extract JSON if wrapped in markdown
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    
    try:
        data = json.loads(response_text)
        
        # Validate required fields
        required_fields = ["severity", "impact", "urgency", "complexity"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
            
            # Ensure values are in range 0-1
            if not (0 <= data[field] <= 1):
                print(f"Warning: {field} value {data[field]} out of range, clamping to [0,1]")
                data[field] = max(0, min(1, data[field]))
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response text: {response_text}")
        # Return default medium values
        return {
            "severity": 0.5,
            "impact": 0.5,
            "urgency": 0.5,
            "complexity": 0.5,
            "explanation": "Error parsing response"
        }


def calculate_overall_priority(dimensions: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Calculate weighted overall priority score.
    
    Default weights: severity=0.4, impact=0.3, urgency=0.2, complexity=0.1
    Note: Lower complexity is better, so we invert it (1 - complexity)
    """
    overall = (
        dimensions["severity"] * weights["severity"] +
        dimensions["impact"] * weights["impact"] +
        dimensions["urgency"] * weights["urgency"] +
        (1 - dimensions["complexity"]) * weights["complexity"]  # Inverted: easier = better
    )
    
    return overall


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Load config
    with open("scoring_config.json", 'r') as f:
        config = json.load(f)
    
    # Example deficiency result
    example_result = {
        "condition_id": "Income: Business tax returns to be signed and dated by all borrowers",
        "status": "deficient",
        "related_documents": "1120 Corporate Tax Return, Form 1120S Scorp, Form 1065",
        "deficiencies": [
            {
                "requirement": "Business tax return must be signed and dated by all borrowers",
                "issue": "Tax return lacks signature and date information from officers/borrowers",
                "field_checked": "form1125E (officer signatures and compensation)",
                "evidence": "form1125E array is empty [], which should contain officer information including signatures"
            }
        ],
        "reasoning": "For a 1120 Corporate Tax Return, form1125E typically contains signature information. The empty array indicates this section is missing.",
        "checked_fields": ["form1125E", "scheduleGPartII", "year"]
    }
    
    result = evaluate_priority(
        example_result,
        detection_confidence=0.65,
        api_key=None,
        config=config
    )
    
    print(json.dumps(result, indent=2))

