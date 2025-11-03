"""
Step 2: Hard Filter Requirements by Compartment Label
Retrieves requirement nodes from Neo4j that match the document's compartment label.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

# Neo4j connection configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')


def get_requirements_by_compartment(compartment_label: str) -> List[Dict[str, Any]]:
    """
    Retrieve all requirement nodes that match the given compartment label.
    
    This implements step 2aaa: Return nodes in neo4j that match with document's compartment label.
    
    Args:
        compartment_label: The compartment/category label to filter by
                          (e.g., "Continuation / Additional Information")
    
    Returns:
        List of requirement nodes as dictionaries with their properties.
        Empty list if no requirements found.
        
    Example:
        >>> get_requirements_by_compartment("Loan & Property Information")
        [
            {
                'id': '123',
                'title': 'Appraisal Report Required',
                'compartment': 'Loan & Property Information',
                'entities': ['Appraisal Report', 'Property Value'],
                ...
            },
            ...
        ]
    """
    query = """
    MATCH (req:Requirement)
    WHERE req.compartment = $compartment_label
    RETURN req
    """
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            result = session.run(query, compartment_label=compartment_label)
            requirements = []
            
            for record in result:
                req_node = record['req']
                # Convert Neo4j node to dictionary
                req_dict = dict(req_node)
                requirements.append(req_dict)
            
            return requirements
    finally:
        driver.close()


def get_requirements_by_compartment_with_entities(
    compartment_label: str, 
    entities: List[str]
) -> List[Dict[str, Any]]:
    """
    Retrieve requirement nodes that match the compartment label AND contain
    at least one of the specified entities.
    
    This implements step 2aab: Filter nodes to only those that have entities
    of the input document.
    
    Args:
        compartment_label: The compartment/category label to filter by
        entities: List of entity names to match against
                 (e.g., ['Appraisal Report', 'Tax Returns', 'W-2'])
    
    Returns:
        List of requirement nodes that match both compartment and have at least
        one of the specified entities.
        
    Example:
        >>> get_requirements_by_compartment_with_entities(
        ...     "Loan & Property Information",
        ...     ["Appraisal Report", "Property Deed"]
        ... )
        [
            {
                'id': '123',
                'title': 'Appraisal Report Required',
                'compartment': 'Loan & Property Information',
                'suggested_data_elements': ['Appraisal Report', 'Property Value'],
                ...
            },
            ...
        ]
    """
    query = """
    MATCH (req:Requirement)
    WHERE req.compartment = $compartment_label
    AND ANY(entity IN $entities WHERE entity IN req.suggested_data_elements)
    RETURN req
    """
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            result = session.run(
                query, 
                compartment_label=compartment_label,
                entities=entities
            )
            requirements = []
            
            for record in result:
                req_node = record['req']
                req_dict = dict(req_node)
                requirements.append(req_dict)
            
            return requirements
    finally:
        driver.close()


def filter_requirements(
    compartment_label: str,
    entities: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Main filtering function. Retrieves requirements by compartment label,
    optionally filtered by entities.
    
    This is the primary function to use for Step 2 hard filtering.
    
    Args:
        compartment_label: The compartment/category label (from Step 1)
        entities: Optional list of entity names to filter by
        
    Returns:
        List of matching requirement nodes
        
    Example:
        >>> # Get all requirements for a compartment
        >>> reqs = filter_requirements("Loan & Property Information")
        
        >>> # Get requirements that also match specific entities
        >>> reqs = filter_requirements(
        ...     "Loan & Property Information",
        ...     entities=["Appraisal Report", "Tax Returns"]
        ... )
    """
    if entities:
        return get_requirements_by_compartment_with_entities(compartment_label, entities)
    else:
        return get_requirements_by_compartment(compartment_label)


def filter_requirements_multiple_compartments(
    compartment_labels: List[str],
    entities: Optional[List[str]] = None,
    deduplicate: bool = True
) -> List[Dict[str, Any]]:
    """
    Filter requirements across MULTIPLE compartments.
    
    Since Step 1 can return multiple compartments for a document,
    this function handles all of them at once.
    
    Args:
        compartment_labels: List of compartment labels (from Step 1)
        entities: Optional list of entity names to filter by
        deduplicate: If True, removes duplicate requirements (default: True)
        
    Returns:
        List of all matching requirement nodes across all compartments
        
    Example:
        >>> # Step 1 returns multiple compartments
        >>> compartments = ["Borrower Information", "Loan & Property Information"]
        >>> 
        >>> # Step 2 processes all compartments
        >>> reqs = filter_requirements_multiple_compartments(compartments)
        >>> 
        >>> # With entity filtering
        >>> reqs = filter_requirements_multiple_compartments(
        ...     compartments,
        ...     entities=["Appraisal Report", "Tax Returns"]
        ... )
    """
    all_requirements = []
    seen_ids = set()
    
    for compartment in compartment_labels:
        requirements = filter_requirements(compartment, entities=entities)
        
        if deduplicate:
            # Add only unique requirements (based on ID or properties)
            for req in requirements:
                # Use a unique identifier (adjust based on your node properties)
                req_id = req.get('id') or str(req)
                
                if req_id not in seen_ids:
                    seen_ids.add(req_id)
                    all_requirements.append(req)
        else:
            all_requirements.extend(requirements)
    
    return all_requirements


# Example usage:
if __name__ == "__main__":
    # Test compartment labels
    test_compartments = [
        "Continuation / Additional Information",
        "Loan & Property Information",
        "Borrower Information"
    ]
    
    print("=" * 70)
    print("Step 2: Hard Filter - Requirements by Compartment")
    print("=" * 70)
    
    for compartment in test_compartments:
        print(f"\n{'='*70}")
        print(f"Compartment: '{compartment}'")
        print('='*70)
        
        # Get all requirements for this compartment
        requirements = filter_requirements(compartment)
        
        print(f"Found {len(requirements)} requirement(s)")
        
        # Display first 3 requirements as sample
        for i, req in enumerate(requirements[:3], 1):
            print(f"\nRequirement {i}:")
            # Display key fields (adjust based on your actual node properties)
            for key, value in req.items():
                if key not in ['embedding', 'vector']:  # Skip large fields
                    if isinstance(value, list) and len(value) > 3:
                        print(f"  {key}: {value[:3]}... ({len(value)} total)")
                    else:
                        print(f"  {key}: {value}")
        
        if len(requirements) > 3:
            print(f"\n  ... and {len(requirements) - 3} more")
    
    # Example with entity filtering
    print("\n" + "=" * 70)
    print("Example with Entity Filtering")
    print("=" * 70)
    
    compartment = "Loan & Property Information"
    entities = ["Appraisal Report", "Property Deed"]
    
    print(f"\nCompartment: '{compartment}'")
    print(f"Entities: {entities}")
    
    filtered_reqs = filter_requirements(compartment, entities=entities)
    print(f"\nFound {len(filtered_reqs)} requirement(s) matching entities")
    
    # Example with MULTIPLE compartments (like from Step 1)
    print("\n" + "=" * 70)
    print("Example with MULTIPLE Compartments (Step 1 → Step 2)")
    print("=" * 70)
    
    # Simulate Step 1 output - multiple compartments for one document
    document_name = "Contractor Bid"
    compartments_from_step1 = [
        "Borrower Information",
        "Loan & Property Information",
        "Acknowledgments & Agreements"
    ]
    
    print(f"\nDocument: '{document_name}'")
    print(f"Compartments from Step 1: {compartments_from_step1}")
    
    # Process all compartments at once
    all_reqs = filter_requirements_multiple_compartments(compartments_from_step1)
    print(f"\nTotal requirements across all compartments: {len(all_reqs)}")
    
    # Break down by compartment
    print("\nBreakdown:")
    for comp in compartments_from_step1:
        comp_reqs = filter_requirements(comp)
        print(f"  {comp}: {len(comp_reqs)} requirement(s)")

