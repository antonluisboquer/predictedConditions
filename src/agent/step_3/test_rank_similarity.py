"""
Test script for rank_by_similarity.py
Interactive testing for similarity ranking.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rank_by_similarity import rank_requirements_by_similarity


def main():
    """Interactive test for Step 3 similarity ranking."""
    print("=" * 70)
    print("Step 3: Similarity Ranking Test")
    print("=" * 70)
    print("\nThis ranks requirements from Step 2 by similarity to entities.\n")
    
    # Create some dummy requirements for testing
    print("Creating sample requirements with dummy embeddings...")
    print("(In production, these come from Step 2 with real embeddings)\n")
    
    sample_requirements = [
        {
            'id': 'req_1',
            'title': 'Appraisal Report Must Be Complete',
            'description': 'Full appraisal report required with AIR certification',
            'compartment': 'Loan & Property Information',
            'suggested_data_elements': ['Appraisal Report', 'AIR Certification'],
            'embedding': [0.1] * 3072  # Dummy - would be real in production
        },
        {
            'id': 'req_2',
            'title': 'Property Value Documentation',
            'description': 'Property value must be documented and verified',
            'compartment': 'Loan & Property Information',
            'suggested_data_elements': ['Property Value', 'Appraisal Report'],
            'embedding': [0.2] * 3072
        },
        {
            'id': 'req_3',
            'title': 'Contractor Bid Submission',
            'description': 'Contractor bid required for repair work',
            'compartment': 'Borrower Information',
            'suggested_data_elements': ['Contractor Bid', 'Repair Estimate'],
            'embedding': [0.15] * 3072
        },
        {
            'id': 'req_4',
            'title': 'Tax Returns Verification',
            'description': 'Two years of tax returns required',
            'compartment': 'Employment & Income',
            'suggested_data_elements': ['Tax Returns', 'W-2 Forms'],
            'embedding': [0.05] * 3072
        },
        {
            'id': 'req_5',
            'title': 'Bank Statements Required',
            'description': 'Three months of bank statements',
            'compartment': 'Assets & Liabilities',
            'suggested_data_elements': ['Bank Statements'],
            'embedding': [0.08] * 3072
        }
    ]
    
    print(f"Sample: {len(sample_requirements)} requirements loaded\n")
    
    while True:
        print("─" * 70)
        
        # Get entity input
        entity_input = input("\nEnter entities to rank by [comma-separated] (or 'quit'): ").strip()
        
        if entity_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if not entity_input:
            print("Error: Entities required")
            continue
        
        entities = [e.strip() for e in entity_input.split(',')]
        
        # Get top N
        top_n_input = input("Return top N results (or press Enter for all): ").strip()
        top_n = int(top_n_input) if top_n_input else None
        
        # Get method
        print("\nSimilarity method:")
        print("  1. max - Use highest entity similarity (default)")
        print("  2. avg - Use average entity similarity")
        method_choice = input("Choose [1/2]: ").strip() or "1"
        method = 'max' if method_choice == '1' else 'avg'
        
        # Run ranking
        try:
            print("\n" + "=" * 70)
            print("WARNING: Using dummy embeddings for demo")
            print("Real embeddings would come from Step 2 requirements")
            print("=" * 70)
            
            ranked = rank_requirements_by_similarity(
                sample_requirements,
                entities=entities,
                top_n=top_n,
                method=method,
                verbose=True
            )
            
            # Display results
            if ranked:
                print("\n" + "─" * 70)
                print(f"RESULTS: {len(ranked)} requirement(s)")
                print("─" * 70)
                
                for i, req in enumerate(ranked, 1):
                    print(f"\n{i}. {req['title']}")
                    print(f"   Score: {req.get('similarity_score', 0.0):.3f}")
                    print(f"   Compartment: {req['compartment']}")
                    print(f"   Elements: {req.get('suggested_data_elements', [])}")
            else:
                print("\n⚠️  No requirements to rank")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")


