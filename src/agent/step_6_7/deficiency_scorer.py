"""
Deficiency Scorer - Main Orchestrator

Combines empirical detection confidence with LLM-based priority scoring
to rank and return top N deficiencies.
"""

import json
import os
import re
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

from confidence_calculator import calculate_detection_confidence, load_config
from priority_evaluator import evaluate_priority


def extract_relevant_documents(actionable_instruction: str, related_documents: str) -> str:
    """
    Extract relevant documents from related_documents based on keywords in actionable_instruction.
    
    Args:
        actionable_instruction: The actionable instruction text (e.g., "Provide K-1 or CPA letter")
        related_documents: Comma-separated list of related documents
        
    Returns:
        Filtered comma-separated list of documents that match the instruction
    """
    if not actionable_instruction or not related_documents:
        return related_documents
    
    # Handle special metadata markers that indicate universal conditions
    related_lower = related_documents.lower().strip()
    if related_lower in ['all docs pass through', 'all documents', 'all docs', 'universal']:
        # For universal conditions, extract document type from actionable instruction
        # e.g., "Upload bank statements" -> "Bank Statement"
        instruction_lower = actionable_instruction.lower()
        
        # Map common instruction keywords to document types
        doc_type_mapping = {
            'bank statement': 'Business Bank Statement, Personal Bank Statement',
            'tax return': '1040 Personal Tax Return, 1120 Corporate Tax Return, Form 1120S Scorp, Form 1065',
            'paystub': 'Paystub, Pay Stub',
            'w-2': 'W-2 Form, W2',
            'cpa letter': 'CPA Letter for Self-Employment, CPA Letter for Use of Business Funds',
            'profit and loss': 'Profit and Loss Statement, P&L Statement',
            'balance sheet': 'Balance Sheet',
            'credit report': 'Credit Report',
            'appraisal': 'Appraisal Report',
            'title': 'Title Report, Preliminary Title',
        }
        
        # Find matching document types
        for keyword, doc_types in doc_type_mapping.items():
            if keyword in instruction_lower:
                return doc_types
        
        # If no specific mapping found, return a generic indicator
        return 'See actionable instruction for required documents'
    
    # Parse related documents
    docs_list = [doc.strip() for doc in related_documents.split(',')]
    
    # Extract keywords from actionable instruction
    # Remove common words and focus on document-type keywords
    instruction_lower = actionable_instruction.lower()
    
    # Common document type keywords to look for
    keywords = []
    
    # Extract specific document mentions
    # Pattern: look for capitalized words, numbers, and common doc terms
    potential_keywords = re.findall(r'\b[A-Z0-9][A-Za-z0-9\-]*\b', actionable_instruction)
    keywords.extend([kw.lower() for kw in potential_keywords])
    
    # Add common document type words from instruction
    doc_types = ['tax', 'return', 'letter', 'cpa', 'k-1', 'k1', 'schedule', 'form', 
                 'statement', 'report', 'agreement', 'certificate', 'paystub', 'w-2', 'w2',
                 '1099', '1040', '1065', '1120', 'articles', 'operating', 'partnership',
                 'incorporation', 'organization', 'bank', 'credit', 'proof', 'verification']
    
    for doc_type in doc_types:
        if doc_type in instruction_lower:
            keywords.append(doc_type)
    
    # Filter documents that contain any of the keywords
    relevant_docs = []
    for doc in docs_list:
        doc_lower = doc.lower()
        if any(keyword in doc_lower for keyword in keywords):
            relevant_docs.append(doc)
    
    # If no matches found, return original list
    if not relevant_docs:
        return related_documents
    
    return ', '.join(relevant_docs)


class DeficiencyScorer:
    """
    Main class for scoring deficiencies from Step 4/5 detection results.
    
    Calculates:
    - Detection confidence (empirical, based on evidence quality)
    - Priority score (LLM-based, for ranking)
    
    Returns top N deficiencies sorted by priority score.
    """
    
    def __init__(
        self,
        config_path: str = "scoring_config.json",
        api_key: Optional[str] = None,
        model: str = "claude-haiku-4-5-20251001"  # Optimized: Haiku is 3-5x faster than Sonnet
    ):
        """
        Initialize the scorer.
        
        Args:
            config_path: Path to scoring configuration JSON
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use for priority evaluation
        """
        self.config = load_config(config_path)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or parameters")
        
        self.client = Anthropic(api_key=self.api_key)
        print(f"✓ DeficiencyScorer initialized with model: {self.model}")
    
    def score_deficiencies(
        self,
        detection_results: Dict[str, Any],
        top_n: int = 10,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Score all deficiencies and return top N by priority.
        
        Args:
            detection_results: Results dict from step_4_5 (or path to JSON file)
            top_n: Number of top deficiencies to return
            verbose: Print progress messages
            
        Returns:
            Dict with scored deficiencies, top N, and summary stats
        """
        # Load detection results if path provided
        if isinstance(detection_results, str):
            with open(detection_results, 'r') as f:
                detection_results = json.load(f)
        
        # Filter to deficient status only
        all_results = detection_results.get("results", [])
        deficient_results = [r for r in all_results if r.get("status") == "deficient"]
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"SCORING {len(deficient_results)} DEFICIENCIES")
            print(f"{'='*80}\n")
        
        if not deficient_results:
            print("⚠ No deficient results found to score")
            return {
                "scored_deficiencies": [],
                "top_n": [],
                "summary": {
                    "total_deficiencies_evaluated": 0,
                    "average_detection_confidence": 0,
                    "average_priority_score": 0,
                    "high_priority_count": 0,
                    "medium_priority_count": 0,
                    "low_priority_count": 0
                }
            }
        
        # Score each deficiency
        scored_deficiencies = []
        for i, result in enumerate(deficient_results, 1):
            if verbose:
                print(f"[{i}/{len(deficient_results)}] Scoring: {result.get('condition_id', 'Unknown')[:60]}...")
            
            scored = self.score_single_deficiency(result, verbose=False)
            scored_deficiencies.append(scored)
        
        # Sort by priority score (descending)
        scored_deficiencies.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Get top N
        top_n_results = scored_deficiencies[:top_n]
        
        # Calculate summary stats
        summary = self._calculate_summary(scored_deficiencies)
        
        if verbose:
            print(f"\n{'='*80}")
            print("SCORING COMPLETE")
            print(f"{'='*80}\n")
            self._print_summary(summary, top_n)
        
        return {
            "scored_deficiencies": scored_deficiencies,
            "top_n": top_n_results,
            "summary": summary,
            "_metadata": detection_results.get("_metadata", {})
        }
    
    def score_single_deficiency(
        self,
        deficiency_result: Dict[str, Any],
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Score a single deficiency.
        
        Args:
            deficiency_result: Single result from step_4_5 detection
            verbose: Print detailed scoring info
            
        Returns:
            Dict with detection confidence, priority score, and original data
        """
        # Calculate empirical detection confidence
        confidence_result = calculate_detection_confidence(deficiency_result, self.config)
        detection_confidence = confidence_result["overall"]
        confidence_breakdown = confidence_result["breakdown"]
        
        if verbose:
            print(f"\n  Detection Confidence: {detection_confidence:.3f}")
            for key, value in confidence_breakdown.items():
                print(f"    - {key}: {value:.3f}")
        
        # Evaluate priority using LLM
        priority_result = evaluate_priority(
            deficiency_result,
            detection_confidence,
            self.api_key,
            self.config,
            self.model
        )
        
        priority_score = priority_result["overall_priority"]
        
        if verbose:
            print(f"  Priority Score: {priority_score:.3f}")
            print(f"    - Severity: {priority_result['severity']:.3f}")
            print(f"    - Impact: {priority_result['impact']:.3f}")
            print(f"    - Urgency: {priority_result['urgency']:.3f}")
            print(f"    - Complexity: {priority_result['complexity']:.3f}")
            print(f"  Explanation: {priority_result.get('explanation', '')[:80]}...")
        
        # Extract actionable documents from related documents
        related_docs = deficiency_result.get("related_documents", "")
        actionable_inst = deficiency_result.get("actionable_instruction", "")
        actionable_docs = extract_relevant_documents(actionable_inst, related_docs)
        
        # Combine into output format
        return {
            "condition_id": deficiency_result.get("condition_id", ""),
            "status": deficiency_result.get("status", "deficient"),
            "detection_confidence": detection_confidence,
            "confidence_breakdown": confidence_breakdown,
            "priority_score": priority_score,
            "priority_dimensions": {
                "severity": priority_result["severity"],
                "impact": priority_result["impact"],
                "urgency": priority_result["urgency"],
                "complexity": priority_result["complexity"],
                "explanation": priority_result.get("explanation", "")
            },
            "related_documents": related_docs,
            "actionable_documents": actionable_docs,
            "actionable_instruction": actionable_inst,
            "documents_checked": deficiency_result.get("documents_checked", []),
            "satisfied_by": deficiency_result.get("satisfied_by"),
            "original_deficiency": deficiency_result
        }
    
    def _calculate_summary(self, scored_deficiencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if not scored_deficiencies:
            return {
                "total_deficiencies_evaluated": 0,
                "average_detection_confidence": 0,
                "average_priority_score": 0,
                "high_priority_count": 0,
                "medium_priority_count": 0,
                "low_priority_count": 0
            }
        
        total = len(scored_deficiencies)
        avg_confidence = sum(d["detection_confidence"] for d in scored_deficiencies) / total
        avg_priority = sum(d["priority_score"] for d in scored_deficiencies) / total
        
        # Count by priority level
        high_count = sum(1 for d in scored_deficiencies if d["priority_score"] >= 0.7)
        medium_count = sum(1 for d in scored_deficiencies if 0.4 <= d["priority_score"] < 0.7)
        low_count = sum(1 for d in scored_deficiencies if d["priority_score"] < 0.4)
        
        return {
            "total_deficiencies_evaluated": total,
            "average_detection_confidence": round(avg_confidence, 3),
            "average_priority_score": round(avg_priority, 3),
            "high_priority_count": high_count,
            "medium_priority_count": medium_count,
            "low_priority_count": low_count
        }
    
    def _print_summary(self, summary: Dict[str, Any], top_n: int):
        """Print summary statistics."""
        print(f"Total Deficiencies Evaluated: {summary['total_deficiencies_evaluated']}")
        print(f"Average Detection Confidence: {summary['average_detection_confidence']:.3f}")
        print(f"Average Priority Score: {summary['average_priority_score']:.3f}")
        print(f"\nPriority Distribution:")
        print(f"  🔴 High Priority (≥0.7): {summary['high_priority_count']}")
        print(f"  🟡 Medium Priority (0.4-0.7): {summary['medium_priority_count']}")
        print(f"  🟢 Low Priority (<0.4): {summary['low_priority_count']}")
        print(f"\nReturning top {top_n} deficiencies by priority score")


def format_results_summary(results: Dict[str, Any]) -> str:
    """Format scored results into a human-readable summary."""
    
    summary_text = "=" * 80 + "\n"
    summary_text += "TOP PRIORITY DEFICIENCIES\n"
    summary_text += "=" * 80 + "\n\n"
    
    top_n = results.get("top_n", [])
    
    for i, result in enumerate(top_n, 1):
        priority_score = result["priority_score"]
        detection_conf = result["detection_confidence"]
        
        # Priority indicator
        if priority_score >= 0.7:
            indicator = "🔴 HIGH"
        elif priority_score >= 0.4:
            indicator = "🟡 MEDIUM"
        else:
            indicator = "🟢 LOW"
        
        summary_text += f"\n{i}. {result['condition_id']}\n"
        summary_text += f"   Priority: {indicator} ({priority_score:.3f})\n"
        summary_text += f"   Detection Confidence: {detection_conf:.3f}\n"
        
        # Actionable instruction (NEW - most important for users!)
        if result.get('actionable_instruction'):
            summary_text += f"   ➡️  ACTION: {result['actionable_instruction']}\n"
        
        if result.get('related_documents'):
            summary_text += f"   Related Documents: {result['related_documents']}\n"
        
        # Priority dimensions
        dims = result["priority_dimensions"]
        summary_text += f"   Dimensions: Severity={dims['severity']:.2f}, Impact={dims['impact']:.2f}, "
        summary_text += f"Urgency={dims['urgency']:.2f}, Complexity={dims['complexity']:.2f}\n"
        
        # Original deficiency info
        orig = result["original_deficiency"]
        deficiency_count = len(orig.get("deficiencies", []))
        summary_text += f"   Deficiency Count: {deficiency_count}\n"
        
        # Show first deficiency
        if orig.get("deficiencies"):
            first_def = orig["deficiencies"][0]
            summary_text += f"   Issue: {first_def.get('issue', '')[:100]}...\n"
        
        summary_text += "\n"
    
    return summary_text


# Example usage
if __name__ == "__main__":
    load_dotenv()
    
    # Initialize scorer
    scorer = DeficiencyScorer(
        config_path="scoring_config.json"
    )
    
    # Score deficiencies from step_4_5 test results
    results = scorer.score_deficiencies(
        detection_results="../step_4_5/test_results.json",
        top_n=5,
        verbose=True
    )
    
    # Print formatted summary
    print("\n" + format_results_summary(results))
    
    # Save results
    output_path = "scored_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_path}")

