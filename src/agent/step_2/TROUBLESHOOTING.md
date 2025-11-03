# Step 2 Troubleshooting: Why Am I Getting 0 Results?

## Problem: Semantic Search Returns 0 Requirements

If you see:
```
Path B: Semantic Entity Search
✓ Found 0 requirement(s) via semantic search

⚠️  No requirements matched BOTH conditions
📋 Fallback: Returning all X requirement(s) from Path A (compartment)
```

## Common Causes & Solutions

### 1. Similarity Threshold Too High ⚠️

**Default:** `similarity_threshold = 0.5` (50% similarity required)

**Solution:** Lower the threshold to be more lenient

```python
requirements = hard_filter(
    compartments=["Loan & Property Information"],
    entities=["Appraisal Report"],
    similarity_threshold=0.3  # Try 0.3 (30%) or even 0.2 (20%)
)
```

**Scale:**
- `0.7` - Very strict (70% similarity)
- `0.5` - Moderate (50% similarity) ← **Default**
- `0.3` - Lenient (30% similarity)
- `0.2` - Very lenient (20% similarity)

---

### 2. Neo4j GDS Plugin Not Installed 🔌

**Error message:**
```
⚠️  Query failed for 'Appraisal Report': ...
💡 This might mean:
   - Neo4j GDS plugin not installed (for gds.similarity.cosine)
```

**Solution:** Install Neo4j Graph Data Science (GDS) plugin

```bash
# For Neo4j Desktop: Install GDS plugin from the plugins section
# For Docker:
docker run \
    -p 7474:7474 -p 7687:7687 \
    neo4j:5.0-enterprise \
    --env NEO4J_PLUGINS='["graph-data-science"]'
```

Or use the alternative query (doesn't require GDS) - see workaround below.

---

### 3. Nodes Don't Have Embeddings 📊

**Cause:** Your Neo4j nodes don't have an `embedding` property

**Check:**
```cypher
MATCH (n)
WHERE n.embedding IS NOT NULL
RETURN count(n) as nodes_with_embeddings
```

If this returns 0, you need to generate embeddings for your nodes.

**Solution:** Generate and add embeddings to your nodes

```python
# See generate_embeddings.py for how to create embeddings
```

---

### 4. No Relationship Path to Requirements 🔗

**Cause:** Nodes don't have a path to Requirement nodes

**Check:**
```cypher
MATCH (n)-[*1..2]-(req:Requirement)
RETURN count(DISTINCT req) as requirements_connected
```

**Solution:** Ensure your graph has relationships connecting nodes to Requirements

---

### 5. Increase Search Scope 🔍

**Default:** `top_k = 20` (finds top 20 similar nodes per entity)

**Solution:** Increase to search more nodes

```python
requirements = hard_filter(
    compartments=["Loan & Property Information"],
    entities=["Appraisal Report"],
    top_k=50  # Search top 50 instead of 20
)
```

---

## Quick Fixes to Try

### Fix 1: More Lenient Search
```python
requirements = hard_filter(
    compartments=["Loan & Property Information"],
    entities=["Appraisal Report"],
    similarity_threshold=0.2,  # Very lenient
    top_k=50  # Search more nodes
)
```

### Fix 2: Check What's Happening
The script now shows debugging info:
```
Path B: Semantic Entity Search
  Similarity threshold: 0.5 (lower = more results)
  Top-k per entity: 20
──────────────────────────────────────────────────────────────────────
    'Appraisal Report': Found 5 requirement(s)
    'Property Value': Found 3 requirement(s)
✓ Found 8 requirement(s) via semantic search
```

If you see `Found 0 requirement(s)` for each entity, it's a database/embedding issue.

### Fix 3: Use Fallback Behavior
The script automatically falls back to Path A (compartment matching) if semantic search returns 0:
```
⚠️  No requirements matched BOTH conditions
📋 Fallback: Returning all 50 requirement(s) from Path A (compartment)
```

This ensures you always get results based on compartment matching.

---

## Workaround: Disable Semantic Search

If semantic search keeps failing, use the compartment-only filter:

```python
from step_2.filter_requirements_by_compartment import filter_requirements_multiple_compartments

requirements = filter_requirements_multiple_compartments(
    compartments=["Loan & Property Information"],
    entities=["Appraisal Report"]  # Uses keyword matching, not embeddings
)
```

---

## Check Your Setup

Run this diagnostic:

```python
from step_2.hard_filter import hard_filter

# Try with very lenient settings
requirements = hard_filter(
    compartments=["Loan & Property Information"],
    entities=["Appraisal Report"],
    similarity_threshold=0.1,  # 10% similarity
    top_k=100,  # Search top 100
    verbose=True  # See debugging output
)

print(f"Got {len(requirements)} requirements")
```

If this still returns 0 from semantic search, you likely have a database configuration issue.

---

## Summary

**Most Common Issue:** Similarity threshold too high
**Quick Fix:** Lower `similarity_threshold` to 0.2-0.3
**Safety Net:** Fallback to compartment matching ensures you always get results

**Recommended Settings:**
```python
hard_filter(
    compartments=compartments,
    entities=entities,
    similarity_threshold=0.3,  # Lenient but not too loose
    top_k=30  # Good balance
)
```

