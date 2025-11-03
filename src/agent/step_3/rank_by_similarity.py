"""
Step 3: Rank Requirements by Similarity
Ranks filtered requirements from Step 2 based on semantic similarity to input entities.
Also retrieves all connected nodes (conditions, dependencies, etc.) for each requirement.
"""

import os
import numpy as np
from openai import OpenAI
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Neo4j configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')


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


def get_connected_nodes(requirement_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve all nodes connected to a requirement from Neo4j.
    
    Args:
        requirement_id: The ID of the requirement node
        
    Returns:
        Dictionary with node types as keys and lists of nodes as values
        Example: {
            'conditions': [{...}, {...}],
            'dependencies': [{...}],
            'other_nodes': [{...}]
        }
    """
    # Query uses elementId for exact matching (Neo4j internal ID)
    query = """
    MATCH (req:Requirement)
    WHERE elementId(req) = $req_id 
       OR req.id = $req_id 
       OR req._id = $req_id
       OR req.name = $req_id
    
    // Get all connected nodes with their relationships
    OPTIONAL MATCH (req)-[r]-(connected)
    WHERE connected IS NOT NULL
    
    RETURN 
        type(r) as relationship_type,
        labels(connected) as node_labels,
        connected,
        elementId(req) as matched_element_id
    """
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            result = session.run(query, req_id=requirement_id)
            
            connected_nodes = {
                'conditions': [],
                'dependencies': [],
                'related_requirements': [],
                'other_nodes': []
            }
            
            for record in result:
                if record['connected'] is None:
                    continue
                
                node = dict(record['connected'])
                labels = record['node_labels']
                rel_type = record['relationship_type']
                
                # Categorize by label
                if 'Condition' in labels:
                    connected_nodes['conditions'].append(node)
                elif 'Dependency' in labels or 'Dependencies' in labels:
                    connected_nodes['dependencies'].append(node)
                elif 'Requirement' in labels:
                    connected_nodes['related_requirements'].append(node)
                else:
                    connected_nodes['other_nodes'].append(node)
            
            return connected_nodes
    finally:
        driver.close()


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First embedding vector
        vec2: Second embedding vector
        
    Returns:
        Similarity score between 0 and 1 (1 = identical, 0 = completely different)
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    # Calculate cosine similarity
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    
    # Ensure result is between 0 and 1
    return float(max(0.0, min(1.0, similarity)))


def calculate_requirement_similarity(
    requirement: Dict[str, Any],
    entity_embeddings: List[List[float]],
    method: str = 'max'
) -> float:
    """
    Calculate how similar a requirement is to the input entities.
    
    Args:
        requirement: Requirement node (must have 'embedding' property)
        entity_embeddings: List of entity embedding vectors
        method: How to combine multiple entity similarities
                'max' = use highest similarity (default)
                'avg' = use average similarity
                
    Returns:
        Overall similarity score (0-1)
    """
    req_embedding = requirement.get('embedding')
    
    if not req_embedding:
        return 0.0
    
    # Calculate similarity to each entity
    similarities = []
    for entity_emb in entity_embeddings:
        sim = cosine_similarity(req_embedding, entity_emb)
        similarities.append(sim)
    
    # Combine similarities
    if method == 'max':
        # Use the highest similarity (most relevant entity)
        return max(similarities) if similarities else 0.0
    elif method == 'avg':
        # Use average similarity (overall relevance)
        return sum(similarities) / len(similarities) if similarities else 0.0
    else:
        return max(similarities) if similarities else 0.0


def rank_requirements_by_similarity(
    requirements: List[Dict[str, Any]],
    entities: List[str],
    top_n: int = None,
    method: str = 'max',
    include_connected_nodes: bool = True,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Rank requirements by similarity to input entities.
    
    This is the main Step 3 function.
    
    Args:
        requirements: List of requirement nodes from Step 2
        entities: List of entity texts from input document
        top_n: Return only top N requirements (None = return all)
        method: Similarity combination method ('max' or 'avg')
        include_connected_nodes: If True, fetch all connected nodes for each requirement
        verbose: Print progress
        
    Returns:
        List of requirements sorted by similarity (highest first),
        each with added 'similarity_score' field and 'connected_nodes' field
        (if include_connected_nodes=True)
        
    Example:
        >>> # From Step 2
        >>> requirements = hard_filter(compartments, entities)
        >>> 
        >>> # Step 3: Rank by similarity
        >>> ranked = rank_requirements_by_similarity(
        ...     requirements,
        ...     entities=["Appraisal Report", "Property Value"],
        ...     top_n=10,
        ...     include_connected_nodes=True
        ... )
        >>> 
        >>> # Top requirement with connected nodes
        >>> print(ranked[0]['name'])
        >>> print("Score:", ranked[0]['similarity_score'])
        >>> print("Conditions:", len(ranked[0]['connected_nodes']['conditions']))
    """
    if verbose:
        print("\n" + "="*70)
        print("STEP 3: RANK BY SIMILARITY")
        print("="*70)
        print(f"\nInput:")
        print(f"  Requirements: {len(requirements)}")
        print(f"  Entities: {entities}")
        print(f"  Method: {method} (how to combine entity similarities)")
    
    if not requirements:
        if verbose:
            print("\n⚠️  No requirements to rank")
        return []
    
    # Generate embeddings for entities
    if verbose:
        print(f"\n{'─'*70}")
        print("Generating entity embeddings...")
        print('─'*70)
    
    entity_embeddings = []
    for entity in entities:
        try:
            emb = get_entity_embedding(entity)
            entity_embeddings.append(emb)
            if verbose:
                print(f"  ✓ '{entity}' embedded")
        except Exception as e:
            if verbose:
                print(f"  ⚠️  Failed to embed '{entity}': {e}")
            continue
    
    if not entity_embeddings:
        if verbose:
            print("\n⚠️  No entity embeddings generated")
        return requirements
    
    # Calculate similarity scores
    if verbose:
        print(f"\n{'─'*70}")
        print("Calculating similarity scores...")
        print('─'*70)
    
    for req in requirements:
        similarity = calculate_requirement_similarity(
            req,
            entity_embeddings,
            method=method
        )
        req['similarity_score'] = similarity
    
    # Sort by similarity (highest first)
    ranked_requirements = sorted(
        requirements,
        key=lambda x: x.get('similarity_score', 0.0),
        reverse=True
    )
    
    # Limit to top N if specified
    if top_n:
        ranked_requirements = ranked_requirements[:top_n]
    
    if verbose:
        print(f"✓ Ranked {len(requirements)} requirements")
        print(f"\nTop 5 similarity scores:")
        for i, req in enumerate(ranked_requirements[:5], 1):
            score = req.get('similarity_score', 0.0)
            # Try different possible field names
            title = (req.get('title') or 
                    req.get('name') or 
                    req.get('Title') or 
                    req.get('description', '').split('.')[0] or  # First sentence
                    f"Requirement {req.get('id', i)}")
            print(f"  {i}. {title[:50]:50s} Score: {score:.3f}")
        
        if top_n:
            print(f"\n✓ Returning top {top_n} requirements")
    
    # Fetch connected nodes for each requirement
    if include_connected_nodes:
        if verbose:
            print(f"\n{'─'*70}")
            print("Fetching connected nodes (conditions, dependencies, etc.)...")
            print('─'*70)
        
        for req in ranked_requirements:
            # Use Neo4j element ID (from Step 2) - this is the internal Neo4j ID
            req_id = (req.get('_element_id') or  # Primary: Neo4j element ID
                     req.get('id') or 
                     req.get('_id') or 
                     req.get('elementId') or
                     req.get('name'))  # Fallback to name if no ID
            
            if verbose:
                name = req.get('name') or req.get('title') or 'Unknown'
                id_type = "_element_id" if req.get('_element_id') else "other"
                print(f"  Fetching nodes for '{name[:40]}' ({id_type}: {str(req_id)[:50]}...)")
            
            try:
                connected = get_connected_nodes(req_id)
                req['connected_nodes'] = connected
                
                if verbose:
                    total_connected = sum(len(nodes) for nodes in connected.values())
                    if total_connected > 0:
                        print(f"    ✓ Found {total_connected} connected node(s)")
                        for node_type, nodes in connected.items():
                            if nodes:
                                print(f"      - {node_type}: {len(nodes)}")
                    else:
                        print(f"    ⚠️  No connected nodes found")
            except Exception as e:
                if verbose:
                    print(f"    ❌ Error: {e}")
                req['connected_nodes'] = {
                    'conditions': [],
                    'dependencies': [],
                    'related_requirements': [],
                    'other_nodes': []
                }
    
    if verbose:
        print("\n" + "="*70)
        print(f"STEP 3 COMPLETE: {len(ranked_requirements)} ranked requirements")
        if include_connected_nodes:
            print("(with connected nodes included)")
        print("="*70)
    
    return ranked_requirements


# Example usage
if __name__ == "__main__":
    print("="*70)
    print("Step 3: Rank Requirements by Similarity")
    print("="*70)
    
    # Simulate Step 2 output
    example_requirements = [
        {
            'id': 'req_1',
            'title': 'Appraisal Report Required',
            'compartment': 'Loan & Property Information',
            'embedding': [0.1] * 3072  # Dummy embedding
        },
        {
            'id': 'req_2',
            'title': 'Property Value Documentation',
            'compartment': 'Loan & Property Information',
            'embedding': [0.2] * 3072  # Dummy embedding
        },
        {
            'id': 'req_3',
            'title': 'Tax Returns Verification',
            'compartment': 'Employment & Income',
            'embedding': [0.05] * 3072  # Dummy embedding
        }
    ]
    
    entities = ["Appraisal Report", "Property Value"]
    
    print(f"\nExample with {len(example_requirements)} requirements")
    print(f"Entities: {entities}")
    print("\nNote: This example uses dummy embeddings.")
    print("In production, requirements from Step 2 will have real embeddings.")
    
    # Uncomment to test with real API:
    # ranked = rank_requirements_by_similarity(
    #     example_requirements,
    #     entities,
    #     top_n=5,
    #     verbose=True
    # )

