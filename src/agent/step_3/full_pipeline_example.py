"""
Complete Pipeline Example: Step 1 → Step 2 → Step 3
Shows the full workflow from document to ranked requirements.
"""

import sys
from pathlib import Path

# Add paths
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "step_1"))
sys.path.insert(0, str(parent_dir / "step_2"))
sys.path.insert(0, str(parent_dir / "step_3"))

from retrieve_document_categories import get_document_category
from hard_filter import hard_filter
from rank_by_similarity import rank_requirements_by_similarity


def run_complete_pipeline(
    document_name: str,
    document_entities: List[str],
    top_n: int = 10,
    similarity_threshold: float = 0.3
):
    """
    Run the complete deficiency detection pipeline.
    
    Args:
        document_name: Name of the document (for Step 1)
        document_entities: List of entities extracted from document
        top_n: Return top N requirements
        similarity_threshold: Threshold for Step 2 semantic search
        
    Returns:
        Top N ranked requirements
    """
    print("\n" + "="*70)
    print("COMPLETE PIPELINE: Steps 1 → 2 → 3")
    print("="*70)
    print(f"\nInput Document: '{document_name}'")
    print(f"Entities: {document_entities}")
    
    # ========== STEP 1: Get Compartment Labels ==========
    print("\n" + "█"*70)
    print("█ STEP 1: OBTAIN COMPARTMENT LABEL")
    print("█"*70)
    
    compartments = get_document_category(document_name)
    
    if not compartments:
        print(f"❌ No compartments found for '{document_name}'")
        return []
    
    print(f"\n✓ Found {len(compartments)} compartment(s):")
    for comp in compartments:
        print(f"  • {comp}")
    
    # ========== STEP 2: Hard Filter ==========
    print("\n" + "█"*70)
    print("█ STEP 2: HARD FILTER")
    print("█"*70)
    
    filtered_requirements = hard_filter(
        compartments=compartments,
        entities=document_entities,
        similarity_threshold=similarity_threshold,
        verbose=True
    )
    
    if not filtered_requirements:
        print("❌ No requirements found after filtering")
        return []
    
    # ========== STEP 3: Rank by Similarity ==========
    print("\n" + "█"*70)
    print("█ STEP 3: RANK BY SIMILARITY")
    print("█"*70)
    
    ranked_requirements = rank_requirements_by_similarity(
        filtered_requirements,
        entities=document_entities,
        top_n=top_n,
        method='max',
        verbose=True
    )
    
    # ========== FINAL RESULTS ==========
    print("\n" + "="*70)
    print("PIPELINE COMPLETE!")
    print("="*70)
    print(f"\nFinal Output: Top {len(ranked_requirements)} Requirements")
    print("\nTop 5:")
    for i, req in enumerate(ranked_requirements[:5], 1):
        print(f"\n{i}. {req.get('title', 'N/A')}")
        print(f"   Compartment: {req.get('compartment', 'N/A')}")
        print(f"   Similarity Score: {req.get('similarity_score', 0.0):.3f}")
        elements = req.get('suggested_data_elements', [])
        if elements:
            print(f"   Data Elements: {elements[:3]}{'...' if len(elements) > 3 else ''}")
    
    return ranked_requirements


# Example scenarios
if __name__ == "__main__":
    from typing import List
    
    print("="*70)
    print("FULL PIPELINE EXAMPLES")
    print("="*70)
    
    scenarios = [
        {
            'name': 'Appraisal Document',
            'document_name': 'Appraisal Report',
            'entities': ['Appraisal Report', 'Property Value', 'AIR Certification']
        },
        {
            'name': 'Contractor Document',
            'document_name': 'Contractor Bid',
            'entities': ['Contractor Bid', 'Repair Estimate', 'Property Address']
        },
        {
            'name': 'Employment Document',
            'document_name': 'W-2 Forms',
            'entities': ['W-2 Forms', 'Pay Stubs', 'Employment Verification']
        }
    ]
    
    print("\nAvailable scenarios:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print(f"   Document: {scenario['document_name']}")
        print(f"   Entities: {scenario['entities']}")
    
    choice = input("\nChoose scenario [1-3] or Enter to skip: ").strip()
    
    if choice and choice.isdigit() and 1 <= int(choice) <= len(scenarios):
        scenario = scenarios[int(choice) - 1]
        
        print(f"\n{'='*70}")
        print(f"Running: {scenario['name']}")
        print(f"{'='*70}")
        
        try:
            results = run_complete_pipeline(
                document_name=scenario['document_name'],
                document_entities=scenario['entities'],
                top_n=10,
                similarity_threshold=0.3
            )
            
            print(f"\n✓ Pipeline completed with {len(results)} results")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nNo scenario selected. Example completed.")


