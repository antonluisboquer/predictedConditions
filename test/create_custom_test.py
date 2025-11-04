"""
Helper script to create custom test inputs for the multi-document agent.

Usage:
    python test/create_custom_test.py

This will create a template that you can customize.
"""

import json
from pathlib import Path

# Template for multi-document input
template = {
    "borrower_info": {
        "borrower_type": "Self-Employed",  # or "W-2 Employee", "Business Owner", etc.
        "business_name": "Your Business Name",
        "email": "borrower@email.com",
        "first_name": "First",
        "last_name": "Last",
        "middle_name": "M.",
        "phone_number": "(555) 555-5555",
        "ssn": "123-45-6789"
    },
    "loan_program": "Flex Supreme",  # or other loan program
    "documents": [
        {
            "classification": "1120 Corporate Tax Return",
            "extracted_entities": {
                "business_name": "Your Business Name",
                "ein": "12-3456789",
                "gross_receipts": "1,000,000",
                "net_income": "150,000",
                "tax_year": "2023",
                "total_assets": "500,000",
                "total_liabilities": "300,000"
            }
        },
        # Add more documents here
        # {
        #     "classification": "Schedule K-1 Form 1120S",
        #     "extracted_entities": {
        #         "shareholder_name": "First M. Last",
        #         "ownership_percentage": "50%",
        #         ...
        #     }
        # }
    ]
}

# Common document classifications
DOCUMENT_TYPES = {
    "tax_returns": [
        "1040 Personal Tax Return",
        "1120 Corporate Tax Return",
        "Form 1120S Scorp",
        "Form 1065 Partnership Return",
        "Schedule C Profit or Loss",
    ],
    "tax_schedules": [
        "Schedule K-1 Form 1120S",
        "Schedule K-1 Form 1065",
        "Schedule E Rental Income",
    ],
    "financial": [
        "Business Bank Statement",
        "Personal Bank Statement",
        "Profit and Loss Statement",
        "Balance Sheet",
    ],
    "verification": [
        "CPA Letter for Self-Employment",
        "CPA Letter for Use of Business Funds",
        "Employment Verification Letter",
        "Paystub",
        "W-2 Form",
    ],
    "business_docs": [
        "Articles of Incorporation",
        "Articles of Organization",
        "Operating Agreement",
        "Partnership Agreement",
    ]
}


def print_document_types():
    """Print available document types."""
    print("\n" + "="*80)
    print("AVAILABLE DOCUMENT CLASSIFICATIONS")
    print("="*80 + "\n")
    
    for category, docs in DOCUMENT_TYPES.items():
        print(f"{category.upper().replace('_', ' ')}:")
        for doc in docs:
            print(f"  - {doc}")
        print()


def create_custom_test():
    """Create a custom test input file."""
    print("\n" + "="*80)
    print("CUSTOM TEST INPUT CREATOR")
    print("="*80 + "\n")
    
    print_document_types()
    
    # Save template
    project_root = Path(__file__).parent.parent
    output_path = project_root / "test" / "custom_test_input.json"
    
    with open(output_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    print("="*80)
    print("✓ Template created!")
    print("="*80)
    print(f"\nFile location: {output_path}")
    print("\nNext steps:")
    print("1. Edit the file to customize borrower info and loan program")
    print("2. Add/modify documents in the 'documents' array")
    print("3. Update extracted_entities for each document")
    print("4. Run: python test/quick_test.py (after modifying quick_test.py to use your file)")
    print("\nOr run the full pipeline directly:")
    print(f"  python -c \"from src.agent.graph import run_pipeline_with_langgraph; run_pipeline_with_langgraph('{output_path}', 'custom_output.json')\"")
    print()


if __name__ == "__main__":
    create_custom_test()

