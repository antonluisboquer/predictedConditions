"""
Interactive test script for retrieve_document_categories.py
Enter a document name and get the categories it belongs to.
"""

import sys
from pathlib import Path

# Add step_1 directory to path
sys.path.insert(0, str(Path(__file__).parent))

from retrieve_document_categories import get_document_category


def main():
    """Main interactive function."""
    print("=" * 70)
    print("Document Category Lookup")
    print("=" * 70)
    print("\nEnter a document name to find which category it belongs to.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    while True:
        # Get user input
        document_name = input("Enter document name: ").strip()
        
        # Check for exit commands
        if document_name.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        # Skip empty input
        if not document_name:
            print("Please enter a document name.\n")
            continue
        
        # Query the database
        print(f"\nSearching for: '{document_name}'...")
        try:
            categories = get_document_category(document_name)
            
            if categories:
                print(f"✅ Found in {len(categories)} category/categories:")
                for i, category in enumerate(categories, 1):
                    print(f"   {i}. {category}")
            else:
                print("❌ Document not found in any category")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()  # Empty line for readability


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)

