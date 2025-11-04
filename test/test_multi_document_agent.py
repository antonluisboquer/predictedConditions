"""
Test Script for Multi-Document Agent Pipeline

Tests various scenarios:
1. Single document (backward compatibility)
2. Multiple documents of same type
3. Cross-document deficiency resolution
4. Embedding removal verification
5. Actionable documents filtering
"""

import sys
import json
from pathlib import Path

# Add src/agent to path
project_root = Path(__file__).parent.parent
agent_path = project_root / "src" / "agent"
sys.path.insert(0, str(agent_path))

from graph import run_pipeline_with_langgraph


# ============================================================================
# TEST CASE 1: Single Document (Backward Compatibility - Old Format)
# ============================================================================

test_case_1_old_format = {
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
    "classification": "1120 Corporate Tax Return",
    "extracted_entities": {
        "business_name": "Sunrise Trading Corporation",
        "ein": "12-3456789",
        "gross_receipts": "1,250,000",
        "net_income": "185,000",
        "tax_year": "2023",
        "total_assets": "750,000",
        "total_liabilities": "420,000"
    },
    "loan_program": "Flex Supreme"
}


# ============================================================================
# TEST CASE 2: Single Document (New Format)
# ============================================================================

test_case_2_single_doc_new_format = {
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
        }
    ]
}


# ============================================================================
# TEST CASE 3: Multiple Documents of Same Type (Two Tax Returns)
# ============================================================================

test_case_3_multiple_same_type = {
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
            "classification": "1120 Corporate Tax Return",
            "extracted_entities": {
                "business_name": "Sunrise Trading Corporation",
                "ein": "12-3456789",
                "gross_receipts": "1,100,000",
                "net_income": "165,000",
                "tax_year": "2022",
                "total_assets": "680,000",
                "total_liabilities": "390,000"
            }
        }
    ]
}


# ============================================================================
# TEST CASE 4: Cross-Document Deficiency Resolution
# 1120 Corporate + 1120S Scorp (1120S provides ownership info missing from 1120)
# ============================================================================

test_case_4_cross_document = {
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
                "line14": 185000
            }
        }
    ]
}


# ============================================================================
# TEST CASE 5: Multiple Diverse Documents
# Tax Return + K-1 + Bank Statement + CPA Letter
# ============================================================================

test_case_5_diverse_documents = {
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
                "total_liabilities": "420,000",
                "signed": "yes",
                "date_signed": "2024-04-15"
            }
        },
        {
            "classification": "Schedule K-1 Form 1120S",
            "extracted_entities": {
                "shareholder_name": "Miguel R. Santos",
                "shareholder_ssn": "123-45-6789",
                "ownership_percentage": "75%",
                "business_name": "Sunrise Trading Corporation",
                "ein": "12-3456789",
                "tax_year": "2023",
                "ordinary_income": "185,000"
            }
        },
        {
            "classification": "Business Bank Statement",
            "extracted_entities": {
                "account_holder": "Sunrise Trading Corporation",
                "account_number": "****5678",
                "statement_date": "2024-10-31",
                "beginning_balance": "145,000",
                "ending_balance": "178,500",
                "average_balance": "162,000"
            }
        },
        {
            "classification": "CPA Letter for Self-Employment",
            "extracted_entities": {
                "borrower_name": "Miguel R. Santos",
                "business_name": "Sunrise Trading Corporation",
                "cpa_name": "Jane Anderson, CPA",
                "cpa_license": "CA-123456",
                "letter_date": "2024-11-01",
                "confirmation_text": "This letter confirms that Miguel R. Santos is self-employed as owner of Sunrise Trading Corporation with 75% ownership stake since 2018.",
                "ownership_percentage": "75%"
            }
        }
    ]
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def save_test_input(test_data: dict, filename: str):
    """Save test input to file."""
    filepath = project_root / "test" / filename
    with open(filepath, 'w') as f:
        json.dump(test_data, f, indent=2)
    print(f"✓ Saved test input: {filepath}")
    return str(filepath)


def verify_output(output_data: dict, test_name: str):
    """Verify output meets expectations."""
    print(f"\n{'='*80}")
    print(f"VERIFYING OUTPUT: {test_name}")
    print(f"{'='*80}")
    
    # Check for embeddings in output (should be removed)
    embeddings_found = check_for_embeddings(output_data)
    if embeddings_found:
        print("❌ FAILED: Embeddings found in output")
    else:
        print("✓ PASSED: No embeddings in output")
    
    # Check for actionable_documents field
    results = output_data.get('results', {}).get('top_n', [])
    if results:
        first_result = results[0]
        
        # Check for new fields
        has_actionable_docs = 'actionable_documents' in first_result
        has_documents_checked = 'documents_checked' in first_result
        has_satisfied_by = 'satisfied_by' in first_result
        
        print(f"✓ PASSED: actionable_documents field present" if has_actionable_docs else "❌ FAILED: actionable_documents field missing")
        print(f"✓ PASSED: documents_checked field present" if has_documents_checked else "❌ FAILED: documents_checked field missing")
        print(f"✓ PASSED: satisfied_by field present" if has_satisfied_by else "❌ FAILED: satisfied_by field missing")
        
        # Verify actionable_documents is subset of related_documents
        if has_actionable_docs:
            related_docs = set(first_result.get('related_documents', '').split(', '))
            actionable_docs = set(first_result.get('actionable_documents', '').split(', '))
            
            if actionable_docs.issubset(related_docs) or actionable_docs == related_docs:
                print("✓ PASSED: actionable_documents is subset of related_documents")
            else:
                print("❌ FAILED: actionable_documents contains items not in related_documents")
        
        # Show first result
        print(f"\nFirst deficiency found:")
        print(f"  Condition: {first_result.get('condition_id', 'N/A')[:60]}...")
        print(f"  Status: {first_result.get('status', 'N/A')}")
        print(f"  Documents Checked: {first_result.get('documents_checked', [])}")
        print(f"  Satisfied By: {first_result.get('satisfied_by', 'null')}")
        print(f"  Actionable Instruction: {first_result.get('actionable_instruction', 'N/A')}")
        print(f"  Actionable Documents: {first_result.get('actionable_documents', 'N/A')[:80]}...")
    else:
        print("⚠ WARNING: No deficiencies found in results")
    
    print(f"{'='*80}\n")


def check_for_embeddings(obj, path="root"):
    """Recursively check for 'embedding' keys in nested structures."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'embedding':
                print(f"  Found embedding at: {path}.{key}")
                return True
            if check_for_embeddings(value, f"{path}.{key}"):
                return True
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            if check_for_embeddings(item, f"{path}[{idx}]"):
                return True
    return False


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*80)
    print("MULTI-DOCUMENT AGENT TEST SUITE")
    print("="*80 + "\n")
    
    test_cases = [
        (test_case_1_old_format, "test_1_old_format_input.json", "Test 1: Backward Compatibility (Old Format)"),
        (test_case_2_single_doc_new_format, "test_2_single_doc_new_format_input.json", "Test 2: Single Document (New Format)"),
        (test_case_3_multiple_same_type, "test_3_multiple_same_type_input.json", "Test 3: Multiple Documents (Same Type)"),
        (test_case_4_cross_document, "test_4_cross_document_input.json", "Test 4: Cross-Document Resolution"),
        (test_case_5_diverse_documents, "test_5_diverse_documents_input.json", "Test 5: Multiple Diverse Documents"),
    ]
    
    for idx, (test_data, input_filename, test_name) in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"RUNNING {test_name}")
        print(f"{'='*80}\n")
        
        try:
            # Save test input
            input_path = save_test_input(test_data, input_filename)
            
            # Run pipeline
            output_filename = f"test_{idx}_output.json"
            output_path = str(project_root / "test" / output_filename)
            
            print(f"\nExecuting pipeline...")
            result = run_pipeline_with_langgraph(
                input_file=input_path,
                output_file=output_path,
                top_n=5,  # Limit to 5 for faster testing
                verbose=True
            )
            
            # Verify output
            verify_output(result, test_name)
            
            print(f"✓ {test_name} COMPLETED")
            print(f"  Output saved to: {output_path}")
            
        except Exception as e:
            print(f"❌ {test_name} FAILED")
            print(f"  Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_all_tests()

