"""
Simple Complete Pipeline Example: Step 1 → Step 2 → Step 3
Runs a single scenario showing the full workflow.
Saves output to JSON file for inspection.
"""

import sys
import json
from pathlib import Path
from typing import List
import numpy as np

# Add paths
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "step_1"))
sys.path.insert(0, str(parent_dir / "step_2"))
sys.path.insert(0, str(parent_dir / "step_3"))

from retrieve_document_categories import get_document_category
from hard_filter import hard_filter
from rank_by_similarity import rank_requirements_by_similarity


def convert_to_json_serializable(obj):
    """Convert numpy arrays and other non-serializable objects to JSON-compatible format."""
    # Handle Neo4j temporal types
    if hasattr(obj, 'iso_format'):  # Neo4j DateTime, Date, Time
        return obj.iso_format()
    elif hasattr(obj, '__class__') and obj.__class__.__name__ in ['DateTime', 'Date', 'Time', 'Duration']:
        return str(obj)
    # Handle numpy types
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    else:
        return obj


def run_complete_pipeline(
    document_name: str,
    document_entities: List[str],
    top_n: int = 10,
    similarity_threshold: float = 0.7
):
    """
    Run the complete deficiency detection pipeline.
    
    Args:
        document_name: Name of the document (for Step 1)
        document_entities: List of entities extracted from document
        top_n: Return top N requirements
        similarity_threshold: Threshold for Step 2 semantic search
        
    Returns:
        Top N ranked requirements
    """
    print("\n" + "="*70)
    print("COMPLETE PIPELINE: Steps 1 → 2 → 3")
    print("="*70)
    print(f"\nInput Document: '{document_name}'")
    print(f"Entities: {document_entities}")
    
    # ========== STEP 1: Get Compartment Labels ==========
    print("\n" + "█"*70)
    print("█ STEP 1: OBTAIN COMPARTMENT LABEL")
    print("█"*70)
    
    compartments = get_document_category(document_name)
    
    if not compartments:
        print(f"❌ No compartments found for '{document_name}'")
        return []
    
    print(f"\n✓ Found {len(compartments)} compartment(s):")
    for comp in compartments:
        print(f"  • {comp}")
    
    # ========== STEP 2: Hard Filter ==========
    print("\n" + "█"*70)
    print("█ STEP 2: HARD FILTER")
    print("█"*70)
    
    filtered_requirements = hard_filter(
        compartments=compartments,
        entities=document_entities,
        similarity_threshold=similarity_threshold,
        verbose=True
    )
    
    if not filtered_requirements:
        print("❌ No requirements found after filtering")
        return []
    
    # ========== STEP 3: Rank by Similarity ==========
    print("\n" + "█"*70)
    print("█ STEP 3: RANK BY SIMILARITY")
    print("█"*70)
    
    ranked_requirements = rank_requirements_by_similarity(
        filtered_requirements,
        entities=document_entities,
        top_n=top_n,
        method='max',
        include_connected_nodes=True,  # Fetch all connected nodes
        verbose=True
    )
    
    # ========== FINAL RESULTS ==========
    print("\n" + "="*70)
    print("PIPELINE COMPLETE!")
    print("="*70)
    print(f"\nFinal Output: Top {len(ranked_requirements)} Requirements")
    print("\nTop 5 (showing all fields + connected nodes):")
    for i, req in enumerate(ranked_requirements[:5], 1):
        print(f"\n{'─'*70}")
        print(f"Requirement {i}:")
        print('─'*70)
        
        # Display all fields except embedding, connected_nodes, and internal IDs
        for key, value in req.items():
            if key in ['embedding', 'vector', 'connected_nodes', '_element_id']:
                # Skip - _element_id is internal, connected_nodes shown separately
                continue
            
            # Format the output
            if isinstance(value, list):
                if len(value) > 5:
                    print(f"  {key}: {value[:5]}... ({len(value)} total)")
                else:
                    print(f"  {key}: {value}")
            elif isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                # Truncate very long strings
                value_str = str(value)
                if len(value_str) > 200:
                    print(f"  {key}: {value_str[:200]}...")
                else:
                    print(f"  {key}: {value}")
        
        # Display connected nodes
        if 'connected_nodes' in req:
            print(f"\n  {'─'*66}")
            print(f"  Connected Nodes:")
            print(f"  {'─'*66}")
            
            connected = req['connected_nodes']
            for node_type, nodes in connected.items():
                if nodes:
                    print(f"\n  {node_type.upper()} ({len(nodes)}):")
                    for j, node in enumerate(nodes[:3], 1):  # Show first 3 of each type
                        node_name = node.get('name') or node.get('title') or f"Node {j}"
                        print(f"    {j}. {node_name}")
                        # Show a few key fields
                        for k, v in list(node.items())[:3]:
                            if k not in ['embedding', 'vector']:
                                v_str = str(v)
                                if len(v_str) > 100:
                                    print(f"       {k}: {v_str[:100]}...")
                                else:
                                    print(f"       {k}: {v}")
                    
                    if len(nodes) > 3:
                        print(f"    ... and {len(nodes) - 3} more")
    
    return ranked_requirements


def save_output_to_json(
    ranked_requirements: List[Dict[str, Any]],
    output_file: str = "step3_sample_output.json"
):
    """
    Save Step 3 output to a JSON file.
    
    Args:
        ranked_requirements: Output from Step 3
        output_file: Path to save JSON file
    """
    # Prepare output structure
    output_data = {
        'metadata': {
            'total_requirements': len(ranked_requirements),
            'description': 'Step 3 output: Ranked requirements with similarity scores and connected nodes',
            'fields_per_requirement': [
                'All original requirement fields',
                'similarity_score (added by Step 3)',
                'connected_nodes (added by Step 3)'
            ]
        },
        'requirements': []
    }
    
    # Convert requirements to JSON-serializable format
    for req in ranked_requirements:
        req_clean = {}
        
        for key, value in req.items():
            # Skip embedding (too large) but keep everything else
            if key in ['embedding', 'vector']:
                req_clean[key] = f"<{len(value)}-dimensional vector omitted>"
            else:
                req_clean[key] = convert_to_json_serializable(value)
        
        output_data['requirements'].append(req_clean)
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n💾 Output saved to: {output_file}")
    print(f"   Total requirements: {len(ranked_requirements)}")
    
    # Show structure summary
    if ranked_requirements:
        sample = ranked_requirements[0]
        print(f"\n📋 Structure of each requirement:")
        print(f"   Main fields: {len(sample)} fields")
        if 'connected_nodes' in sample:
            for node_type, nodes in sample['connected_nodes'].items():
                if nodes:
                    print(f"   - {node_type}: {len(nodes)} node(s)")


if __name__ == "__main__":
    print("="*70)
    print("SIMPLE PIPELINE EXAMPLE")
    print("="*70)
    
    # Single scenario: Contractor Bid document
    document_name = "Contractor Bid"
    document_entities = ["Contractor Bid", "Repair Estimate", "Property Address"]
    
    print(f"\nScenario: Contractor Document")
    print(f"Document: {document_name}")
    print(f"Entities: {document_entities}")
    
    try:
        results = run_complete_pipeline(
            document_name=document_name,
            document_entities=document_entities,
            top_n=10,
            similarity_threshold=0.3
        )
        
        print(f"\n{'='*70}")
        print(f"✓ Pipeline completed successfully!")
        print(f"✓ Returned {len(results)} ranked requirements")
        print(f"{'='*70}")
        
        # Save output to JSON file
        save_output_to_json(results, output_file="step3_sample_output.json")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

