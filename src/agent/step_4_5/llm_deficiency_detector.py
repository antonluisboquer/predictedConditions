"""
LLM-Based Deficiency Detection System (Approach 1)
Uses Claude with prompt caching to validate documents against natural language conditions.
"""

import json
import os
import pandas as pd
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMDeficiencyDetector:
    """
    Detects loan document deficiencies using Claude AI with prompt caching.
    No rule generation needed - works directly with natural language conditions.
    """
    
    def __init__(
        self, 
        conditions_csv_path: str,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929"#"claude-3-5-sonnet-20241022"
    ):
        """
        Initialize the detector with conditions from CSV.
        
        Args:
            conditions_csv_path: Path to CSV file with conditions
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or parameters")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        
        # Load conditions
        print(f"Loading conditions from {conditions_csv_path}...")
        self.conditions_df = pd.read_csv(conditions_csv_path)
        print(f"Loaded {len(self.conditions_df)} conditions")
        
        # Build cached system prompt with all conditions
        self.system_prompt = self._build_system_prompt()
        print(f"System prompt built ({len(self.system_prompt)} chars) - will be cached on first use")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt containing all conditions (for caching)."""
        
        prompt = """You are an expert loan underwriting compliance checker.

Your job is to evaluate loan documents against specific underwriting conditions and determine if they are satisfied, deficient, or not applicable.

INSTRUCTIONS:
1. Read the condition requirements carefully, including ALL parts (Description, Enhanced Description, Required Documents, Data Elements)
2. Examine the provided document data thoroughly
3. Check if the condition applies to this loan scenario
4. If applicable, verify ALL requirements are met
5. Identify specific deficiencies with field references and evidence
6. Provide clear reasoning for your determination
7. Return results as valid JSON ONLY (no markdown, no extra text)

IMPORTANT: Focus on DETECTION only. Do not score or rank deficiencies - that will be done in post-processing.

CONDITION CATALOG:
Below are all underwriting conditions you may be asked to check:

"""
        
        # Add each condition with full details
        for idx, row in self.conditions_df.iterrows():
            condition_id = row['Title']
            description = row.get('Description', '')
            # enhanced_desc = row.get('Enhanced Description by RAM', '')
            # compartment = row.get('Proposed Compartmentalization', '')
            related_docs = row.get('Related documents', '')
            data_elements = row.get('Suggested Data Elements', '')
            
            # Removed enhanced description and compartment from prompt
            # to shorten prompt length
            
            prompt += f"""
---
CONDITION ID: {condition_id}
DESCRIPTION: {description}
RELATED DOCUMENTS: {related_docs}
KEY DATA ELEMENTS: {data_elements}
"""
        
        prompt += """
---

RESPONSE FORMAT:
Always return valid JSON with this exact structure:
{
  "results": [
    {
      "condition_id": "condition title",
      "status": "satisfied|deficient|not_applicable",
      "deficiencies": [
        {
          "requirement": "specific requirement not met",
          "issue": "what's wrong or missing",
          "field_checked": "document field path",
          "evidence": "what was found or not found"
        }
      ],
      "reasoning": "brief explanation of evaluation",
      "checked_fields": ["list", "of", "fields", "examined"],
      "actionable_instruction": "Simple, clear action in plain language that a loan processor can take to resolve this deficiency. Use imperative verbs. Examples: 'Upload signed tax return', 'Obtain signature from borrower', 'Request Schedule C attachment', 'Provide proof of ownership percentage'"
    }
  ]
}

IMPORTANT: The "actionable_instruction" field must be:
- Short and direct (5-10 words)
- Use action verbs: Upload, Obtain, Request, Provide, Submit, Collect, etc.
- Non-technical language that anyone can understand
- Specific to what document or action is needed
- Immediately actionable by a loan processor

NOTE: Do not provide confidence scores. Focus only on clear deficiency detection.
"""
        return prompt
    
    def check_document(
        self, 
        document_data: Dict[str, Any], 
        condition_ids: List[str],
        max_tokens: int = 4000,
        additional_context: Optional[List[Dict[str, Any]]] = None,
        loan_program: Optional[str] = None,
        borrower_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check a document against specific conditions.
        
        Args:
            document_data: Document JSON with extracted data (from your ETL/parsing)
            condition_ids: List of condition IDs (titles) to check
            max_tokens: Maximum tokens for response
            additional_context: Optional context from step 3 (ranked requirements with connected nodes)
            loan_program: Optional loan program name (e.g., "Flex Supreme")
            borrower_info: Optional borrower information (name, type, SSN, etc.)
            
        Returns:
            Dict with evaluation results for each condition
        """
        
        # Build user prompt with loan program and borrower info context
        user_prompt = ""
        
        # Add loan program and borrower info at the top for context
        if loan_program or borrower_info:
            user_prompt += "LOAN APPLICATION CONTEXT:\n"
            
            if loan_program:
                user_prompt += f"Loan Program: {loan_program}\n"
                print(f"  ✓ Adding loan program to LLM context: {loan_program}")
            
            if borrower_info:
                user_prompt += "Borrower Information:\n"
                borrower_context_items = []
                
                if borrower_info.get('first_name') or borrower_info.get('last_name'):
                    name_parts = [
                        borrower_info.get('first_name', ''),
                        borrower_info.get('middle_name', ''),
                        borrower_info.get('last_name', '')
                    ]
                    full_name = ' '.join(part for part in name_parts if part).strip()
                    user_prompt += f"  - Name: {full_name}\n"
                    borrower_context_items.append(f"Name: {full_name}")
                
                if borrower_info.get('borrower_type'):
                    user_prompt += f"  - Type: {borrower_info['borrower_type']}\n"
                    borrower_context_items.append(f"Type: {borrower_info['borrower_type']}")
                
                if borrower_info.get('business_name'):
                    user_prompt += f"  - Business Name: {borrower_info['business_name']}\n"
                    borrower_context_items.append(f"Business: {borrower_info['business_name']}")
                
                if borrower_info.get('email'):
                    user_prompt += f"  - Email: {borrower_info['email']}\n"
                
                if borrower_context_items:
                    print(f"  ✓ Adding borrower info to LLM context: {', '.join(borrower_context_items)}")
            
            user_prompt += "\nIMPORTANT: Only select and evaluate conditions that relate to the loan program that the borrower is eligible for. Consider the borrower's type and context when evaluating requirements.\n\n"
        
        # Add conditions and document data
        user_prompt += f"""Please evaluate this loan document against the following conditions:

CONDITIONS TO CHECK: {', '.join(condition_ids)}

DOCUMENT DATA:
{json.dumps(document_data, indent=2)}
"""
        
        # Add additional context from step 3 if available
        if additional_context:
            user_prompt += "\n\nADDITIONAL CONTEXT FROM GRAPH ANALYSIS:\n"
            user_prompt += "The following related requirements, conditions, and dependencies were identified as relevant:\n\n"
            
            for idx, req in enumerate(additional_context[:10], 1):  # Limit to top 10 to manage prompt size
                req_name = req.get('name') or req.get('title') or f"Requirement {idx}"
                similarity = req.get('similarity_score', 0)
                user_prompt += f"{idx}. {req_name} (Similarity: {similarity:.3f})\n"
                
                # Add connected nodes information
                connected = req.get('connected_nodes', {})
                
                # Add conditions
                if connected.get('conditions'):
                    user_prompt += f"   Related Conditions:\n"
                    for cond in connected['conditions'][:3]:  # Limit to 3 per requirement
                        cond_title = cond.get('Title') or cond.get('name') or 'Unknown'
                        cond_desc = cond.get('Description', '')[:100]  # Truncate long descriptions
                        if cond_desc:
                            user_prompt += f"   - {cond_title}: {cond_desc}...\n"
                        else:
                            user_prompt += f"   - {cond_title}\n"
                
                # Add dependencies
                if connected.get('dependencies'):
                    user_prompt += f"   Dependencies:\n"
                    for dep in connected['dependencies'][:3]:
                        dep_name = dep.get('name') or dep.get('title') or 'Unknown'
                        user_prompt += f"   - {dep_name}\n"
                
                # Add related requirements
                if connected.get('related_requirements'):
                    user_prompt += f"   Related Requirements:\n"
                    for rel_req in connected['related_requirements'][:3]:
                        rel_name = rel_req.get('name') or rel_req.get('title') or 'Unknown'
                        user_prompt += f"   - {rel_name}\n"
                
                user_prompt += "\n"
            
            user_prompt += "Consider this context when evaluating the conditions. These connections may indicate:\n"
            user_prompt += "- Related conditions that should be checked together\n"
            user_prompt += "- Dependencies between requirements\n"
            user_prompt += "- Additional requirements that may apply\n\n"
        
        user_prompt += """
For each condition listed above:
1. Determine if it applies to this loan
2. Check if all requirements are satisfied
3. Identify any deficiencies with specific field references and evidence
4. Provide clear reasoning for your determination
5. Consider the additional context provided when making your determination
6. Provide a simple, actionable instruction for resolving each deficiency (e.g., "Upload signed tax return", "Obtain CPA letter showing 25% ownership")

Return the evaluation as JSON following the response format specified in the system prompt.
IMPORTANT: Include the "actionable_instruction" field for each deficient condition.
Do NOT include confidence scores - focus only on clear deficiency detection.
"""
        
        try:
            # Make API call with prompt caching
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=[{
                    "type": "text",
                    "text": self.system_prompt,
                    "cache_control": {"type": "ephemeral"}  # Enable caching
                }],
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }]
            )
            
            # Parse response
            response_text = response.content[0].text
            
            # Try to extract JSON from response (in case there's markdown formatting)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            
            # Enrich results with related documents from CSV
            if "results" in result:
                for item in result["results"]:
                    condition_id = item.get("condition_id")
                    if condition_id:
                        # Look up the condition in the CSV
                        condition_row = self.conditions_df[
                            self.conditions_df['Title'] == condition_id
                        ]
                        if len(condition_row) > 0:
                            related_docs = condition_row.iloc[0].get('Related documents', '')
                            item['related_documents'] = related_docs if pd.notna(related_docs) else ''
                        else:
                            item['related_documents'] = ''
            
            # Add metadata
            result['_metadata'] = {
                'model': self.model,
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'cache_read_tokens': getattr(response.usage, 'cache_read_input_tokens', 0),
                'cache_creation_tokens': getattr(response.usage, 'cache_creation_input_tokens', 0),
            }
            
            return result
            
        except json.JSONDecodeError as e:
            return {
                "error": "Failed to parse LLM response as JSON",
                "raw_response": response_text,
                "exception": str(e)
            }
        except Exception as e:
            return {
                "error": "API call failed",
                "exception": str(e)
            }
    
    def check_document_batch(
        self,
        document_data: Dict[str, Any],
        batch_size: int = 10,
        additional_context: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Check document against ALL conditions in batches.
        
        Args:
            document_data: Document JSON
            batch_size: Number of conditions to check per API call
            additional_context: Optional context from step 3 (ranked requirements with connected nodes)
            
        Returns:
            List of all evaluation results
        """
        all_results = []
        condition_ids = self.conditions_df['Title'].tolist()
        
        print(f"Checking document against {len(condition_ids)} conditions in batches of {batch_size}...")
        
        for i in range(0, len(condition_ids), batch_size):
            batch = condition_ids[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(condition_ids)-1)//batch_size + 1}...")
            
            result = self.check_document(document_data, batch, additional_context=additional_context)
            
            if "results" in result:
                all_results.extend(result["results"])
            else:
                print(f"Warning: Batch failed - {result.get('error', 'Unknown error')}")
        
        return all_results
    
    def get_condition_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Get full condition details by title."""
        matches = self.conditions_df[self.conditions_df['Title'] == title]
        if len(matches) > 0:
            return matches.iloc[0].to_dict()
        return None
    
    def search_conditions(self, keyword: str) -> pd.DataFrame:
        """Search conditions by keyword in title or description."""
        mask = (
            self.conditions_df['Title'].str.contains(keyword, case=False, na=False) |
            self.conditions_df['Description'].str.contains(keyword, case=False, na=False)
        )
        return self.conditions_df[mask]
    
    def filter_by_classification(
        self, 
        classification: str, 
        document_fields: List[str] = None,
        loan_program: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Filter conditions based on document classification AND extracted fields.
        
        A condition is included ONLY IF:
        1. Related documents contains the classification
        AND
        2. Suggested Data Elements contains at least one document field
        
        Falls back to "All Docs" conditions if no matches found.
        
        Args:
            classification: Document classification string (e.g., "1120 Corporate Tax Return")
            document_fields: List of field names from extracted_entities (e.g., ["year", "line8", "corporation"])
            loan_program: Optional loan program name for additional filtering context
            
        Returns:
            DataFrame of matching conditions
        """
        if 'Related documents' not in self.conditions_df.columns:
            print(f"Warning: 'Related documents' column not found")
            return pd.DataFrame()
        
        # Step 1: Filter by classification in Related documents
        classification_mask = self.conditions_df['Related documents'].fillna('').str.contains(
            classification,
            case=False,
            na=False
        )
        classification_matches = self.conditions_df[classification_mask]
        
        # If no document fields provided, return classification matches only
        if not document_fields or 'Suggested Data Elements' not in self.conditions_df.columns:
            if len(classification_matches) > 0:
                print(f"✓ Found {len(classification_matches)} conditions (classification only)")
            return classification_matches
        
        # Step 2: Filter classification matches by field presence
        # Only keep conditions that ALSO have at least one matching field
        final_mask = pd.Series([False] * len(classification_matches), index=classification_matches.index)
        
        for idx, row in classification_matches.iterrows():
            suggested_elements = str(row.get('Suggested Data Elements', '')).lower()
            
            # Check if ANY document field appears in suggested data elements
            for field in document_fields:
                if field.lower() in suggested_elements:
                    final_mask[idx] = True
                    break  # Found at least one field match, include this condition
        
        # Apply the field filter to classification matches (INTERSECTION)
        matching = classification_matches[final_mask]
        
        if len(matching) > 0:
            if loan_program:
                print(f"✓ Found {len(matching)} conditions (classification + field match) for loan program '{loan_program}'")
            else:
                print(f"✓ Found {len(matching)} conditions (classification + field match)")
            return matching
        
        # If no matches with both criteria, try "All Docs" fallback
        print(f"Note: No conditions matched both classification '{classification}' AND document fields")
        
        fallback_mask = self.conditions_df['Related documents'].fillna('').str.contains(
            r'all\s+doc',  # Matches "All Docs", "All Documents", etc.
            case=False,
            regex=True,
            na=False
        )
        matching = self.conditions_df[fallback_mask]
        
        if len(matching) > 0:
            print(f"Using {len(matching)} universal 'All Docs' conditions as fallback")
        
        return matching


def format_results_summary(results: List[Dict[str, Any]]) -> str:
    """Format results into a human-readable summary."""
    
    summary = "=" * 80 + "\n"
    summary += "DEFICIENCY DETECTION RESULTS\n"
    summary += "=" * 80 + "\n\n"
    
    satisfied = [r for r in results if r['status'] == 'satisfied']
    deficient = [r for r in results if r['status'] == 'deficient']
    not_applicable = [r for r in results if r['status'] == 'not_applicable']
    
    summary += f"Total Conditions Checked: {len(results)}\n"
    summary += f"✅ Satisfied: {len(satisfied)}\n"
    summary += f"❌ Deficient: {len(deficient)}\n"
    summary += f"⊘  Not Applicable: {len(not_applicable)}\n\n"
    
    if deficient:
        summary += "DEFICIENCIES FOUND:\n"
        summary += "-" * 80 + "\n"
        
        for i, result in enumerate(deficient, 1):
            summary += f"\n{i}. {result['condition_id']}\n"
            
            # Show actionable instruction prominently (NEW!)
            if result.get('actionable_instruction'):
                summary += f"   ➡️  ACTION NEEDED: {result['actionable_instruction']}\n"
            
            if result.get('related_documents'):
                summary += f"   Related Documents: {result['related_documents']}\n"
            summary += f"   Reasoning: {result['reasoning']}\n"
            
            if result.get('deficiencies'):
                summary += f"   Issues:\n"
                for deficiency in result['deficiencies']:
                    summary += f"   • {deficiency['requirement']}\n"
                    summary += f"     Problem: {deficiency['issue']}\n"
                    if deficiency.get('field_checked'):
                        summary += f"     Field: {deficiency['field_checked']}\n"
                    if deficiency.get('evidence'):
                        summary += f"     Evidence: {deficiency['evidence']}\n"
            summary += "\n"
    
    return summary


# Example usage
if __name__ == "__main__":
    # Load sample document from file
    sample_doc_path = "../sample_doc_input.json"
    
    print(f"Loading sample document from: {sample_doc_path}")
    try:
        with open(sample_doc_path, "r") as f:
            SAMPLE_DOC = json.load(f)
        print(f"✓ Loaded document with classification: {SAMPLE_DOC.get('classification', 'N/A')}")
    except FileNotFoundError:
        print(f"Error: Could not find {sample_doc_path}")
        print("Please ensure sample_doc_input.json exists in the parent directory")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {sample_doc_path}: {e}")
        exit(1)
    
    # Initialize detector
    detector = LLMDeficiencyDetector(
        conditions_csv_path="../merged_conditions_with_related_docs__FULL_filtered_simple.csv"
    )
    
    # Check specific conditions
    print("\n" + "="*80)
    doc_classification = SAMPLE_DOC.get('classification', 'Unknown type')
    print(f"Testing with sample document: {doc_classification}")
    print("="*80 + "\n")
    
    # Filter conditions based on document classification AND extracted fields
    print(f"Filtering conditions based on:")
    print(f"  - Classification: '{doc_classification}'")
    
    # Extract field names from extracted_entities
    document_fields = []
    if "extracted_entities" in SAMPLE_DOC:
        document_fields = list(SAMPLE_DOC["extracted_entities"].keys())
        print(f"  - Document fields: {document_fields[:10]}{'...' if len(document_fields) > 10 else ''}")
    print()
    
    matching_conditions = detector.filter_by_classification(doc_classification, document_fields)
    
    if len(matching_conditions) > 0:
        conditions_to_check = matching_conditions['Title'].tolist()
        print(f"Conditions: {conditions_to_check[:5]}{'...' if len(conditions_to_check) > 5 else ''}\n")
    else:
        print(f"⚠ No conditions found (including 'All Docs' fallback)")
        print("Using first 3 conditions for testing purposes...\n")
        conditions_to_check = detector.conditions_df['Title'].head(3).tolist()
    
    result = detector.check_document(SAMPLE_DOC, conditions_to_check)
    
    # Print results
    if "results" in result:
        print(json.dumps(result, indent=2))
        print("\n" + format_results_summary(result["results"]))
        
        # Print token usage
        if "_metadata" in result:
            meta = result["_metadata"]
            print("="*80)
            print("API USAGE:")
            print(f"Input tokens: {meta['input_tokens']}")
            print(f"Output tokens: {meta['output_tokens']}")
            print(f"Cache read tokens: {meta['cache_read_tokens']}")
            print(f"Cache creation tokens: {meta['cache_creation_tokens']}")
            
            if meta['cache_read_tokens'] > 0:
                print("\n✅ Prompt cache HIT - 90% cost savings!")
            elif meta['cache_creation_tokens'] > 0:
                print("\n📝 Prompt cache CREATED - will save on next call")
    else:
        print("ERROR:", result.get("error"))
        if "raw_response" in result:
            print("\nRaw response:", result["raw_response"])

