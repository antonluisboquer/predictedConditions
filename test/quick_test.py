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

