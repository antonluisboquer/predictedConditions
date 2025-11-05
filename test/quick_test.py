"""
Quick Test Script for Multi-Document Agent

Runs a simple test with cross-document resolution scenario.
"""

import sys
import json
from pathlib import Path

# Add src/agent to path
project_root = Path(__file__).parent.parent
agent_path = project_root / "src" / "agent"
sys.path.insert(0, str(agent_path))

from graph import run_pipeline_with_langgraph


# Test case: Tax Return + K-1 (cross-document resolution)
test_input = {
    "borrower_info": {
        "borrower_type": "Self-Employed",
        "business_name": "Sunrise Trading Corporation",
        "email": "miguel.santos@email.com",
        "first_name": "Miguel",
        "last_name": "Santos",
        "middle_name": "R.",
        "phone_number": "(0917) 555-3829",
        "ssn": "123-45-6789"
    },
    "loan_program": "Flex Supreme",
    "documents": [
        {
            "classification": "1120 Corporate Tax Return",
            "extracted_entities": {
                "business_name": "Sunrise Trading Corporation",
                "ein": "12-3456789",
                "gross_receipts": "1,250,000",
                "net_income": "185,000",
                "tax_year": "2023",
                "total_assets": "750,000",
                "total_liabilities": "420,000"
            }
        },
        {
            "classification": "Form 1120S Scorp",
            "extracted_entities": {
                "year": 2023,
                "SCorporation": {
                    "name": "Sunrise Trading Corporation",
                    "EIN": "123456789"
                },
                "businessAddress": {
                    "address1": "123 Main Street",
                    "city": "Los Angeles",
                    "state": "California",
                    "zipCode": "90001"
                },
                "typeOfBusiness": "Trading",
                "line4": 1250000,
                "line5": 850000,
                "line14": 185000,
                "line15": 165000,
                "form1125E": [
                    {
                        "officer": {
                            "firstName": "Miguel",
                            "middleName": "R",
                            "lastName": "Santos",
                            "last4SSN": "6789"
                        },
                        "percentStockOwned": 75,
                        "amountOfCompensation": 120000
                    }
                ],
                "scheduleGPartII": [
                    {
                        "individual": {
                            "firstName": "Miguel",
                            "middleName": "R",
                            "lastName": "Santos",
                            "last4SSN": "6789"
                        },
                        "percentageOwned": 75
                    }
                ],
                "scheduleLLine17ColumnD": 750000,
                "scheduleM1Line3B": 15000
            }
        }
    ]
}


if __name__ == "__main__":
    print("\n" + "="*80)
    print("QUICK TEST: Multi-Document Agent (Cross-Document Resolution)")
    print("="*80 + "\n")
    
    # Save test input
    input_path = project_root / "test" / "quick_test_input.json"
    with open(input_path, 'w') as f:
        json.dump(test_input, f, indent=2)
    print(f"✓ Saved test input: {input_path}\n")
    
    # Run pipeline
    output_path = project_root / "test" / "quick_test_output.json"
    
    try:
        result = run_pipeline_with_langgraph(
            input_file=str(input_path),
            output_file=str(output_path),
            top_n=5,
            verbose=True
        )
        
        # Show latency breakdown
        print("\n" + "="*80)
        print("PERFORMANCE METRICS")
        print("="*80)
        
        # Get step metrics from output structure
        step_metrics = result.get('step_metrics', {})
        
        # Convert latency from milliseconds to seconds
        step1_latency = step_metrics.get('step_1', {}).get('latency_ms', 0) / 1000
        step2_latency = step_metrics.get('step_2', {}).get('latency_ms', 0) / 1000
        step3_latency = step_metrics.get('step_3', {}).get('latency_ms', 0) / 1000
        step4_5_latency = step_metrics.get('step_4_5', {}).get('latency_ms', 0) / 1000
        step6_7_latency = step_metrics.get('step_6_7', {}).get('latency_ms', 0) / 1000
        
        # Get total latency from execution metadata
        total_latency = result.get('execution_metadata', {}).get('total_latency_seconds', 0)
        
        print(f"\nLatency per step:")
        print(f"  Step 1 (Get Compartments):    {step1_latency:>8.3f}s ({(step1_latency/total_latency*100) if total_latency > 0 else 0:>5.1f}%)")
        print(f"  Step 2 (Hard Filter):         {step2_latency:>8.3f}s ({(step2_latency/total_latency*100) if total_latency > 0 else 0:>5.1f}%)")
        print(f"  Step 3 (Rank Requirements):   {step3_latency:>8.3f}s ({(step3_latency/total_latency*100) if total_latency > 0 else 0:>5.1f}%)")
        print(f"  Step 4/5 (Detect Deficiency):  {step4_5_latency:>8.3f}s ({(step4_5_latency/total_latency*100) if total_latency > 0 else 0:>5.1f}%)")
        print(f"  Step 6/7 (Score Deficiency):   {step6_7_latency:>8.3f}s ({(step6_7_latency/total_latency*100) if total_latency > 0 else 0:>5.1f}%)")
        print(f"  {'─'*70}")
        print(f"  TOTAL:                         {total_latency:>8.3f}s")
        
        # Show token usage
        print(f"\nToken usage:")
        step3_tokens = step_metrics.get('step_3', {}).get('tokens', {})
        step4_5_tokens = step_metrics.get('step_4_5', {}).get('tokens', {})
        step6_7_tokens = step_metrics.get('step_6_7', {}).get('tokens', {})
        
        if step3_tokens:
            print(f"  Step 3: {step3_tokens.get('estimated_embedding_tokens', 0)} tokens (embeddings)")
        if step4_5_tokens:
            input_tok = step4_5_tokens.get('input_tokens', 0)
            output_tok = step4_5_tokens.get('output_tokens', 0)
            cache_read = step4_5_tokens.get('cache_read_tokens', 0)
            cache_create = step4_5_tokens.get('cache_creation_tokens', 0)
            print(f"  Step 4/5: {input_tok:,} input, {output_tok:,} output")
            if cache_read > 0:
                print(f"            {cache_read:,} cache read tokens (✓ cached prompt reused!)")
            if cache_create > 0:
                print(f"            {cache_create:,} cache creation tokens (first run)")
        if step6_7_tokens:
            input_tok = step6_7_tokens.get('input_tokens', 0)
            output_tok = step6_7_tokens.get('output_tokens', 0)
            print(f"  Step 6/7: {input_tok:,} input, {output_tok:,} output")
        
        # Show results summary
        print("\n" + "="*80)
        print("RESULTS SUMMARY")
        print("="*80)
        
        top_n = result.get('results', {}).get('top_n', [])
        print(f"\nTotal deficiencies found: {len(top_n)}")
        
        if top_n:
            print("\nTop Deficiencies:")
            for idx, deficiency in enumerate(top_n, 1):
                print(f"\n{idx}. {deficiency.get('condition_id', 'Unknown')[:70]}...")
                print(f"   Status: {deficiency.get('status', 'N/A')}")
                print(f"   Priority Score: {deficiency.get('priority_score', 0):.3f}")
                print(f"   Documents Checked: {deficiency.get('documents_checked', [])}")
                print(f"   Satisfied By: {deficiency.get('satisfied_by', 'null')}")
                print(f"   Actionable: {deficiency.get('actionable_instruction', 'N/A')}")
                
                # Show actionable documents (filtered)
                actionable_docs = deficiency.get('actionable_documents', '')
                if actionable_docs:
                    print(f"   Actionable Docs: {actionable_docs[:80]}...")
        
        # Check for embeddings (should be removed)
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)
        
        output_str = json.dumps(result)
        has_embeddings = '"embedding"' in output_str
        
        if has_embeddings:
            print("❌ WARNING: Output contains embeddings (should be removed)")
        else:
            print("✓ PASS: No embeddings in output")
        
        if top_n:
            first = top_n[0]
            checks = [
                ('actionable_documents', 'actionable_documents' in first),
                ('documents_checked', 'documents_checked' in first),
                ('satisfied_by', 'satisfied_by' in first)
            ]
            
            for field_name, present in checks:
                status = "✓ PASS" if present else "❌ FAIL"
                print(f"{status}: '{field_name}' field present")
        
        print(f"\n✓ Output saved to: {output_path}")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

