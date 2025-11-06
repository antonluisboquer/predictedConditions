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


# Test case: W2 borrower with URLA 1003 unsigned (tests actionable_documents fix)
test_input = {
    "borrower_info": {
        "borrower_type": "W2",
        "first_name": "Ramin",
        "last_name": "Dailamy"
    },
    "loan_program": "Flex Select",
    "documents": [
        {
            "classification": "Borrower Certification as to Business Purpose",
            "extracted_entities": {
                "borrowers": [
                    {
                        "signed": True,
                        "suffix": "",
                        "lastName": "Delgado",
                        "firstName": "Marisol",
                        "dateSigned": "2025-11-04",
                        "middleName": ""
                    }
                ],
                "propertyAddress": {
                    "city": "Riverside",
                    "state": "California",
                    "zipCode": "92501-2932",
                    "address1": "3311 LIME ST",
                    "address2": "",
                    "fullAddress": ""
                }
            }
        },
        {
            "classification": "Bank Statement",
            "extracted_entities": {
                "bank": {
                    "name": "CITI BANK N.A"
                },
                "accounts": [
                    {
                        "accountType": "Checking",
                        "accountNumber": "42029260439",
                        "endingBalance": "10985.99",
                        "accountHolderTypes": ["", "person"],
                        "accountHolderTrusts": [],
                        "accountHolderPersons": [
                            {
                                "suffix": "",
                                "lastName": "DAILAMY",
                                "firstName": "RAMIN",
                                "middleName": ""
                            }
                        ],
                        "accountHolderBusinesses": [],
                        "hasLargeDepositWithdrawal": True
                    },
                    {
                        "accountType": "Savings",
                        "accountNumber": "42029260447",
                        "endingBalance": "175.66",
                        "accountHolderTypes": ["", "person"],
                        "accountHolderTrusts": [],
                        "accountHolderPersons": [
                            {
                                "suffix": "",
                                "lastName": "DAILAMY",
                                "firstName": "RAMIN",
                                "middleName": ""
                            }
                        ],
                        "accountHolderBusinesses": [],
                        "hasLargeDepositWithdrawal": False
                    }
                ],
                "statementAddress": {
                    "city": "WEST HILLS",
                    "state": "CA",
                    "zipCode": "91307-1425",
                    "address1": "23360 SANDALWOOD ST",
                    "address2": "",
                    "fullAddress": ""
                },
                "statementPeriodTo": "2025-08-31",
                "statementPeriodFrom": "2025-08-01"
            }
        },
        {
            "classification": "Title Invoice",
            "extracted_entities": {
                "borrowers": [
                    {
                        "lastName": "Rocco",
                        "firstName": "Francis",
                        "middleName": "",
                        "suffix": "",
                        "dateSigned": "",
                        "signed": False
                    }
                ]
            }
        },
        {
            "classification": "Credit Report",
            "extracted_entities": {
                "alerts": [],
                "scores": [],
                "address": {
                    "city": "Los Angeles",
                    "state": "California",
                    "zipCode": "91307",
                    "address1": "23360 Sandalwood Street",
                    "address2": "",
                    "fullAddress": ""
                },
                "company": {
                    "name": "XACTUS"
                },
                "inquiries": [],
                "applicant1": {
                    "suffix": "",
                    "last4SSN": "4801",
                    "lastName": "Dailamy",
                    "firstName": "Ramin",
                    "middleName": ""
                },
                "applicant2": {
                    "suffix": "",
                    "last4SSN": "",
                    "lastName": "",
                    "firstName": "",
                    "middleName": ""
                },
                "reportIssued": "2025-09-16",
                "tradeSummary": [],
                "publicRecords": [],
                "mortgageSummary": [],
                "creditTradeLines": [],
                "derogatorySummary": [],
                "collectionAccounts": [],
                "derogatoryAccounts": [],
                "aliasesAndAddresses": []
            }
        },
        {
            "classification": "URLA 1003",
            "extracted_entities": {
                "a": "",
                "b": "",
                "c": "",
                "d": "",
                "e": "",
                "f": "",
                "g": "",
                "h": "",
                "i": "",
                "j": "",
                "k": "",
                "l": "",
                "m": "",
                "cost": 0,
                "banks": [],
                "total": 0,
                "amount": 0,
                "signed": False,
                "retired": False,
                "employer": {
                    "name": ""
                },
                "position": "",
                "borrowers": [
                    {
                        "DOB": "",
                        "signed": False,
                        "status": "",
                        "suffix": "",
                        "last4SSN": "",
                        "lastName": "DAILAMY",
                        "position": "",
                        "firstName": "RAMIN",
                        "homePhone": "",
                        "yrsSchool": "",
                        "dateSigned": "",
                        "middleName": "",
                        "mailingAddress": {
                            "city": "",
                            "state": "",
                            "zipCode": "",
                            "address1": "",
                            "address2": "",
                            "fullAddress": ""
                        },
                        "presentAddress": {
                            "city": "",
                            "noYrs": 0,
                            "state": "",
                            "zipCode": "",
                            "address1": "",
                            "address2": "",
                            "noMonths": 0,
                            "ownOrRent": "",
                            "fullAddress": ""
                        },
                        "formerAddresses": []
                    }
                ],
                "startDate": "",
                "employedBy": False,
                "noOfMonths": "",
                "properties": [],
                "coBorrowerA": "",
                "coBorrowerB": "",
                "coBorrowerC": "",
                "coBorrowerD": "",
                "coBorrowerE": "",
                "coBorrowerF": "",
                "coBorrowerG": "",
                "coBorrowerH": "",
                "coBorrowerI": "",
                "coBorrowerJ": "",
                "coBorrowerK": "",
                "coBorrowerL": "",
                "coBorrowerM": "",
                "liabilities": [],
                "interestRate": 0,
                "originalCost": 0,
                "selfEmployed": False,
                "yrsOnThisJob": {
                    "years": 0,
                    "months": 0
                },
                "borrowerGross": [],
                "businessPhone": "",
                "purposeOfLoan": "",
                "madeOrToBeMade": "",
                "ownershipShare": "",
                "propertyWillBe": "",
                "propertyAddress": {
                    "TBD": False,
                    "city": "CALABASAS",
                    "state": "CA",
                    "zipCode": "91302",
                    "address1": "23675 PARK CAPRI",
                    "address2": "",
                    "fullAddress": ""
                },
                "yearLotAcquired": 0,
                "amortizationType": "",
                "new1003Borrowers": [],
                "addressOfEmployer": {
                    "city": "",
                    "state": "",
                    "zipCode": "",
                    "address1": "",
                    "address2": "",
                    "fullAddress": ""
                },
                "presentValueOfLot": 0,
                "signed1003Version": "",
                "costOfImprovements": 0,
                "mortgageAppliedFor": "",
                "purposeOfRefinance": "",
                "amountExistingLiens": 0,
                "sourceOfDownPayment": "",
                "describeImprovements": "",
                "titleWillBeHeldInWhatNames": [],
                "borrowerPreviousEmployments": [],
                "yrsEmployedInThisLineOfWork": "",
                "mannerInWhichTitleWillBeHeld": ""
            }
        }
    ]
}


if __name__ == "__main__":
    print("\n" + "="*80)
    print("QUICK TEST: Multi-Document Agent (actionable_documents fix)")
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

