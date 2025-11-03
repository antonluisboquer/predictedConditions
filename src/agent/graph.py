"""
LangGraph-Based Complete Pipeline (Steps 1-7)
Provides orchestration, logging, tracing, and token tracking for each step.
"""

import sys
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Annotated
from typing_extensions import TypedDict
from datetime import datetime
from dotenv import load_dotenv

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Load environment variables
load_dotenv()

# Add all step directories to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "step_1"))
sys.path.insert(0, str(project_root / "step_2"))
sys.path.insert(0, str(project_root / "step_3"))
sys.path.insert(0, str(project_root / "step_4_5"))
sys.path.insert(0, str(project_root / "step_6_7"))

# Import step functions
from retrieve_document_categories import get_document_category
from hard_filter import hard_filter
from rank_by_similarity import rank_requirements_by_similarity
from llm_deficiency_detector import LLMDeficiencyDetector
from deficiency_scorer import DeficiencyScorer


# ============================================================================
# STATE DEFINITION
# ============================================================================

class PipelineState(TypedDict):
    """State that flows through the LangGraph pipeline."""
    
    # Execution metadata
    execution_id: str
    start_time: float
    
    # Input data
    input_file: str
    classification: str
    extracted_entities: Dict[str, Any]
    loan_program: str
    borrower_info: Dict[str, Any]
    
    # Step 1 outputs
    compartments: List[str]
    step1_latency: float
    
    # Step 2 outputs
    filtered_requirements: List[Dict[str, Any]]
    step2_latency: float
    
    # Step 3 outputs
    ranked_requirements: List[Dict[str, Any]]
    step3_latency: float
    step3_tokens: Dict[str, int]  # OpenAI embedding tokens
    
    # Step 4/5 outputs
    detection_results: Dict[str, Any]
    deficient_conditions: List[Dict[str, Any]]
    step4_5_latency: float
    step4_5_tokens: Dict[str, int]  # Anthropic tokens
    
    # Step 6/7 outputs
    final_results: Dict[str, Any]
    step6_7_latency: float
    step6_7_tokens: Dict[str, int]  # Anthropic tokens
    
    # Overall tracking
    total_latency: float
    total_tokens: Dict[str, Dict[str, int]]  # {model: {input: X, output: Y}}
    
    # Logging
    logs: List[Dict[str, Any]]
    
    # Configuration
    top_n: int
    verbose: bool
    conditions_csv_path: str


# ============================================================================
# LOGGING UTILITIES
# ============================================================================

def log_event(state: PipelineState, step: str, event_type: str, message: str, **kwargs):
    """Add a log entry to the state."""
    log_entry = {
        "execution_id": state.get("execution_id", "unknown"),
        "timestamp": datetime.now().isoformat(),
        "step": step,
        "event_type": event_type,
        "message": message,
        **kwargs
    }
    
    if "logs" not in state:
        state["logs"] = []
    
    state["logs"].append(log_entry)
    
    if state.get("verbose", True):
        print(f"[{step}] {event_type.upper()}: {message}")
    
    return state


# ============================================================================
# STEP 1: OBTAIN COMPARTMENT LABELS
# ============================================================================

def step1_get_compartments(state: PipelineState) -> PipelineState:
    """Step 1: Get compartment labels for the document."""
    # Initialize state fields if not present
    if "execution_id" not in state:
        state["execution_id"] = str(uuid.uuid4())
    if "start_time" not in state:
        state["start_time"] = time.time()
    if "logs" not in state:
        state["logs"] = []
    
    step_start = time.time()
    
    log_event(state, "STEP_1", "start", "Obtaining compartment labels")
    
    try:
        classification = state.get("classification", "")
        
        if not classification:
            log_event(state, "STEP_1", "warning", "No classification provided in input")
            state["compartments"] = []
            state["step1_latency"] = time.time() - step_start
            return state
        
        # Get compartments from classification
        compartments = get_document_category(classification)
        
        # Fallback: try first entity if no compartments found
        if not compartments:
            log_event(state, "STEP_1", "warning", f"No compartments for '{classification}', trying entities")
            
            # Extract entity keywords
            extracted_entities = state.get("extracted_entities", {})
            entity_keywords = list(extracted_entities.keys()) if extracted_entities else []
            if entity_keywords:
                compartments = get_document_category(entity_keywords[0])
        
        state["compartments"] = compartments or []
        state["step1_latency"] = time.time() - step_start
        
        log_event(
            state, "STEP_1", "complete", 
            f"Found {len(compartments)} compartment(s)",
            compartments=compartments,
            latency_ms=state["step1_latency"] * 1000
        )
        
    except Exception as e:
        log_event(state, "STEP_1", "error", str(e))
        state["compartments"] = []
        state["step1_latency"] = time.time() - step_start
    
    return state


# ============================================================================
# STEP 2: HARD FILTER
# ============================================================================

def step2_hard_filter(state: PipelineState) -> PipelineState:
    """Step 2: Filter requirements by compartment and entities."""
    step_start = time.time()
    
    log_event(state, "STEP_2", "start", "Filtering requirements")
    
    try:
        compartments = state["compartments"]
        
        if not compartments:
            log_event(state, "STEP_2", "skip", "No compartments, skipping hard filter")
            state["filtered_requirements"] = []
            state["step2_latency"] = time.time() - step_start
            return state
        
        # Extract entity keywords
        entity_keywords = _extract_entity_keywords(
            state["extracted_entities"], 
            state["classification"]
        )
        
        # Apply hard filter
        filtered_requirements = hard_filter(
            compartments=compartments,
            entities=entity_keywords,
            loan_program=state.get("loan_program"),
            similarity_threshold=0.3,
            verbose=state.get("verbose", False)
        )
        
        state["filtered_requirements"] = filtered_requirements
        state["step2_latency"] = time.time() - step_start
        
        log_event(
            state, "STEP_2", "complete",
            f"Filtered to {len(filtered_requirements)} requirements",
            count=len(filtered_requirements),
            latency_ms=state["step2_latency"] * 1000
        )
        
    except Exception as e:
        log_event(state, "STEP_2", "error", str(e))
        state["filtered_requirements"] = []
        state["step2_latency"] = time.time() - step_start
    
    return state


# ============================================================================
# STEP 3: RANK BY SIMILARITY
# ============================================================================

def step3_rank_requirements(state: PipelineState) -> PipelineState:
    """Step 3: Rank requirements by similarity to document entities."""
    step_start = time.time()
    
    log_event(state, "STEP_3", "start", "Ranking requirements by similarity")
    
    try:
        filtered_requirements = state["filtered_requirements"]
        
        if not filtered_requirements:
            log_event(state, "STEP_3", "skip", "No filtered requirements")
            state["ranked_requirements"] = []
            state["step3_latency"] = time.time() - step_start
            state["step3_tokens"] = {}
            return state
        
        # Extract entity keywords
        entity_keywords = _extract_entity_keywords(
            state["extracted_entities"],
            state["classification"]
        )
        
        # Rank requirements
        ranked_requirements = rank_requirements_by_similarity(
            requirements=filtered_requirements,
            entities=entity_keywords,
            top_n=5,  # Top 5 for context
            include_connected_nodes=True,
            verbose=state.get("verbose", False)
        )
        
        state["ranked_requirements"] = ranked_requirements
        state["step3_latency"] = time.time() - step_start
        
        # Track OpenAI embedding tokens (approximate)
        num_embeddings = len(entity_keywords) + len(filtered_requirements)
        estimated_tokens = num_embeddings * 50  # Rough estimate
        state["step3_tokens"] = {
            "model": "text-embedding-ada-002",
            "estimated_embedding_tokens": estimated_tokens
        }
        
        log_event(
            state, "STEP_3", "complete",
            f"Ranked top {len(ranked_requirements)} requirements",
            count=len(ranked_requirements),
            latency_ms=state["step3_latency"] * 1000,
            tokens=state["step3_tokens"]
        )
        
    except Exception as e:
        log_event(state, "STEP_3", "error", str(e))
        state["ranked_requirements"] = []
        state["step3_latency"] = time.time() - step_start
        state["step3_tokens"] = {}
    
    return state


# ============================================================================
# STEP 4/5: DEFICIENCY DETECTION
# ============================================================================

def step4_5_detect_deficiencies(state: PipelineState) -> PipelineState:
    """Step 4/5: Detect deficiencies using LLM."""
    step_start = time.time()
    
    log_event(state, "STEP_4_5", "start", "Detecting deficiencies with LLM")
    
    try:
        # Get conditions CSV path, default to project root
        conditions_csv_path = state.get(
            "conditions_csv_path",
            str(project_root / "merged_conditions_with_related_docs__FULL_filtered_simple.csv")
        )
        
        # Initialize detector
        detector = LLMDeficiencyDetector(
            conditions_csv_path=conditions_csv_path
        )
        
        # Filter conditions by classification
        extracted_entities = state.get("extracted_entities", {})
        document_fields = list(extracted_entities.keys()) if extracted_entities else []
        classification = state.get("classification", "")
        
        filtered_conditions = detector.filter_by_classification(
            classification=classification,
            document_fields=document_fields,
            loan_program=state.get("loan_program")
        )
        
        condition_ids = filtered_conditions['Title'].tolist()
        
        # Limit for cost efficiency
        if len(condition_ids) > 100:
            condition_ids = condition_ids[:100]
            log_event(state, "STEP_4_5", "info", f"Limited to 100 conditions for efficiency")
        
        if not condition_ids:
            log_event(state, "STEP_4_5", "warning", "No conditions found")
            state["detection_results"] = {"results": []}
            state["deficient_conditions"] = []
            state["step4_5_latency"] = time.time() - step_start
            state["step4_5_tokens"] = {}
            return state
        
        log_event(state, "STEP_4_5", "info", f"Checking {len(condition_ids)} conditions")
        
        # Check document
        detection_results = detector.check_document(
            document_data=extracted_entities,
            condition_ids=condition_ids,
            additional_context=state.get("ranked_requirements"),
            loan_program=state.get("loan_program"),
            borrower_info=state.get("borrower_info", {})
        )
        
        # Extract deficient conditions
        deficient_conditions = [
            r for r in detection_results.get('results', [])
            if r.get('status') == 'deficient'
        ]
        
        state["detection_results"] = detection_results
        state["deficient_conditions"] = deficient_conditions
        state["step4_5_latency"] = time.time() - step_start
        
        # Extract token usage from metadata
        metadata = detection_results.get('_metadata', {})
        state["step4_5_tokens"] = {
            "model": metadata.get('model', 'unknown'),
            "input_tokens": metadata.get('input_tokens', 0),
            "output_tokens": metadata.get('output_tokens', 0),
            "cache_read_tokens": metadata.get('cache_read_tokens', 0),
            "cache_creation_tokens": metadata.get('cache_creation_tokens', 0),
            "total_tokens": metadata.get('input_tokens', 0) + metadata.get('output_tokens', 0)
        }
        
        log_event(
            state, "STEP_4_5", "complete",
            f"Found {len(deficient_conditions)} deficiencies",
            total_checked=len(detection_results.get('results', [])),
            deficiencies_found=len(deficient_conditions),
            latency_ms=state["step4_5_latency"] * 1000,
            tokens=state["step4_5_tokens"]
        )
        
    except Exception as e:
        log_event(state, "STEP_4_5", "error", str(e))
        state["detection_results"] = {"results": []}
        state["deficient_conditions"] = []
        state["step4_5_latency"] = time.time() - step_start
        state["step4_5_tokens"] = {}
    
    return state


# ============================================================================
# STEP 6/7: SCORING & RANKING
# ============================================================================

def step6_7_score_deficiencies(state: PipelineState) -> PipelineState:
    """Step 6/7: Score and rank deficiencies."""
    step_start = time.time()
    
    log_event(state, "STEP_6_7", "start", "Scoring and ranking deficiencies")
    
    try:
        deficient_conditions = state["deficient_conditions"]
        
        if not deficient_conditions:
            log_event(state, "STEP_6_7", "skip", "No deficiencies to score")
            state["final_results"] = {
                "top_n": [],
                "scored_deficiencies": [],
                "summary": {"total_deficiencies_evaluated": 0}
            }
            state["step6_7_latency"] = time.time() - step_start
            state["step6_7_tokens"] = {}
            return state
        
        # Initialize scorer
        scorer = DeficiencyScorer(
            config_path=str(project_root / "step_6_7" / "scoring_config.json")
        )
        
        # Score deficiencies
        final_results = scorer.score_deficiencies(
            detection_results=state["detection_results"],
            top_n=state.get("top_n", 10),
            verbose=state.get("verbose", False)
        )
        
        state["final_results"] = final_results
        state["step6_7_latency"] = time.time() - step_start
        
        # Extract token usage (if scorer uses LLM)
        metadata = final_results.get('_metadata', {})
        state["step6_7_tokens"] = {
            "model": metadata.get('model', 'claude-sonnet-4-5'),
            "input_tokens": metadata.get('input_tokens', 0),
            "output_tokens": metadata.get('output_tokens', 0),
            "cache_read_tokens": metadata.get('cache_read_tokens', 0),
            "total_tokens": metadata.get('input_tokens', 0) + metadata.get('output_tokens', 0)
        }
        
        log_event(
            state, "STEP_6_7", "complete",
            f"Scored {len(final_results.get('top_n', []))} top deficiencies",
            total_scored=len(final_results.get('scored_deficiencies', [])),
            top_n=len(final_results.get('top_n', [])),
            latency_ms=state["step6_7_latency"] * 1000,
            tokens=state["step6_7_tokens"]
        )
        
    except Exception as e:
        log_event(state, "STEP_6_7", "error", str(e))
        state["final_results"] = {"top_n": [], "scored_deficiencies": []}
        state["step6_7_latency"] = time.time() - step_start
        state["step6_7_tokens"] = {}
    
    return state


# ============================================================================
# FINALIZATION
# ============================================================================

def finalize_pipeline(state: PipelineState) -> PipelineState:
    """Finalize the pipeline by calculating total metrics."""
    
    # Calculate total latency
    start_time = state.get("start_time", time.time())
    state["total_latency"] = time.time() - start_time
    
    # Aggregate all token usage
    state["total_tokens"] = {
        "step_3_embeddings": state.get("step3_tokens", {}),
        "step_4_5_detection": state.get("step4_5_tokens", {}),
        "step_6_7_scoring": state.get("step6_7_tokens", {})
    }
    
    # Calculate grand total
    total_input = 0
    total_output = 0
    
    for step_name, tokens in state["total_tokens"].items():
        total_input += tokens.get("input_tokens", 0)
        total_output += tokens.get("output_tokens", 0)
    
    state["total_tokens"]["grand_total"] = {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_input + total_output
    }
    
    log_event(
        state, "FINALIZE", "complete",
        "Pipeline execution finished",
        total_latency_s=state["total_latency"],
        total_latency_ms=state["total_latency"] * 1000,
        total_tokens=state["total_tokens"]["grand_total"]
    )
    
    return state


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _extract_entity_keywords(extracted_entities: Dict[str, Any], classification: str) -> List[str]:
    """Extract entity keywords from document data."""
    entities = []
    
    if classification:
        entities.append(classification)
    
    # Recursively extract field names
    def extract_fields(data, prefix=""):
        fields = []
        if isinstance(data, dict):
            for key, value in data.items():
                field_name = f"{prefix}.{key}" if prefix else key
                fields.append(field_name)
                if isinstance(value, dict):
                    fields.extend(extract_fields(value, field_name))
                elif isinstance(value, str) and value.strip():
                    fields.append(value.strip())
        return fields
    
    if extracted_entities:
        entities.extend(extract_fields(extracted_entities))
    
    return list(set([e for e in entities if e and str(e).strip()]))


# ============================================================================
# LANGGRAPH WORKFLOW
# ============================================================================

def create_pipeline_graph() -> StateGraph:
    """Create the LangGraph workflow for the complete pipeline."""
    
    # Create graph
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("step1_compartments", step1_get_compartments)
    workflow.add_node("step2_hard_filter", step2_hard_filter)
    workflow.add_node("step3_rank_requirements", step3_rank_requirements)
    workflow.add_node("step4_5_detect_deficiencies", step4_5_detect_deficiencies)
    workflow.add_node("step6_7_score_deficiencies", step6_7_score_deficiencies)
    workflow.add_node("finalize", finalize_pipeline)
    
    # Define edges (linear flow)
    workflow.set_entry_point("step1_compartments")
    workflow.add_edge("step1_compartments", "step2_hard_filter")
    workflow.add_edge("step2_hard_filter", "step3_rank_requirements")
    workflow.add_edge("step3_rank_requirements", "step4_5_detect_deficiencies")
    workflow.add_edge("step4_5_detect_deficiencies", "step6_7_score_deficiencies")
    workflow.add_edge("step6_7_score_deficiencies", "finalize")
    workflow.add_edge("finalize", END)
    
    return workflow.compile()


# ============================================================================
# MAIN EXECUTION FUNCTION
# ============================================================================

def run_pipeline_with_langgraph(
    input_file: str,
    output_file: str = "step7_final_output.json",
    top_n: int = 10,
    verbose: bool = True,
    conditions_csv: str = None
) -> Dict[str, Any]:
    """
    Run the complete pipeline using LangGraph.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to save final output
        top_n: Number of top deficiencies to return
        verbose: Print progress
        conditions_csv: Path to conditions CSV
        
    Returns:
        Final results with execution metadata
    """
    
    # Set default paths
    if conditions_csv is None:
        conditions_csv = str(project_root / "merged_conditions_with_related_docs__FULL_filtered_simple.csv")
    
    # Load input
    input_path = Path(input_file)
    if not input_path.is_absolute():
        if not input_path.exists():
            input_path = project_root / input_file
    
    with open(input_path, 'r') as f:
        input_data = json.load(f)
    
    # Extract input fields
    indexing_output = input_data.get('indexing_output', {})
    classification = indexing_output.get('classification', input_data.get('classification', ''))
    extracted_entities = indexing_output.get('extracted_entities', input_data.get('extracted_entities', {}))
    loan_program = input_data.get('loan_program', '')
    borrower_info = input_data.get('borrower_info', {})
    
    # Initialize state
    initial_state: PipelineState = {
        "execution_id": str(uuid.uuid4()),
        "start_time": time.time(),
        "input_file": str(input_path),
        "classification": classification,
        "extracted_entities": extracted_entities,
        "loan_program": loan_program,
        "borrower_info": borrower_info,
        "compartments": [],
        "filtered_requirements": [],
        "ranked_requirements": [],
        "detection_results": {},
        "deficient_conditions": [],
        "final_results": {},
        "step1_latency": 0.0,
        "step2_latency": 0.0,
        "step3_latency": 0.0,
        "step4_5_latency": 0.0,
        "step6_7_latency": 0.0,
        "step3_tokens": {},
        "step4_5_tokens": {},
        "step6_7_tokens": {},
        "total_latency": 0.0,
        "total_tokens": {},
        "logs": [],
        "top_n": top_n,
        "verbose": verbose,
        "conditions_csv_path": conditions_csv
    }
    
    if verbose:
        print("\n" + "="*70)
        print("🔷 LANGGRAPH PIPELINE: STEPS 1-7")
        print("="*70)
        print(f"Execution ID: {initial_state['execution_id']}")
        print(f"Classification: {classification}")
        if loan_program:
            print(f"Loan Program: {loan_program}")
        if borrower_info:
            name = f"{borrower_info.get('first_name', '')} {borrower_info.get('last_name', '')}".strip()
            if name:
                print(f"Borrower: {name}")
        print("="*70 + "\n")
    
    # Create and run graph
    graph = create_pipeline_graph()
    final_state = graph.invoke(initial_state)
    
    # Save results
    output_data = {
        "execution_metadata": {
            "execution_id": final_state["execution_id"],
            "total_latency_seconds": final_state["total_latency"],
            "input_file": final_state["input_file"],
            "timestamp": datetime.now().isoformat()
        },
        "step_metrics": {
            "step_1": {"latency_ms": final_state["step1_latency"] * 1000},
            "step_2": {"latency_ms": final_state["step2_latency"] * 1000},
            "step_3": {
                "latency_ms": final_state["step3_latency"] * 1000,
                "tokens": final_state.get("step3_tokens", {})
            },
            "step_4_5": {
                "latency_ms": final_state["step4_5_latency"] * 1000,
                "tokens": final_state.get("step4_5_tokens", {})
            },
            "step_6_7": {
                "latency_ms": final_state["step6_7_latency"] * 1000,
                "tokens": final_state.get("step6_7_tokens", {})
            }
        },
        "total_tokens": final_state.get("total_tokens", {}),
        "results": final_state.get("final_results", {}),
        "logs": final_state.get("logs", [])
    }
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    if verbose:
        print("\n" + "="*70)
        print("✅ PIPELINE COMPLETE")
        print("="*70)
        print(f"Total Latency: {final_state['total_latency']:.2f}s")
        print(f"Deficiencies Found: {len(final_state.get('final_results', {}).get('top_n', []))}")
        print(f"Output saved to: {output_file}")
        
        # Print token usage
        total_tokens_info = final_state.get("total_tokens", {}).get("grand_total", {})
        if total_tokens_info:
            print(f"\n📊 Token Usage:")
            print(f"  Total Input Tokens: {total_tokens_info.get('total_input_tokens', 0):,}")
            print(f"  Total Output Tokens: {total_tokens_info.get('total_output_tokens', 0):,}")
            print(f"  Grand Total: {total_tokens_info.get('total_tokens', 0):,}")
        
        print("="*70 + "\n")
    
    return output_data


# ============================================================================
# GRAPH EXPORT (for LangGraph deployment)
# ============================================================================

# Define the compiled graph for deployment
graph = create_pipeline_graph()


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run LangGraph pipeline')
    parser.add_argument('input_file', nargs='?', default='sample_doc_input.json')
    parser.add_argument('-o', '--output', default=None)
    parser.add_argument('-n', '--top-n', type=int, default=10)
    parser.add_argument('-q', '--quiet', action='store_true')
    
    args = parser.parse_args()
    
    if args.output is None:
        input_name = Path(args.input_file).stem
        args.output = f"langgraph_output_{input_name}.json"
    
    try:
        results = run_pipeline_with_langgraph(
            input_file=args.input_file,
            output_file=args.output,
            top_n=args.top_n,
            verbose=not args.quiet
        )
        
        print(f"\n✓ Success! Results saved to: {args.output}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
