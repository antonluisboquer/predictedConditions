# Test Values for test_hard_filter.py

## Test Scenario 1: Appraisal Documents
**Compartment(s):**
```
Loan & Property Information
```

**Entities:**
```
Appraisal Report, Property Value, AIR Certification
```

---

## Test Scenario 2: Multiple Compartments
**Compartment(s):**
```
Loan & Property Information, Assets & Liabilities
```

**Entities:**
```
Appraisal Report, Acknowledgement of Receipt of Appraisal Report
```

---

## Test Scenario 3: Contractor/Repair Documents
**Compartment(s):**
```
Borrower Information, Loan & Property Information
```

**Entities:**
```
Contractor Bid, Repair Estimate, Property Address
```

---

## Test Scenario 4: Employment/Income Documents
**Compartment(s):**
```
Employment & Income
```

**Entities:**
```
W-2 Forms, Pay Stubs, Tax Returns, Employment Verification Letter
```

---

## Test Scenario 5: Single Compartment, Single Entity
**Compartment(s):**
```
Declarations
```

**Entities:**
```
Bankruptcy Declaration
```

---

## Test Scenario 6: Broad Search
**Compartment(s):**
```
Continuation / Additional Information, Borrower Information, Loan & Property Information
```

**Entities:**
```
Contractor Bid, Appraisal Report, Tax Returns
```

---

## Common Compartment Labels

Use any of these:
- `Continuation / Additional Information`
- `Loan & Property Information`
- `Borrower Information`
- `Assets & Liabilities`
- `Declarations`
- `Employment & Income`
- `Acknowledgments & Agreements`
- `Demographic Information (HMDA)`

---

## Common Entity Names

Use any of these:
- `Appraisal Report`
- `Acknowledgement of Receipt of Appraisal Report`
- `Contractor Bid`
- `AIR Certification`
- `Property Value`
- `Property Deed`
- `Tax Returns`
- `W-2 Forms`
- `Pay Stubs`
- `Bank Statements`
- `Driver's License`
- `Social Security Card`
- `Employment Verification Letter`
- `Bankruptcy Declaration`
- `Repair Estimate`
- `Property Address`

---

## Quick Copy-Paste Examples

### Example 1:
```
Compartment: Loan & Property Information
Entities: Appraisal Report, Property Value
```

### Example 2:
```
Compartment: Loan & Property Information, Borrower Information
Entities: Contractor Bid, Repair Estimate
```

### Example 3:
```
Compartment: Assets & Liabilities
Entities: Bank Statements, Tax Returns
```

### Example 4:
```
Compartment: Employment & Income
Entities: W-2 Forms, Pay Stubs
```

