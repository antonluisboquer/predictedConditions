"""
Step 2 Enhanced: Semantic Entity Filtering using Embeddings
Uses vector similarity search to find nodes related to entities,
then retrieves their connected Requirement nodes.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from openai import OpenAI

# Load environment variables
load_dotenv()

# Neo4j connection configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def get_entity_embedding(entity_text: str) -> List[float]:
    """
    Generate embedding for an entity using OpenAI.
    
    Args:
        entity_text: The entity text to embed
        
    Returns:
        Embedding vector as list of floats
    """
    if not openai_client:
        raise ValueError("OpenAI API key not configured")
    
    response = openai_client.embeddings.create(
        input=entity_text,
        model="text-embedding-3-large"
    )
    return response.data[0].embedding


def semantic_search_nodes_by_entity(
    entity_text: str,
    top_k: int = 10,
    similarity_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Perform semantic search to find nodes similar to the entity.
    
    Uses vector similarity search in Neo4j to find the closest nodes
    based on embedding similarity.
    
    Args:
        entity_text: The entity text to search for
        top_k: Number of top similar nodes to return
        similarity_threshold: Minimum similarity score (0-1)
        
    Returns:
        List of similar nodes with their similarity scores
    """
    # Get embedding for the entity
    entity_embedding = get_entity_embedding(entity_text)
    
    # Neo4j vector similarity search
    # Note: Assumes nodes have an 'embedding' property
    query = """
    MATCH (n)
    WHERE n.embedding IS NOT NULL
    WITH n, 
         gds.similarity.cosine(n.embedding, $entity_embedding) AS similarity
    WHERE similarity >= $threshold
    RETURN n, similarity
    ORDER BY similarity DESC
    LIMIT $top_k
    """
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            result = session.run(
                query,
                entity_embedding=entity_embedding,
                threshold=similarity_threshold,
                top_k=top_k
            )
            
            nodes = []
            for record in result:
                node_data = dict(record['n'])
                node_data['similarity_score'] = record['similarity']
                nodes.append(node_data)
            
            return nodes
    finally:
        driver.close()


def get_requirements_from_nodes(node_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Get Requirement nodes that are connected to the given nodes.
    
    Traverses relationships from various node types to their parent
    Requirement nodes.
    
    Args:
        node_ids: List of node IDs to find requirements for
        
    Returns:
        List of unique Requirement nodes
    """
    query = """
    MATCH (n)
    WHERE elementId(n) IN $node_ids
    MATCH (n)-[*1..2]-(req:Requirement)
    RETURN DISTINCT req
    """
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            result = session.run(query, node_ids=node_ids)
            
            requirements = []
            for record in result:
                req_node = record['req']
                requirements.append(dict(req_node))
            
            return requirements
    finally:
        driver.close()


def get_requirements_by_entity_semantic_search(
    entities: List[str],
    top_k_per_entity: int = 5,
    similarity_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Find Requirement nodes via semantic search of entities.
    
    Process:
    1. For each entity, generate embedding
    2. Find top-k most similar nodes in the database
    3. Traverse from those nodes to their Requirement nodes
    4. Collate all Requirement nodes
    
    Args:
        entities: List of entity texts from the input document
        top_k_per_entity: How many similar nodes to find per entity
        similarity_threshold: Minimum similarity score
        
    Returns:
        List of unique Requirement nodes found via entity similarity
    """
    all_requirements = []
    seen_req_ids = set()
    
    for entity in entities:
        print(f"  Searching for entity: '{entity}'...")
        
        # Find similar nodes
        similar_nodes = semantic_search_nodes_by_entity(
            entity,
            top_k=top_k_per_entity,
            similarity_threshold=similarity_threshold
        )
        
        if not similar_nodes:
            print(f"    No similar nodes found")
            continue
        
        print(f"    Found {len(similar_nodes)} similar nodes")
        
        # Get node IDs
        node_ids = [node.get('id') or str(node) for node in similar_nodes]
        
        # Get connected Requirement nodes
        requirements = get_requirements_from_nodes(node_ids)
        
        print(f"    → {len(requirements)} requirement(s) found")
        
        # Add unique requirements
        for req in requirements:
            req_id = req.get('id') or str(req)
            if req_id not in seen_req_ids:
                seen_req_ids.add(req_id)
                all_requirements.append(req)
    
    return all_requirements


def filter_requirements_combined(
    compartment_labels: List[str],
    entities: Optional[List[str]] = None,
    use_semantic_search: bool = True,
    combine_method: str = 'intersection'
) -> List[Dict[str, Any]]:
    """
    Combined filtering: Compartment matching + Entity semantic search.
    
    Two filtering paths:
    - Path A: Requirements matching compartment labels (exact match)
    - Path B: Requirements found via entity semantic search (embeddings)
    
    Args:
        compartment_labels: List of compartment labels from Step 1
        entities: List of entity texts from input document
        use_semantic_search: If True, use embeddings; if False, use keyword match
        combine_method: 'intersection' (AND) or 'union' (OR)
        
    Returns:
        List of Requirement nodes based on combine_method
        
    Example:
        >>> # Get requirements that match BOTH compartment AND entities
        >>> reqs = filter_requirements_combined(
        ...     compartment_labels=["Loan & Property Information"],
        ...     entities=["Appraisal Report", "Property Value"],
        ...     combine_method='intersection'
        ... )
    """
    from filter_requirements_by_compartment import filter_requirements_multiple_compartments
    
    print(f"\n{'─'*70}")
    print("Combined Filtering (Compartment + Entity Semantic Search)")
    print('─'*70)
    
    # Path A: Get requirements by compartment
    print("\nPath A: Filtering by compartment labels...")
    print(f"Compartments: {compartment_labels}")
    reqs_by_compartment = filter_requirements_multiple_compartments(compartment_labels)
    print(f"✓ Found {len(reqs_by_compartment)} requirement(s) by compartment")
    
    # If no entities provided, return compartment results only
    if not entities:
        return reqs_by_compartment
    
    # Path B: Get requirements by entity semantic search
    print("\nPath B: Filtering by entity semantic search...")
    print(f"Entities: {entities}")
    
    if use_semantic_search:
        reqs_by_entities = get_requirements_by_entity_semantic_search(entities)
        print(f"✓ Found {len(reqs_by_entities)} requirement(s) by semantic search")
    else:
        # Fallback to keyword matching
        reqs_by_entities = filter_requirements_multiple_compartments(
            compartment_labels,
            entities=entities
        )
        print(f"✓ Found {len(reqs_by_entities)} requirement(s) by keyword match")
    
    # Combine results
    print(f"\nCombining results using '{combine_method}' method...")
    
    if combine_method == 'intersection':
        # Requirements must be in BOTH sets (AND logic)
        reqs_comp_ids = {req.get('id') or str(req) for req in reqs_by_compartment}
        
        combined = []
        for req in reqs_by_entities:
            req_id = req.get('id') or str(req)
            if req_id in reqs_comp_ids:
                combined.append(req)
        
        print(f"✓ {len(combined)} requirement(s) match BOTH compartment AND entities")
        return combined
    
    else:  # union
        # Requirements in EITHER set (OR logic)
        seen_ids = set()
        combined = []
        
        for req in reqs_by_compartment + reqs_by_entities:
            req_id = req.get('id') or str(req)
            if req_id not in seen_ids:
                seen_ids.add(req_id)
                combined.append(req)
        
        print(f"✓ {len(combined)} unique requirement(s) match compartment OR entities")
        return combined


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("Step 2 Enhanced: Semantic Entity Filtering")
    print("=" * 70)
    
    # Example: Complete workflow with semantic search
    compartments = ["Loan & Property Information"]
    entities = ["Appraisal Report", "Property Valuation"]
    
    print(f"\nInput:")
    print(f"  Compartments: {compartments}")
    print(f"  Entities: {entities}")
    
    try:
        # Method 1: Intersection (requirements must match BOTH)
        requirements = filter_requirements_combined(
            compartment_labels=compartments,
            entities=entities,
            use_semantic_search=True,
            combine_method='intersection'
        )
        
        print(f"\n{'='*70}")
        print("Results:")
        print(f"  Found {len(requirements)} requirement(s)")
        
        # Show sample
        if requirements:
            print("\nSample requirement:")
            req = requirements[0]
            for key, value in req.items():
                if key not in ['embedding', 'vector']:
                    if isinstance(value, list) and len(value) > 3:
                        print(f"  {key}: {value[:3]}... ({len(value)} total)")
                    else:
                        print(f"  {key}: {value}")
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

