"""
Test script for hard_filter.py - Main Step 2 workflow.
Interactive testing for compartment + semantic entity filtering.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hard_filter import hard_filter


def main():
    """Interactive test for Step 2 hard filter."""
    print("=" * 70)
    print("Step 2: Hard Filter Test")
    print("=" * 70)
    print("\nThis combines:")
    print("  • Compartment matching (exact)")
    print("  • Entity semantic search (embeddings)")
    print("  • Returns requirements matching BOTH\n")
    
    while True:
        # Get compartment input
        print("─" * 70)
        compartment_input = input("\nEnter compartment(s) [comma-separated] (or 'quit'): ").strip()
        
        if compartment_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if not compartment_input:
            print("Error: Compartment required")
            continue
        
        compartments = [c.strip() for c in compartment_input.split(',')]
        
        # Get entity input
        entity_input = input("Enter entities [comma-separated]: ").strip()
        
        if not entity_input:
            print("Error: Entities required for semantic search")
            continue
        
        entities = [e.strip() for e in entity_input.split(',')]
        
        # Ask about similarity threshold
        threshold_input = input("Similarity threshold (0.1-1.0, default 0.5): ").strip()
        if threshold_input:
            try:
                similarity_threshold = float(threshold_input)
            except:
                print("Invalid threshold, using default 0.5")
                similarity_threshold = 0.5
        else:
            similarity_threshold = 0.5
        
        # Run hard filter
        try:
            requirements = hard_filter(
                compartments=compartments,
                entities=entities,
                verbose=True,
                similarity_threshold=similarity_threshold
            )
            
            # Display results
            if requirements:
                print("\n" + "─" * 70)
                print(f"RESULTS: {len(requirements)} requirement(s)")
                print("─" * 70)
                
                # Show first 3
                for i, req in enumerate(requirements[:3], 1):
                    print(f"\nRequirement {i}:")
                    for key, value in req.items():
                        if key in ['embedding', 'vector']:
                            continue
                        if isinstance(value, list) and len(value) > 3:
                            print(f"  {key}: {value[:3]}... ({len(value)} total)")
                        else:
                            print(f"  {key}: {value}")
                
                if len(requirements) > 3:
                    print(f"\n... and {len(requirements) - 3} more")
            else:
                print("\n⚠️  No requirements matched both compartment AND entities")
                print("Try:")
                print("  • Different compartments")
                print("  • Different entities")
                print("  • Check if entities are related to the compartment")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()


def quick_example():
    """Run a quick example without user input."""
    print("=" * 70)
    print("Quick Example")
    print("=" * 70)
    
    compartments = ["Loan & Property Information"]
    entities = ["Appraisal Report", "Property Value"]
    
    print(f"\nCompartments: {compartments}")
    print(f"Entities: {entities}")
    
    try:
        requirements = hard_filter(
            compartments=compartments,
            entities=entities,
            verbose=True
        )
        
        print(f"\n✓ Found {len(requirements)} matching requirements")
        
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--example':
        # Run quick example
        quick_example()
    else:
        # Run interactive mode
        try:
            main()
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")

