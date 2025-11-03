"""
Interactive test script for filter_requirements_by_compartment.py
Enter a compartment label and get the requirement nodes that match.
"""

import sys
from pathlib import Path

# Add step_2 directory to path
sys.path.insert(0, str(Path(__file__).parent))

from filter_requirements_by_compartment import (
    filter_requirements,
    filter_requirements_multiple_compartments
)


def main():
    """Main interactive function."""
    print("=" * 70)
    print("Step 2: Requirement Filter by Compartment")
    print("=" * 70)
    print("\nEnter compartment label(s) to get matching requirements.")
    print("  • Single compartment: 'Loan & Property Information'")
    print("  • Multiple compartments: separate with commas")
    print("    Example: 'Loan & Property Information, Borrower Information'")
    print("\nType 'quit' or 'exit' to stop.\n")
    
    print("Common compartment labels:")
    print("  - Continuation / Additional Information")
    print("  - Loan & Property Information")
    print("  - Borrower Information")
    print("  - Assets & Liabilities")
    print("  - Declarations")
    print("  - Employment & Income")
    print("  - Acknowledgments & Agreements")
    print("  - Demographic Information (HMDA)")
    print()
    
    while True:
        # Get user input
        compartment_input = input("Enter compartment label(s): ").strip()
        
        # Check for exit commands
        if compartment_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        # Skip empty input
        if not compartment_input:
            print("Please enter a compartment label.\n")
            continue
        
        # Check if multiple compartments (comma-separated)
        compartments = [c.strip() for c in compartment_input.split(',')]
        
        # Query the database
        try:
            if len(compartments) == 1:
                compartment_label = compartments[0]
                print(f"\nSearching for requirements in: '{compartment_label}'...")
                requirements = filter_requirements(compartment_label)
            else:
                print(f"\nSearching across {len(compartments)} compartments:")
                for comp in compartments:
                    print(f"  • {comp}")
                print()
                requirements = filter_requirements_multiple_compartments(compartments)
            
            if requirements:
                print(f"✅ Found {len(requirements)} requirement(s)\n")
                
                # Display first 5 requirements
                for i, req in enumerate(requirements[:5], 1):
                    print(f"Requirement {i}:")
                    
                    # Display important fields
                    for key, value in req.items():
                        # Skip large fields
                        if key in ['embedding', 'vector']:
                            continue
                        
                        # Truncate long lists
                        if isinstance(value, list) and len(value) > 3:
                            print(f"  {key}: {value[:3]}... ({len(value)} total)")
                        else:
                            print(f"  {key}: {value}")
                    print()
                
                if len(requirements) > 5:
                    print(f"... and {len(requirements) - 5} more requirements")
                
                # Ask if user wants to filter by entities
                filter_by_entities = input("\nFilter by entities? (y/n): ").strip().lower()
                if filter_by_entities == 'y':
                    entities_input = input("Enter entity names (comma-separated): ").strip()
                    if entities_input:
                        entities = [e.strip() for e in entities_input.split(',')]
                        print(f"\nFiltering by entities: {entities}...")
                        
                        # Use appropriate function based on number of compartments
                        if len(compartments) == 1:
                            filtered_reqs = filter_requirements(compartments[0], entities=entities)
                        else:
                            filtered_reqs = filter_requirements_multiple_compartments(compartments, entities=entities)
                        
                        print(f"✅ Found {len(filtered_reqs)} requirement(s) matching entities\n")
                        
                        for i, req in enumerate(filtered_reqs[:3], 1):
                            print(f"Requirement {i}:")
                            for key, value in req.items():
                                if key in ['embedding', 'vector']:
                                    continue
                                if isinstance(value, list) and len(value) > 3:
                                    print(f"  {key}: {value[:3]}... ({len(value)} total)")
                                else:
                                    print(f"  {key}: {value}")
                            print()
            else:
                print("❌ No requirements found for this compartment(s)")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()  # Empty line for readability


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)

