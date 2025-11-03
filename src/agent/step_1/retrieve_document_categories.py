"""
Retrieve DocumentCategory data from Neo4j database.
Simple function to find which category/compartment a document belongs to.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

# Neo4j connection configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')


def get_document_category(document_name: str) -> List[str]:
    """
    Find which category/compartment a document belongs to.
    
    Args:
        document_name: Name of the document to search for
        
    Returns:
        List of category names (compartments) containing the document.
        Empty list if document not found.
        
    Example:
        >>> get_document_category("Appraisal Report")
        ['Loan & Property Information', 'Assets & Liabilities']
    """
    query = """
    MATCH (dc:DocumentCategory)
    WHERE $document_name IN dc.documents
    RETURN dc.name as name
    """
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            result = session.run(query, document_name=document_name)
            return [record['name'] for record in result]
    finally:
        driver.close()



# Example usage:
if __name__ == "__main__":
    # Test with different documents
    documents_to_test = [
        "Acknowledgement of Receipt of Appraisal Report",
        "Appraisal Report",
        "W-2 Forms"
    ]
    
    print("Finding document categories/compartments:")
    print("=" * 60)
    
    for doc in documents_to_test:
        categories = get_document_category(doc)
        print(f"\n'{doc}'")
        if categories:
            print(f"  → Found in: {categories}")
        else:
            print(f"  → Not found in any category")

