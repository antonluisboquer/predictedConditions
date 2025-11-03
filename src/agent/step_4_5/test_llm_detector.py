"""
Quick test script for the LLM-based deficiency detector.
"""

import json
from llm_deficiency_detector import LLMDeficiencyDetector, format_results_summary
from dotenv import load_dotenv
import os

# Load .env from parent directory
load_dotenv("../.env")
load_dotenv()  # Also try current directory

# Load sample document from file
def load_sample_document():
    """Load sample document from JSON file."""
    sample_path = "../sample_doc_input.json"
    try:
        with open(sample_path, "r") as f:
            doc = json.load(f)
        print(f"✓ Loaded sample document from {sample_path}")
        if "classification" in doc:
            print(f"  Document type: {doc['classification']}")
        return doc
    except FileNotFoundError:
        print(f"✗ Could not find {sample_path}")
        print("  Using fallback FEMA purchase example...")
        # Fallback to hardcoded example
        return {
            "doc_presence": {
                "Borrower Attestation": True,
                "Appraisal Report": True
            },
            "transaction": {
                "purpose": {"value": "Purchase", "confidence": 0.99}
            },
            "property": {
                "fema_impacted": {"value": True, "confidence": 0.97}
            }
        }
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing JSON: {e}")
        return {}


def main():
    print("="*80)
    print("LLM DEFICIENCY DETECTOR TEST")
    print("="*80)
    print()
    
    # Load sample document
    sample_doc = load_sample_document()
    if not sample_doc:
        print("Failed to load sample document. Exiting.")
        return
    print()
    
    # Initialize detector
    print("Initializing detector...")
    detector = LLMDeficiencyDetector(
        conditions_csv_path="../merged_conditions_with_related_docs__FULL_filtered_simple.csv"
    )
    print(f"✓ Loaded {len(detector.conditions_df)} conditions\n")
    
    # Test 1: Filter conditions based on document classification AND fields
    print("TEST 1: Filtering conditions based on classification + extracted fields")
    print("-"*80)
    
    doc_classification = sample_doc.get('classification', 'Unknown')
    print(f"Document classification: '{doc_classification}'")
    
    # Extract field names from extracted_entities
    document_fields = []
    if "extracted_entities" in sample_doc:
        document_fields = list(sample_doc["extracted_entities"].keys())
        print(f"Document fields: {document_fields[:10]}{'...' if len(document_fields) > 10 else ''}")
    
    print(f"\nSearching for matches in 'Related documents' and 'Suggested Data Elements'...\n")
    
    # Find conditions based on classification AND fields
    matching_conditions = detector.filter_by_classification(doc_classification, document_fields)
    
    if len(matching_conditions) > 0:
        sample_conditions = matching_conditions['Title'].tolist()
        print(f"✓ Found {len(sample_conditions)} matching conditions")
        
        # Limit to first 5 for testing
        if len(sample_conditions) > 5:
            print(f"  Checking first 5 of {len(sample_conditions)} matches")
            sample_conditions = sample_conditions[:5]
        
        print(f"\nConditions to check:")
        for i, cond in enumerate(sample_conditions, 1):
            print(f"  {i}. {cond}")
    else:
        print(f"⚠ No conditions found (including 'All Docs' fallback)")
        print("  Using first 3 conditions for testing")
        sample_conditions = detector.conditions_df['Title'].head(3).tolist()
    
    print()
    result = detector.check_document(sample_doc, sample_conditions)
    
    if "error" in result:
        print(f"❌ ERROR: {result.get('error')}")
        if "exception" in result:
            print(f"   Exception details: {result['exception']}")
        if "raw_response" in result:
            print(f"   Raw response: {result['raw_response'][:200]}...")
        
        # Specific guidance for rate limits
        if "rate" in result.get('error', '').lower() or "429" in result.get('exception', ''):
            print()
            print("📊 RATE LIMIT DETECTED")
            print()
            print("This is Anthropic's 'acceleration limit' - you're scaling up too fast.")
            print()
            print("Solutions:")
            print("  1. Wait 2-3 minutes, then try again")
            print("  2. Run the warm-up script first: python warm_up_api.py")
            print("  3. Check fewer conditions (reduce to 2-3 instead of 5)")
            print("  4. Check your API tier: https://console.anthropic.com/")
            print()
        else:
            print()
            print("Troubleshooting tips:")
            print("1. Check if ANTHROPIC_API_KEY is set in ../.env")
            print("2. Verify your API key is valid at https://console.anthropic.com/")
            print("3. Check your internet connection")
            print("4. Ensure you have API credits remaining")
        return
    
    if "results" in result:
        print("\n📊 RESULTS:")
        for r in result["results"]:
            status_icon = "✅" if r["status"] == "satisfied" else "❌" if r["status"] == "deficient" else "⊘"
            print(f"\n{status_icon} {r['condition_id']}")
            print(f"   Status: {r['status'].upper()}")
            if r.get('related_documents'):
                print(f"   Related Documents: {r['related_documents']}")
            print(f"   Reasoning: {r['reasoning'][:100]}..." if len(r['reasoning']) > 100 else f"   Reasoning: {r['reasoning']}")
            
            if r.get('deficiencies'):
                print(f"   Deficiencies found:")
                for d in r['deficiencies']:
                    print(f"      • {d['requirement']}: {d['issue']}")
        
        # Print usage stats
        if "_metadata" in result:
            meta = result["_metadata"]
            print("\n" + "="*80)
            print("💰 API USAGE:")
            print(f"   Input tokens: {meta['input_tokens']:,}")
            print(f"   Output tokens: {meta['output_tokens']:,}")
            print(f"   Cache read: {meta['cache_read_tokens']:,}")
            print(f"   Cache creation: {meta['cache_creation_tokens']:,}")
            
            if meta['cache_read_tokens'] > 0:
                savings = (meta['cache_read_tokens'] * 0.9) / (meta['input_tokens'] if meta['input_tokens'] > 0 else 1)
                print(f"\n   ✅ Cache HIT! Estimated {savings:.0%} cost savings")
            elif meta['cache_creation_tokens'] > 0:
                print(f"\n   📝 Cache CREATED - next calls will be 90% cheaper!")
        
        # Save full results to file
        with open("test_results.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Full results saved to test_results.json")
        
    else:
        print(f"\n❌ ERROR: {result.get('error')}")
        if "raw_response" in result:
            print(f"Raw response: {result['raw_response'][:500]}...")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

