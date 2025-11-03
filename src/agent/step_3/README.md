# Step 3: Rank Requirements by Similarity

## Overview

Step 3 takes the filtered requirements from Step 2 and ranks them by semantic similarity to the input document entities using embeddings.

**Input:** Filtered requirements from Step 2 + Document entities  
**Output:** Requirements sorted by similarity score (highest = most relevant)

## Main Function: `rank_requirements_by_similarity()`

### Basic Usage

```python
from step_3.rank_by_similarity import rank_requirements_by_similarity

# Input from Step 2
filtered_requirements = hard_filter(compartments, entities)

# Step 3: Rank by similarity
ranked_requirements = rank_requirements_by_similarity(
    requirements=filtered_requirements,
    entities=["Appraisal Report", "Property Value"],
    top_n=10  # Return top 10 most similar
)

# Top requirement
print(ranked_requirements[0]['title'])
print(f"Score: {ranked_requirements[0]['similarity_score']:.3f}")
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `requirements` | List[Dict] | Required | Requirements from Step 2 |
| `entities` | List[str] | Required | Entity texts from document |
| `top_n` | int | None | Return top N (None = all) |
| `method` | str | 'max' | Similarity method: 'max' or 'avg' |
| `verbose` | bool | True | Print progress |

### Similarity Methods

**'max' (default)** - Use highest entity similarity
- Best for: Finding requirements related to ANY entity
- Example: If requirement matches "Appraisal Report" strongly but "Tax Returns" weakly, uses the strong match

**'avg'** - Use average entity similarity
- Best for: Finding requirements related to ALL entities
- Example: Requirement must be relevant to all provided entities

## How It Works

```
Input:
  Requirements: 50 (from Step 2)
  Entities: ["Appraisal Report", "Property Value"]

Step 3 Process:
  1. Generate embeddings for entities
     → "Appraisal Report" → [0.123, 0.456, ...]
     → "Property Value" → [0.789, 0.012, ...]
  
  2. Calculate similarity for each requirement
     → Req 1 vs "Appraisal Report": 0.89
     → Req 1 vs "Property Value": 0.75
     → Req 1 final score: 0.89 (max)
  
  3. Sort by score (highest first)
  
  4. Return top N

Output:
  [
    {req_1, similarity_score: 0.89},
    {req_2, similarity_score: 0.82},
    ...
  ]
```

## Interactive Testing

```bash
cd step_3
python3 test_rank_similarity.py
```

**Example Session:**
```
======================================================================
Step 3: Similarity Ranking Test
======================================================================

This ranks requirements from Step 2 by similarity to entities.

Creating sample requirements with dummy embeddings...
Sample: 5 requirements loaded

──────────────────────────────────────────────────────────────────────

Enter entities to rank by [comma-separated] (or 'quit'): Appraisal Report, Property Value
Return top N results (or press Enter for all): 3

Similarity method:
  1. max - Use highest entity similarity (default)
  2. avg - Use average entity similarity
Choose [1/2]: 1

======================================================================
WARNING: Using dummy embeddings for demo
Real embeddings would come from Step 2 requirements
======================================================================

STEP 3: RANK BY SIMILARITY
======================================================================

Input:
  Requirements: 5
  Entities: ['Appraisal Report', 'Property Value']
  Method: max (how to combine entity similarities)

──────────────────────────────────────────────────────────────────────
Generating entity embeddings...
──────────────────────────────────────────────────────────────────────
  ✓ 'Appraisal Report' embedded
  ✓ 'Property Value' embedded

──────────────────────────────────────────────────────────────────────
Calculating similarity scores...
──────────────────────────────────────────────────────────────────────
✓ Ranked 5 requirements

Top 5 similarity scores:
  1. Appraisal Report Must Be Complete                Score: 0.856
  2. Property Value Documentation                     Score: 0.823
  3. Contractor Bid Submission                        Score: 0.612
  4. Bank Statements Required                         Score: 0.445
  5. Tax Returns Verification                         Score: 0.321

✓ Returning top 3 requirements

======================================================================
STEP 3 COMPLETE: 3 ranked requirements
======================================================================
```

## Complete Pipeline Example

Run Steps 1 → 2 → 3 together:

```bash
cd step_3
python3 full_pipeline_example.py
```

This shows the complete workflow from document name to final ranked requirements.

## Integration Example

```python
from step_1.retrieve_document_categories import get_document_category
from step_2.hard_filter import hard_filter
from step_3.rank_by_similarity import rank_requirements_by_similarity

# Document input
document_name = "Contractor Bid"
document_entities = ["Contractor Bid", "Repair Estimate", "Property Address"]

# Step 1: Get compartments
compartments = get_document_category(document_name)
# → ["Borrower Information", "Loan & Property Information", ...]

# Step 2: Hard filter
filtered = hard_filter(compartments, document_entities)
# → 50 requirements

# Step 3: Rank by similarity
ranked = rank_requirements_by_similarity(
    filtered,
    entities=document_entities,
    top_n=10
)
# → Top 10 most relevant requirements

# Use results
for i, req in enumerate(ranked, 1):
    print(f"{i}. {req['title']} (Score: {req['similarity_score']:.3f})")
```

## Output Format

Each requirement gets a `similarity_score` field added:

```python
{
    'id': 'req_123',
    'title': 'Appraisal Report Required',
    'compartment': 'Loan & Property Information',
    'suggested_data_elements': ['Appraisal Report', 'AIR Certification'],
    'embedding': [0.123, 0.456, ...],
    'similarity_score': 0.856  # ← Added by Step 3
}
```

**Score Range:** 0.0 to 1.0
- `1.0` = Perfect match (identical)
- `0.8-1.0` = Very similar
- `0.6-0.8` = Similar
- `0.4-0.6` = Somewhat similar
- `0.0-0.4` = Not very similar

## Setup Requirements

Same as previous steps:

```bash
pip install openai numpy python-dotenv
```

`.env`:
```
OPENAI_API_KEY=your_key_here
```

## Next Steps

After Step 3, the ranked requirements go to Step 4:
- Deficiency detection
- LLM scoring
- Final recommendations

## Files

- `rank_by_similarity.py` - Main ranking function
- `test_rank_similarity.py` - Interactive testing
- `full_pipeline_example.py` - Complete Step 1→2→3 workflow
- `README.md` - This file


