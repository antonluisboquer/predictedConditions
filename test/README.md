# Multi-Document Agent Tests

This directory contains test scripts for the multi-document agent pipeline.

## Test Scripts

### 1. `quick_test.py` - Fast Single Test
Quick test with a simple cross-document scenario (Tax Return + K-1).

**Run:**
```bash
python test/quick_test.py
```

**What it tests:**
- Cross-document deficiency resolution
- New field presence (documents_checked, satisfied_by, actionable_documents)
- Embedding removal verification

**Expected duration:** ~30-60 seconds

---

### 2. `test_multi_document_agent.py` - Full Test Suite
Comprehensive test suite covering all scenarios.

**Run:**
```bash
python test/test_multi_document_agent.py
```

**Test Cases:**

| Test | Description | Purpose |
|------|-------------|---------|
| Test 1 | Old format input (backward compatibility) | Verify old single-document format still works |
| Test 2 | New format with single document | Verify new format with one document |
| Test 3 | Multiple documents of same type | Test with 2x Tax Returns (2023 & 2022) |
| Test 4 | Cross-document resolution | Tax Return + K-1 (ownership info in K-1) |
| Test 5 | Diverse document types | Tax Return + K-1 + Bank Statement + CPA Letter |

**Expected duration:** ~3-5 minutes (all 5 tests)

---

## Test Inputs

Test inputs are automatically generated and saved to:
- `test_1_old_format_input.json`
- `test_2_single_doc_new_format_input.json`
- `test_3_multiple_same_type_input.json`
- `test_4_cross_document_input.json`
- `test_5_diverse_documents_input.json`
- `quick_test_input.json`

## Test Outputs

Test outputs are saved to:
- `test_1_output.json`
- `test_2_output.json`
- `test_3_output.json`
- `test_4_output.json`
- `test_5_output.json`
- `quick_test_output.json`

## Verification Checks

Each test automatically verifies:

✅ **No embeddings in output** - Confirms embedding arrays were removed

✅ **New fields present** - Checks for:
  - `actionable_documents`: Filtered document list based on instruction
  - `documents_checked`: Documents that were reviewed
  - `satisfied_by`: Document that satisfied the requirement (or null)

✅ **Field relationships** - Verifies `actionable_documents` ⊆ `related_documents`

✅ **Cross-document logic** - In multi-document tests, checks that:
  - Multiple documents are processed collectively
  - LLM considers information from all documents
  - Deficiencies can be resolved across documents

## Sample Input Formats

### Old Format (Backward Compatible)
```json
{
  "borrower_info": {...},
  "classification": "1120 Corporate Tax Return",
  "extracted_entities": {...},
  "loan_program": "Flex Supreme"
}
```

### New Format (Multi-Document)
```json
{
  "borrower_info": {...},
  "loan_program": "Flex Supreme",
  "documents": [
    {
      "classification": "1120 Corporate Tax Return",
      "extracted_entities": {...}
    },
    {
      "classification": "Schedule K-1 Form 1120S",
      "extracted_entities": {...}
    }
  ]
}
```

## Expected Output Fields

Each deficiency result should include:

```json
{
  "condition_id": "Condition name",
  "status": "deficient",
  "detection_confidence": 0.85,
  "priority_score": 0.92,
  "related_documents": "Doc1, Doc2, Doc3, ...",
  "actionable_documents": "Doc1, Doc2",  // ← Filtered list
  "actionable_instruction": "Upload signed tax return",
  "documents_checked": ["1120 Corporate Tax Return", "K-1"],  // ← All docs reviewed
  "satisfied_by": null,  // ← Which doc satisfied (or null)
  ...
}
```

## Troubleshooting

**Import errors:**
- Ensure you're running from project root
- Check that `src/agent` is accessible

**API errors:**
- Verify `ANTHROPIC_API_KEY` in `.env`
- Verify `OPENAI_API_KEY` in `.env`
- Check `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` in `.env`

**Slow performance:**
- Tests use `top_n=5` to limit deficiencies checked
- Full pipeline may take 30-60 seconds per test case
- Condition filtering is limited to 100 conditions max

## Notes

- Tests require active API keys (Anthropic, OpenAI)
- Tests require Neo4j connection for graph queries
- First test may be slower due to LLM prompt cache creation
- Subsequent tests benefit from cached prompts (90% cost savings)

