"""
Compare Rule-Based vs LLM-Based Deficiency Detection

This script demonstrates the difference between the two approaches
using the same sample document.
"""

import json
import time
import os
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv("../.env")
load_dotenv()  # Also try current directory

# Load sample document from file
sample_doc_path = "../sample_doc_input.json"
print(f"Loading sample document from: {sample_doc_path}")
try:
    with open(sample_doc_path, "r") as f:
        SAMPLE_DOC = json.load(f)
    print(f"✓ Loaded document: {SAMPLE_DOC.get('classification', 'Unknown type')}\n")
except FileNotFoundError:
    print(f"✗ Could not find {sample_doc_path}")
    print("Using fallback hardcoded example...\n")
    SAMPLE_DOC = {
        "doc_presence": {"Borrower Attestation": True, "Appraisal Report": True},
        "transaction": {"purpose": {"value": "Purchase", "confidence": 0.99}},
        "property": {"fema_impacted": {"value": True, "confidence": 0.97}}
    }
except json.JSONDecodeError as e:
    print(f"✗ Error parsing JSON: {e}")
    exit(1)

# Import rule-based approach (with its hardcoded examples)
try:
    from detect_deficiencies import DOC_JSON, CONDITION_TEMPLATES, evaluate_condition
    print("✓ Rule-based engine loaded (using its hardcoded examples for demo)\n")
except ImportError:
    print("✗ Could not import detect_deficiencies.py")
    CONDITION_TEMPLATES = []
    DOC_JSON = {}

print("="*80)
print("COMPARING RULE-BASED VS LLM-BASED DEFICIENCY DETECTION")
print("="*80)
print()

# ============================================================================
# APPROACH 1: Rule-Based (Original - detect_deficiencies.py)
# ============================================================================

print("APPROACH 1: RULE-BASED ENGINE")
print("-"*80)
print()

print("Conditions available:")
for template in CONDITION_TEMPLATES:
    print(f"  - {template['condition_id']}")
print()

print("Running rule-based evaluation...")
start_time = time.time()

rule_results = []
for condition in CONDITION_TEMPLATES:
    result = evaluate_condition(DOC_JSON, condition)
    rule_results.append(result)

rule_time = time.time() - start_time

print(f"✓ Completed in {rule_time*1000:.2f}ms")
print()

print("RESULTS:")
for result in rule_results:
    status_icon = "✅" if result["status"] == "satisfied" else "❌" if result["status"] == "deficient" else "⊘"
    print(f"{status_icon} {result['condition_id']}: {result['status'].upper()}")
    if result['failures']:
        print(f"   Failures: {len(result['failures'])}")
        for failure in result['failures'][:2]:  # Show first 2
            print(f"   • {failure['field']}: expected {failure['expected']}, got {failure['actual']}")

print()
print(f"Summary: {sum(1 for r in rule_results if r['status'] == 'satisfied')} satisfied, "
      f"{sum(1 for r in rule_results if r['status'] == 'deficient')} deficient")
print()

# ============================================================================
# APPROACH 2: LLM-Based (New)
# ============================================================================

print()
print("="*80)
print("APPROACH 2: LLM-BASED VALIDATION")
print("-"*80)
print()

try:
    from llm_deficiency_detector import LLMDeficiencyDetector
    
    print("Initializing LLM detector...")
    print("(Note: This requires ANTHROPIC_API_KEY in .env)")
    print()
    
    detector = LLMDeficiencyDetector(
        conditions_csv_path="../merged_conditions_with_related_docs__FULL_filtered_simple.csv"
    )
    
    print(f"✓ Loaded {len(detector.conditions_df)} conditions from CSV")
    print()
    
    # Filter conditions based on document classification AND fields
    doc_classification = SAMPLE_DOC.get('classification', 'Unknown')
    print(f"Document classification: '{doc_classification}'")
    
    # Extract fields from document
    document_fields = []
    if "extracted_entities" in SAMPLE_DOC:
        document_fields = list(SAMPLE_DOC["extracted_entities"].keys())
        print(f"Document fields: {len(document_fields)} fields")
    
    print(f"Filtering conditions...\n")
    
    matching_conditions = detector.filter_by_classification(doc_classification, document_fields)
    
    if len(matching_conditions) > 0:
        conditions_to_check = matching_conditions['Title'].head(3).tolist()
        print(f"✓ Found {len(matching_conditions)} matching conditions")
        print(f"Checking first 3: {conditions_to_check}\n")
    else:
        print(f"⚠ No matches found (including 'All Docs' fallback)")
        conditions_to_check = detector.conditions_df['Title'].head(3).tolist()
        print(f"Using first 3 conditions for testing: {conditions_to_check}\n")
    
    print("Calling Claude API with prompt caching...")
    print()
    
    start_time = time.time()
    llm_result = detector.check_document(SAMPLE_DOC, conditions_to_check)
    llm_time = time.time() - start_time
    
    print(f"✓ Completed in {llm_time*1000:.0f}ms")
    print()
    
    if "results" in llm_result:
        print("RESULTS:")
        for result in llm_result["results"]:
            status_icon = "✅" if result["status"] == "satisfied" else "❌" if result["status"] == "deficient" else "⊘"
            print(f"{status_icon} {result['condition_id']}: {result['status'].upper()}")
            if result.get('related_documents'):
                print(f"   Related Documents: {result['related_documents']}")
            print(f"   Reasoning: {result['reasoning'][:150]}...")
            
            if result.get('deficiencies'):
                print(f"   Deficiencies: {len(result['deficiencies'])}")
                for deficiency in result['deficiencies'][:2]:  # Show first 2
                    print(f"   • {deficiency['requirement']}")
                    print(f"     Issue: {deficiency['issue']}")
        
        print()
        
        # Show token usage
        if "_metadata" in llm_result:
            meta = llm_result["_metadata"]
            print("API Usage:")
            print(f"  Input tokens: {meta['input_tokens']:,}")
            print(f"  Output tokens: {meta['output_tokens']:,}")
            print(f"  Cache read: {meta['cache_read_tokens']:,}")
            print(f"  Cache creation: {meta['cache_creation_tokens']:,}")
            
            if meta['cache_read_tokens'] > 0:
                print(f"  ✅ Cache HIT - 90% cost savings!")
            elif meta['cache_creation_tokens'] > 0:
                print(f"  📝 Cache CREATED - next calls will save 90%")
    else:
        print(f"❌ Error: {llm_result.get('error')}")

except ImportError:
    print("❌ LLM detector not available (missing dependencies)")
    print("   Run: pip install anthropic")
except Exception as e:
    print(f"❌ Error: {e}")
    print("   Make sure ANTHROPIC_API_KEY is set in .env file")

print()
print("="*80)
print("COMPARISON SUMMARY")
print("="*80)
print()

comparison_table = f"""
{'Metric':<30} {'Rule-Based':<20} {'LLM-Based':<20}
{'-'*70}
{'Setup Time':<30} {'Weeks':<20} {'Minutes':<20}
{'Speed':<30} {f'{rule_time*1000:.2f}ms':<20} {f'{llm_time*1000:.0f}ms' if 'llm_time' in locals() else 'N/A':<20}
{'Conditions Available':<30} {'2 (hardcoded)':<20} {'700+ (from CSV)':<20}
{'Natural Language Support':<30} {'No (rules only)':<20} {'Yes':<20}
{'Handles Ambiguity':<30} {'No':<20} {'Yes':<20}
{'Cost per Document':<30} {'Free':<20} {'~$0.05 (cached)':<20}
{'Explainability':<30} {'Limited':<20} {'Full reasoning':<20}
{'Maintenance':<30} {'Manual':<20} {'Automatic':<20}
"""

print(comparison_table)

print()
print("RECOMMENDATION:")
print("  • Use Rule-Based for: Simple, well-defined checks with known field mappings")
print("  • Use LLM-Based for: Complex natural language conditions from your CSV")
print("  • Hybrid: Use rules for 20% clear-cut cases, LLM for 80% complex cases")
print()



