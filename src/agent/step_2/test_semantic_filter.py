"""
Test script for semantic entity filtering in Step 2.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from semantic_entity_filter import filter_requirements_combined


def main():
    """Interactive test for semantic entity filtering."""
    print("=" * 70)
    print("Step 2: Semantic Entity Filter Test")
    print("=" * 70)
    print("\nThis uses embedding-based semantic search to find requirements")
    print("related to entities, then combines with compartment filtering.\n")
    
    # Get compartment input
    compartment_input = input("Enter compartment label(s) [comma-separated]: ").strip()
    if not compartment_input:
        print("Error: Compartment required")
        return
    
    compartments = [c.strip() for c in compartment_input.split(',')]
    
    # Get entity input
    entity_input = input("Enter entities [comma-separated]: ").strip()
    if not entity_input:
        print("No entities provided, using compartment only")
        entities = None
    else:
        entities = [e.strip() for e in entity_input.split(',')]
    
    # Get combine method
    print("\nCombine method:")
    print("  1. intersection - Requirements must match BOTH compartment AND entities")
    print("  2. union - Requirements match EITHER compartment OR entities")
    method_choice = input("Choose method [1/2] (default: 1): ").strip() or "1"
    combine_method = 'intersection' if method_choice == '1' else 'union'
    
    print("\n" + "=" * 70)
    print("Searching...")
    print("=" * 70)
    
    try:
        requirements = filter_requirements_combined(
            compartment_labels=compartments,
            entities=entities,
            use_semantic_search=True,
            combine_method=combine_method
        )
        
        print("\n" + "=" * 70)
        print(f"Results: {len(requirements)} requirement(s) found")
        print("=" * 70)
        
        # Display results
        for i, req in enumerate(requirements[:5], 1):
            print(f"\nRequirement {i}:")
            for key, value in req.items():
                if key in ['embedding', 'vector']:
                    continue
                if isinstance(value, list) and len(value) > 3:
                    print(f"  {key}: {value[:3]}... ({len(value)} total)")
                else:
                    print(f"  {key}: {value}")
        
        if len(requirements) > 5:
            print(f"\n... and {len(requirements) - 5} more")
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")

