"""
Test script for Step 6/7 Deficiency Scorer

Tests the hybrid scoring system with detection results from Step 4/5.
"""

import json
import os
import sys
from dotenv import load_dotenv

from deficiency_scorer import DeficiencyScorer, format_results_summary


def test_scorer():
    """Test the deficiency scorer with step_4_5 test results."""
    
    print("=" * 80)
    print("STEP 6/7: DEFICIENCY SCORING TEST")
    print("=" * 80)
    print()
    
    # Load environment variables
    load_dotenv("../.env")
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found in environment")
        print("\nPlease set your API key:")
        print("1. Create a .env file in the project root")
        print("2. Add: ANTHROPIC_API_KEY=your-key-here")
        print("\nOr export it in your shell:")
        print("export ANTHROPIC_API_KEY=your-key-here")
        return
    
    print(f"✓ API key found: {api_key[:20]}...")
    print()
    
    # Initialize scorer
    try:
        scorer = DeficiencyScorer(
            config_path="scoring_config.json"
        )
    except Exception as e:
        print(f"❌ Error initializing scorer: {e}")
        return
    
    # Test input file
    test_input = "../step_4_5/test_results.json"
    
    if not os.path.exists(test_input):
        print(f"❌ ERROR: Test input file not found: {test_input}")
        print("\nPlease run step_4_5/test_llm_detector.py first to generate test results")
        return
    
    print(f"✓ Loading detection results from: {test_input}")
    print()
    
    # Load and preview input
    with open(test_input, 'r') as f:
        detection_data = json.load(f)
    
    all_results = detection_data.get("results", [])
    deficient_count = sum(1 for r in all_results if r.get("status") == "deficient")
    
    print(f"Input Summary:")
    print(f"  Total conditions checked: {len(all_results)}")
    print(f"  Deficient conditions: {deficient_count}")
    print()
    
    if deficient_count == 0:
        print("⚠ No deficient conditions found in test results")
        print("Run step_4_5/test_llm_detector.py to generate test data with deficiencies")
        return
    
    # Test with different top_n values
    test_cases = [
        {"top_n": 3, "description": "Top 3 deficiencies"},
        {"top_n": deficient_count, "description": f"All {deficient_count} deficiencies"}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print("\n" + "=" * 80)
        print(f"TEST CASE {i}: {test_case['description']}")
        print("=" * 80)
        
        try:
            results = scorer.score_deficiencies(
                detection_results=test_input,
                top_n=test_case["top_n"],
                verbose=True
            )
            
            # Print formatted summary
            print("\n" + format_results_summary(results))
            
            # Save results
            output_path = f"test_scored_results_top{test_case['top_n']}.json"
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"✓ Results saved to: {output_path}")
            
            # Print detailed breakdown for first result
            if results["top_n"]:
                print("\n" + "-" * 80)
                print("DETAILED BREAKDOWN (Top Priority Deficiency)")
                print("-" * 80)
                
                top_result = results["top_n"][0]
                
                print(f"\nCondition: {top_result['condition_id']}")
                print(f"\nPriority Score: {top_result['priority_score']:.3f}")
                print(f"  Dimensions:")
                for dim, value in top_result["priority_dimensions"].items():
                    if dim != "explanation":
                        print(f"    - {dim.capitalize()}: {value:.3f}")
                print(f"  Explanation: {top_result['priority_dimensions'].get('explanation', '')}")
                
                print(f"\nDetection Confidence: {top_result['detection_confidence']:.3f}")
                print(f"  Breakdown:")
                for metric, value in top_result["confidence_breakdown"].items():
                    print(f"    - {metric}: {value:.3f}")
                
                print(f"\nOriginal Deficiencies:")
                orig = top_result["original_deficiency"]
                for j, deficiency in enumerate(orig.get("deficiencies", []), 1):
                    print(f"\n  {j}. Requirement: {deficiency.get('requirement', '')}")
                    print(f"     Issue: {deficiency.get('issue', '')}")
                    print(f"     Field: {deficiency.get('field_checked', '')}")
                    print(f"     Evidence: {deficiency.get('evidence', '')[:100]}...")
            
        except Exception as e:
            print(f"\n❌ ERROR during scoring: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


def test_confidence_calculator():
    """Test just the confidence calculator component."""
    print("\n" + "=" * 80)
    print("TESTING: Confidence Calculator")
    print("=" * 80 + "\n")
    
    from confidence_calculator import calculate_detection_confidence, load_config
    
    config = load_config("scoring_config.json")
    
    # Test with sample deficiency
    sample = {
        "condition_id": "Test: Multiple deficiencies with complete evidence",
        "status": "deficient",
        "deficiencies": [
            {
                "requirement": "Tax return must be signed",
                "issue": "Signature missing from return",
                "field_checked": "form1125E[].signature",
                "evidence": "Array is empty [], no signature data found"
            },
            {
                "requirement": "Return must be dated",
                "issue": "Date field is missing",
                "field_checked": "form1125E[].date",
                "evidence": "Date field not present in document"
            }
        ],
        "reasoning": "The tax return lacks both signature and date information which are required for loan approval. Form 1125E should contain this data but the array is empty.",
        "checked_fields": ["form1125E", "scheduleGPartII", "year", "corporation.EIN"]
    }
    
    result = calculate_detection_confidence(sample, config)
    
    print(f"Sample Condition: {sample['condition_id']}")
    print(f"\nDetection Confidence: {result['overall']:.3f}")
    print(f"\nBreakdown:")
    for metric, value in result['breakdown'].items():
        print(f"  - {metric}: {value:.3f}")


if __name__ == "__main__":
    # Check command line args
    if len(sys.argv) > 1 and sys.argv[1] == "--confidence-only":
        test_confidence_calculator()
    else:
        test_scorer()

