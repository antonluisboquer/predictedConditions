# Known Issues and Solutions

## Issue 1: JSON Parsing Error - "Unterminated string" (FIXED)

### Symptom
```
❌ ERROR: Failed to parse LLM response as JSON
Exception: Unterminated string starting at: line 294 column 20 (char 14433)
```

### Root Cause
When checking too many conditions (e.g., 100) in a single LLM call:
1. The LLM generates a very long JSON response
2. Response hits the `max_tokens` limit (was 4000)
3. Response gets truncated mid-string
4. Truncated JSON cannot be parsed

### Solution
**Applied two fixes:**

1. **Reduced max conditions per batch** (in `graph.py`):
   - Changed from 100 → 50 conditions per LLM call
   - Prevents response from getting too large

2. **Increased max_tokens** (in `llm_deficiency_detector.py`):
   - Changed from 4000 → 8000 tokens
   - Allows for longer responses when needed

3. **Better error diagnostics**:
   - Shows response length
   - Shows both start and end of response
   - Detects if response was truncated
   - Suggests solution

### Files Modified
- `src/agent/graph.py` - Lines 378-383
- `src/agent/step_4_5/llm_deficiency_detector.py` - Lines 147, 359-379

### Testing
After fix:
```bash
python test/quick_test.py  # Should now complete successfully
python test/debug_step4.py  # Test with 10 conditions
```

### Prevention
If you see this error again:
1. Check how many conditions are being checked
2. Reduce conditions per batch OR increase max_tokens
3. Look at the error output for truncation warning

---

## Issue 2: Silent Failures - "model: unknown" and 0 tokens (FIXED)

### Symptom
In output JSON:
```json
{
  "step_4_5": {
    "tokens": {
      "model": "unknown",
      "input_tokens": 0,
      "output_tokens": 0
    }
  }
}
```

### Root Cause
When LLM call fails:
1. Error handler returns `{"error": "...", "exception": "..."}`
2. Old code didn't check for errors
3. Tried to extract `_metadata` from error dict
4. Got empty dict with default values
5. Continued silently without logging the error

### Solution
**Added error detection in graph.py** (lines 402-421):
- Check for `"error"` key in detection results
- Log error with full details
- Set model to `"error"` instead of `"unknown"`
- Return early with proper error state
- Prevents silent failures

### Files Modified
- `src/agent/graph.py` - Lines 402-421
- `src/agent/step_4_5/llm_deficiency_detector.py` - Lines 359-379

### Testing
Errors now appear in logs:
```
[STEP_4_5] ERROR: LLM call failed: Failed to parse LLM response as JSON
```

And in output JSON:
```json
{
  "step_4_5": {
    "tokens": {
      "model": "error",
      ...
    }
  },
  "logs": [
    {
      "event_type": "error",
      "message": "LLM call failed: ...",
      "exception": "...",
      "raw_response": "..."
    }
  ]
}
```

---

## Best Practices

### Checking Multiple Conditions
- **Recommended**: 10-50 conditions per batch
- **Maximum**: 50 conditions (enforced in code)
- **If you need more**: Process in batches or use `check_document_batch()`

### Token Limits
- Current `max_tokens`: 8000
- Each condition result: ~150-300 tokens
- Formula: `conditions * 250 + overhead < max_tokens`
- For 50 conditions: ~12,500 tokens needed (but responses are often shorter)

### Error Handling
Always check logs for errors:
```python
with open('output.json') as f:
    data = json.load(f)
    
# Check for errors
for log in data['logs']:
    if log['event_type'] == 'error':
        print(f"Error in {log['step']}: {log['message']}")
```

### Debugging Tips
1. Use `test/debug_step4.py` to test LLM calls directly
2. Start with 5-10 conditions for testing
3. Check terminal output for detailed error messages
4. Look at both start and end of LLM responses
5. Check if `appears_truncated: true` in error response

