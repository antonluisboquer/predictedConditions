"""
Step 2: Hard Filter Requirements
Main workflow - simple and clear.

Process:
1. Get requirements with matching compartment (exact match)
2. Get requirements via semantic search on entities (embeddings)
3. Return requirements that match BOTH (intersection)
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict, Any
from openai import OpenAI

# Load environment variables
load_dotenv()

# Neo4j configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def get_requirements_by_compartment(
    compartments: List[str],
    loan_program: str = None
) -> List[Dict[str, Any]]:
    """
    Path A: Get all requirements that match the compartment labels and optionally loan program.
    
    Args:
        compartments: List of compartment labels from Step 1
        loan_program: Optional loan program name to filter by (fuzzy match)
        
    Returns:
        List of requirement nodes matching compartments (and loan program if specified)
    """
    if loan_program:
        # New implementation: First find loan program, then get its requirements filtered by compartment
        query = """
        // Step 1: Find the loan program node (fuzzy match)
        MATCH (program)
        WHERE program.name IS NOT NULL
          AND (toLower(program.name) CONTAINS toLower($loan_program)
               OR toLower($loan_program) CONTAINS toLower(program.name))
        
        // Step 2: Get all requirements connected to this program
        MATCH (program)-[]->(req:Requirement)
        
        // Step 3: Filter by compartment
        WHERE req.compartment IN $compartments
        
        RETURN DISTINCT req, program.name AS program_name
        """
    else:
        # Without loan program filter, just match by compartment
        query = """
        MATCH (req:Requirement)
        WHERE req.compartment IN $compartments
        
        // Optionally get program if it exists
        OPTIONAL MATCH (program)-[]->(req)
        WHERE program.name IS NOT NULL
        
        RETURN req, collect(DISTINCT program.name) AS programs
        """
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            if loan_program:
                result = session.run(query, compartments=compartments, loan_program=loan_program)
            else:
                result = session.run(query, compartments=compartments)
            
            requirements = []
            program_counts = {}  # Track which programs requirements belong to
            
            for record in result:
                req_node = record['req']
                req_dict = dict(req_node)
                # Add the Neo4j element ID for later use
                req_dict['_element_id'] = req_node.element_id
                
                # Get programs this requirement belongs to
                if loan_program:
                    # When filtering by loan_program, we get a single program_name
                    program_name = record.get('program_name')
                    req_dict['_programs'] = [program_name] if program_name else []
                else:
                    # Without loan_program filter, we get a list of programs
                    programs = record.get('programs', [])
                    programs = [p for p in programs if p]  # Filter out None values
                    req_dict['_programs'] = programs
                
                # Count programs
                for prog in req_dict['_programs']:
                    program_counts[prog] = program_counts.get(prog, 0) + 1
                
                requirements.append(req_dict)
            
            # Print summary of programs found
            if program_counts:
                print(f"\n  Requirements by Program:")
                for prog, count in sorted(program_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"    • {prog}: {count} requirement(s)")
            
            return requirements
    finally:
        driver.close()


def get_entity_embedding(entity_text: str) -> List[float]:
    """Generate embedding for an entity using OpenAI."""
    if not openai_client:
        raise ValueError("OpenAI API key not configured")
    
    response = openai_client.embeddings.create(
        input=entity_text,
        model="text-embedding-3-large"
    )
    return response.data[0].embedding


def get_requirements_by_semantic_search(
    entities: List[str],
    top_k: int = 20,
    similarity_threshold: float = 0.5  # Lowered from 0.7 to 0.5 (50% similarity)
) -> List[Dict[str, Any]]:
    """
    Path B: Get requirements via semantic search on entities.
    
    Process:
    1. For each entity, generate embedding
    2. Find all nodes in DB similar to entity (using embeddings)
    3. Get Requirement nodes connected to those similar nodes
    4. Collate all unique requirements
    
    Args:
        entities: List of entity texts from input document
        top_k: How many similar nodes to find per entity
        similarity_threshold: Minimum similarity score (0-1)
        
    Returns:
        List of unique requirement nodes found via semantic search
    """
    all_requirements = []
    seen_req_ids = set()
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            for entity in entities:
                # Generate embedding for entity
                try:
                    entity_embedding = get_entity_embedding(entity)
                except Exception as e:
                    print(f"    ⚠️  Failed to get embedding for '{entity}': {e}")
                    continue
                
                # Find similar nodes and their connected Requirements
                query = """
                MATCH (n)
                WHERE n.embedding IS NOT NULL
                WITH n, 
                     gds.similarity.cosine(n.embedding, $entity_embedding) AS similarity
                WHERE similarity >= $threshold
                ORDER BY similarity DESC
                LIMIT $top_k
                WITH n
                MATCH (n)-[*1..2]-(req:Requirement)
                RETURN DISTINCT req
                """
                
                try:
                    result = session.run(
                        query,
                        entity_embedding=entity_embedding,
                        threshold=similarity_threshold,
                        top_k=top_k
                    )
                    
                    count = 0
                    # Collect unique requirements
                    for record in result:
                        req_node = record['req']
                        req_dict = dict(req_node)
                        # Add the Neo4j element ID for later use
                        req_dict['_element_id'] = req_node.element_id
                        req_id = req_dict.get('id') or str(req_dict)
                        
                        if req_id not in seen_req_ids:
                            seen_req_ids.add(req_id)
                            all_requirements.append(req_dict)
                            count += 1
                    
                    print(f"    '{entity}': Found {count} requirement(s)")
                    
                except Exception as e:
                    print(f"    ⚠️  Query failed for '{entity}': {e}")
                    print(f"    💡 This might mean:")
                    print(f"       - Neo4j GDS plugin not installed (for gds.similarity.cosine)")
                    print(f"       - Nodes don't have 'embedding' property")
                    print(f"       - No relationship path to Requirement nodes")
                    continue
        
        return all_requirements
    finally:
        driver.close()


def hard_filter(
    compartments: List[str],
    entities: List[str],
    loan_program: str = None,
    verbose: bool = True,
    similarity_threshold: float = 0.5,
    top_k: int = 20
) -> List[Dict[str, Any]]:
    """
    Main Step 2 function: Hard filter requirements.
    
    Workflow:
    1. Get requirements with matching compartment (and optionally loan program)
    2. Get requirements via semantic search on entities  
    3. Return only requirements that match BOTH
    
    Args:
        compartments: List of compartment labels (from Step 1)
        entities: List of entity texts from input document
        loan_program: Optional loan program name to filter by (fuzzy match)
        verbose: If True, print progress
        similarity_threshold: Minimum similarity score (0-1). Default 0.5 (50%)
                             Lower = more results, Higher = stricter matching
        top_k: How many similar nodes to find per entity. Default 20
        
    Returns:
        List of requirement nodes that match BOTH compartment AND entities.
        If no intersection, returns all compartment-matched requirements.
        
    Example:
        >>> # Basic usage
        >>> requirements = hard_filter(
        ...     compartments=["Loan & Property Information"],
        ...     entities=["Appraisal Report", "Property Value"]
        ... )
        
        >>> # With loan program filter
        >>> requirements = hard_filter(
        ...     compartments=["Loan & Property Information"],
        ...     entities=["Appraisal Report"],
        ...     loan_program="Flex Supreme"
        ... )
        
        >>> # Adjust strictness
        >>> requirements = hard_filter(
        ...     compartments=["Loan & Property Information"],
        ...     entities=["Appraisal Report"],
        ...     similarity_threshold=0.3,  # More lenient (30% similarity)
        ...     top_k=50  # Search more nodes
        ... )
    """
    if verbose:
        print("\n" + "="*70)
        print("STEP 2: HARD FILTER")
        print("="*70)
        print(f"\nInput:")
        print(f"  Compartments: {compartments}")
        print(f"  Entities: {entities}")
        if loan_program:
            print(f"  Loan Program: {loan_program}")
    
    # Path A: Filter by compartment (and optionally loan program)
    if verbose:
        print(f"\n{'─'*70}")
        if loan_program:
            print("Path A: Compartment + Loan Program Matching")
        else:
            print("Path A: Compartment Matching")
        print('─'*70)
    
    reqs_by_compartment = get_requirements_by_compartment(compartments, loan_program)
    
    if verbose:
        print(f"✓ Found {len(reqs_by_compartment)} requirement(s) with matching compartment")
        
        # Show sample requirements with their programs
        if reqs_by_compartment and len(reqs_by_compartment) > 0:
            print(f"\n  Sample Requirements (showing up to 3):")
            for i, req in enumerate(reqs_by_compartment[:3], 1):
                req_name = req.get('name') or req.get('title') or req.get('id', 'N/A')
                programs = req.get('_programs', ['Unknown'])
                programs_str = ', '.join(programs)
                print(f"    {i}. {req_name[:60]}")
                print(f"       └─ Program(s): {programs_str}")
    
    # Path B: Semantic search on entities
    if verbose:
        print(f"\n{'─'*70}")
        print("Path B: Semantic Entity Search")
        print(f"  Similarity threshold: {similarity_threshold} (lower = more results)")
        print(f"  Top-k per entity: {top_k}")
        print('─'*70)
    
    reqs_by_entities = get_requirements_by_semantic_search(
        entities,
        top_k=top_k,
        similarity_threshold=similarity_threshold
    )
    
    if verbose:
        print(f"✓ Found {len(reqs_by_entities)} requirement(s) via semantic search")
    
    # Intersection: Requirements that match BOTH
    if verbose:
        print(f"\n{'─'*70}")
        print("Combining: Intersection (BOTH compartment AND entities)")
        print('─'*70)
    
    # Create set of IDs from compartment results
    compartment_ids = {req.get('id') or str(req) for req in reqs_by_compartment}
    
    # Keep only entity results that are also in compartment results
    final_requirements = []
    for req in reqs_by_entities:
        req_id = req.get('id') or str(req)
        if req_id in compartment_ids:
            final_requirements.append(req)
    
    # Fallback: If no intersection, return all compartment results
    if len(final_requirements) == 0:
        if verbose:
            print(f"⚠️  No requirements matched BOTH conditions")
            print(f"📋 Fallback: Returning all {len(reqs_by_compartment)} requirement(s) from Path A (compartment)")
        final_requirements = reqs_by_compartment
    else:
        if verbose:
            print(f"✓ {len(final_requirements)} requirement(s) match BOTH conditions")
    
    if verbose:
        print("\n" + "="*70)
        print(f"STEP 2 COMPLETE: {len(final_requirements)} requirements → Send to Step 3")
        print("="*70)
    
    return final_requirements


# Example usage
if __name__ == "__main__":
    print("="*70)
    print("Step 2: Hard Filter - Main Workflow")
    print("="*70)
    
    # Example inputs
    compartments = ["Loan & Property Information"]
    entities = ["Appraisal Report", "Property Value"]
    
    try:
        requirements = hard_filter(
            compartments=compartments,
            entities=entities,
            verbose=True
        )
        
        # Show results
        if requirements:
            print(f"\nSample Result (first requirement):")
            req = requirements[0]
            for key, value in req.items():
                if key not in ['embedding', 'vector']:
                    if isinstance(value, list) and len(value) > 3:
                        print(f"  {key}: {value[:3]}... ({len(value)} total)")
                    else:
                        print(f"  {key}: {value}")
        else:
            print("\nNo requirements found matching both conditions.")
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

