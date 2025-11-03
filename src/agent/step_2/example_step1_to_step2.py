"""
Example: Complete Step 1 → Step 2 Pipeline
Shows how to handle multiple compartments from Step 1 in Step 2.
"""

import sys
from pathlib import Path

# Add parent and step_1 to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "step_1"))
sys.path.insert(0, str(parent_dir / "step_2"))

from retrieve_document_categories import get_document_category
from filter_requirements_by_compartment import (
    filter_requirements,
    filter_requirements_multiple_compartments
)


def example_single_compartment_workflow():
    """Example: Document with single compartment."""
    print("=" * 70)
    print("Example 1: Single Compartment Workflow")
    print("=" * 70)
    
    document_name = "Some Document"
    
    # Step 1: Get compartments
    print(f"\nSTEP 1: Getting compartments for '{document_name}'...")
    compartments = get_document_category(document_name)
    print(f"Found compartments: {compartments}")
    
    if not compartments:
        print("No compartments found. Exiting.")
        return
    
    # Step 2: Get requirements (if only one compartment)
    if len(compartments) == 1:
        print(f"\nSTEP 2: Getting requirements for '{compartments[0]}'...")
        requirements = filter_requirements(compartments[0])
        print(f"Found {len(requirements)} requirement(s)")


def example_multiple_compartments_workflow():
    """Example: Document with multiple compartments (most common case)."""
    print("\n" + "=" * 70)
    print("Example 2: Multiple Compartments Workflow")
    print("=" * 70)
    
    document_name = "Contractor Bid"
    
    # Step 1: Get compartments
    print(f"\nSTEP 1: Getting compartments for '{document_name}'...")
    compartments = get_document_category(document_name)
    print(f"Found {len(compartments)} compartment(s): {compartments}")
    
    if not compartments:
        print("No compartments found. Exiting.")
        return
    
    # Step 2 Option A: Process each compartment separately
    print(f"\nSTEP 2a: Processing each compartment separately...")
    for compartment in compartments:
        requirements = filter_requirements(compartment)
        print(f"  '{compartment}': {len(requirements)} requirement(s)")
    
    # Step 2 Option B: Process all compartments at once (RECOMMENDED)
    print(f"\nSTEP 2b: Processing all compartments together...")
    all_requirements = filter_requirements_multiple_compartments(compartments)
    print(f"Total unique requirements: {len(all_requirements)}")
    
    return all_requirements


def example_with_entity_filtering():
    """Example: Multiple compartments WITH entity filtering."""
    print("\n" + "=" * 70)
    print("Example 3: Multiple Compartments + Entity Filtering")
    print("=" * 70)
    
    document_name = "Appraisal Report"
    entities = ["Appraisal Report", "AIR Certification", "Property Value"]
    
    # Step 1: Get compartments
    print(f"\nSTEP 1: Getting compartments for '{document_name}'...")
    compartments = get_document_category(document_name)
    print(f"Found compartments: {compartments}")
    
    if not compartments:
        print("No compartments found. Exiting.")
        return
    
    # Step 2: Get requirements filtered by entities
    print(f"\nSTEP 2: Filtering by compartments AND entities...")
    print(f"Entities: {entities}")
    
    requirements = filter_requirements_multiple_compartments(
        compartments,
        entities=entities
    )
    
    print(f"\nFound {len(requirements)} requirement(s) matching criteria")
    
    # Show sample
    if requirements:
        print("\nSample requirement:")
        req = requirements[0]
        print(f"  Title: {req.get('title', 'N/A')}")
        print(f"  Compartment: {req.get('compartment', 'N/A')}")
        matched_entities = [e for e in entities if e in req.get('suggested_data_elements', [])]
        print(f"  Matched entities: {matched_entities}")


def example_complete_pipeline():
    """Example: Complete realistic pipeline."""
    print("\n" + "=" * 70)
    print("Example 4: Complete Pipeline (Realistic Scenario)")
    print("=" * 70)
    
    # Input: Document from rack and stack
    document_name = "Contractor Bid"
    document_entities = ["Contractor Bid", "Repair Estimate", "Property Address"]
    
    print(f"\nInput Document: '{document_name}'")
    print(f"Detected Entities: {document_entities}")
    
    # STEP 1: Get compartment labels
    print(f"\n{'─'*70}")
    print("STEP 1: Obtain Compartment Label")
    print('─'*70)
    compartments = get_document_category(document_name)
    print(f"✓ Found {len(compartments)} compartment(s):")
    for comp in compartments:
        print(f"  • {comp}")
    
    # STEP 2: Hard filter by compartment
    print(f"\n{'─'*70}")
    print("STEP 2: Hard Filter Requirements")
    print('─'*70)
    
    # 2a: Filter by compartment only
    print("\n2a. Filtering by compartment...")
    reqs_by_compartment = filter_requirements_multiple_compartments(compartments)
    print(f"✓ Found {len(reqs_by_compartment)} requirement(s) across all compartments")
    
    # 2b: Filter by compartment AND entities
    print("\n2b. Further filtering by entities...")
    reqs_final = filter_requirements_multiple_compartments(
        compartments,
        entities=document_entities
    )
    print(f"✓ Found {len(reqs_final)} requirement(s) matching entities")
    
    print(f"\n{'─'*70}")
    print("SUMMARY")
    print('─'*70)
    print(f"Document: {document_name}")
    print(f"Compartments: {len(compartments)}")
    print(f"Requirements (compartment only): {len(reqs_by_compartment)}")
    print(f"Requirements (compartment + entities): {len(reqs_final)}")
    print("\n→ Ready for Step 3: Similarity Search")
    
    return reqs_final


if __name__ == "__main__":
    try:
        print("\n" + "=" * 70)
        print("STEP 1 → STEP 2 PIPELINE EXAMPLES")
        print("=" * 70)
        
        example_multiple_compartments_workflow()
        
        example_with_entity_filtering()
        
        example_complete_pipeline()
        
        print("\n" + "=" * 70)
        print("All examples completed!")
        print("=" * 70)
        print("\nKey Takeaway:")
        print("  Use filter_requirements_multiple_compartments() to handle")
        print("  multiple compartments from Step 1 efficiently.")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

