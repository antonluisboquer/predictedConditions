# End-to-end demo for Step 4: from a sample doc JSON to a list of deficiencies.
# - Assumes you already have the candidate "condition templates" (from Steps 1–3).
# - We only implement: compare doc features vs. condition rules and emit deficiencies.

from typing import Any, Dict, List, Tuple
from dotenv import load_dotenv
import json

CONF_T = 0.6  # confidence threshold to treat a parsed value as usable
load_dotenv()

# ---------- Sample input: normalized/ETL doc JSON (what Step 0 would output) ----------

DOC_JSON = {
    "doc_presence": {
        "Borrower Attestation": True,
        "Seller Certification": True,
        "Realtor Certification": True,
        "Photos (Interior/Exterior/Street Scene)": True,
        "Appraisal Report": True
    },
    "transaction": {
        "purpose": {"value": "Purchase", "confidence": 0.99}
    },
    "property": {
        "fema_impacted": {"value": True, "confidence": 0.97, "source_doc": "fema_portal.png"}
    },
    "appraisal": {
        "damage_observed": {"value": False, "confidence": 0.93, "source_doc": "appraisal.pdf#p4"}
    },
    "attestation": {
        "borrower": {
            "no_damage": {"value": True, "confidence": 0.95, "source_doc": "attestation.pdf#p1"},
            "no_claims": {"value": True, "confidence": 0.91, "source_doc": "attestation.pdf#p1"}
        }
    },
    "certification": {
        "seller": {
            "no_damage": {"value": True, "confidence": 0.9, "source_doc": "seller_cert.pdf#p1"},
            "no_claims": {"value": True, "confidence": 0.9, "source_doc": "seller_cert.pdf#p1"}
        },
        "realtor": {
            "post_storm_visit": {"value": True, "confidence": 0.92, "source_doc": "realtor_cert.pdf#p1"}
        }
    },
    "photos": {
        "coverage_includes_interior": {"value": True, "confidence": 0.95, "source_doc": "photos.zip#img_001"},
        "coverage_includes_exterior_all_angles": {"value": True, "confidence": 0.95, "source_doc": "photos.zip#img_010-020"},
        "coverage_includes_street_scene": {"value": True, "confidence": 0.95, "source_doc": "photos.zip#img_021"},
        "dated": {"value": True, "confidence": 0.95, "source_doc": "photos.zip#exif"}
    }
}


# ---------- Sample condition templates (from Step 3 results) ----------

CONDITION_TEMPLATES = [
    {
        "condition_id": "COND_ALT_APPRAISAL_FEMA_P",
        "title": "Alt - Appraisal: FEMA (P) Impacted Areas",
        "compartment": "Loan & Property Information",
        "scope": "property",
        "severity": "hard",
        "applies_when": [
            {"field": "transaction.purpose", "op": "eq", "value": "Purchase"},
            {"field": "property.fema_impacted", "op": "eq", "value": True}
        ],
        "must_have_docs": [
            "Borrower Attestation",
            "Seller Certification",
            "Realtor Certification",
            "Photos (Interior/Exterior/Street Scene)",
            "Appraisal Report"
        ],
        "checks": [
            {"field": "attestation.borrower.no_damage",  "op": "eq",  "value": True},
            {"field": "attestation.borrower.no_claims",  "op": "eq",  "value": True},
            {"field": "certification.seller.no_damage",  "op": "eq",  "value": True},
            {"field": "certification.seller.no_claims",  "op": "eq",  "value": True},
            {"field": "certification.realtor.post_storm_visit", "op": "eq", "value": True},
            {"field": "photos.coverage_includes_interior",       "op": "eq", "value": True},
            {"field": "photos.coverage_includes_exterior_all_angles", "op": "eq", "value": True},
            {"field": "photos.coverage_includes_street_scene",   "op": "eq", "value": True},
            {"field": "photos.dated",                            "op": "eq", "value": True},
            {"field": "appraisal.damage_observed",               "op": "eq", "value": False}
        ],
        "exceptions": [
            {
                "when": {"field": "appraisal.damage_observed", "op": "eq", "value": True},
                "action": "deficient",
                "note": "Damage observed cannot be waived by attestations/certifications."
            }
        ],
        "aggregation": "single"
    },
    # Add one more example to show a failing/unknown behavior:
    {
        "condition_id": "COND_ALT_APPRAISAL_FEMA_P_MISSING_DOCS",
        "title": "Alt - Appraisal: FEMA (P) Impacted Areas - Docs Complete",
        "compartment": "Loan & Property Information",
        "scope": "property",
        "severity": "hard",
        "applies_when": [
            {"field": "transaction.purpose", "op": "eq", "value": "Purchase"},
            {"field": "property.fema_impacted", "op": "eq", "value": True}
        ],
        "must_have_docs": [
            "Borrower Attestation",
            "Seller Certification",
            "Realtor Certification",
            "Photos (Interior/Exterior/Street Scene)",
            "Appraisal Report",
            "Flood/Elevation Cert (if applicable)"  # pretend this is required here for demo
        ],
        "checks": [
            {"field": "attestation.borrower.no_damage",  "op": "eq",  "value": True}
        ],
        "exceptions": [],
        "aggregation": "single"
    }
]


# ---------- Validator utilities ----------

def _get_nested(d: Dict[str, Any], dotted_key: str) -> Any:
    """Fetch d['a']['b']['c'] via 'a.b.c', return {} if missing to avoid KeyError."""
    cur = d
    for part in dotted_key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return {}
    return cur

def _get_value(d: Dict[str, Any], dotted_key: str) -> Tuple[Any, float, Any]:
    """Return (value, confidence, provenance) from a normalized field or (None, 0.0, None)."""
    node = _get_nested(d, dotted_key)
    if isinstance(node, dict) and "value" in node:
        val = node.get("value")
        conf = float(node.get("confidence", 0.0) or 0.0)
        prov = node.get("source_doc")
        return val, conf, prov
    # allow raw booleans/strings for presence-like fields
    if isinstance(node, bool) or isinstance(node, (int, float, str)):
        return node, 1.0, None
    return None, 0.0, None

def _compare(op: str, actual: Any, expected: Any) -> bool:
    if op == "eq":
        return actual == expected
    if op == "neq":
        return actual != expected
    if op == "gte":
        try: return float(actual) >= float(expected)
        except: return False
    if op == "lte":
        try: return float(actual) <= float(expected)
        except: return False
    if op == "in":
        try: return actual in expected
        except: return False
    if op == "between":
        try:
            lo, hi = expected
            return float(lo) <= float(actual) <= float(hi)
        except:
            return False
    return False

def _applies_when(doc: Dict[str, Any], cond: Dict[str, Any]) -> bool:
    for rule in cond.get("applies_when", []):
        actual, conf, _ = _get_value(doc, rule["field"])
        if conf < CONF_T:
            return False
        if not _compare(rule["op"], actual, rule["value"]):
            return False
    return True

def evaluate_condition(doc: Dict[str, Any], cond: Dict[str, Any]) -> Dict[str, Any]:
    # 1) Check applicability
    if not _applies_when(doc, cond):
        return {
            "condition_id": cond["condition_id"],
            "title": cond.get("title"),
            "status": "not_applicable",
            "failures": [],
            "notes": "applies_when not satisfied"
        }

    failures = []
    notes = []

    # 2) Check required documents
    for docname in cond.get("must_have_docs", []):
        present = doc.get("doc_presence", {}).get(docname, False)
        if not present:
            failures.append({
                "field": f"doc_presence.{docname}",
                "expected": "present",
                "actual": "missing",
                "provenance": None
            })

    # 3) Apply exception guardrails first (if any)
    for ex in cond.get("exceptions", []):
        actual, conf, prov = _get_value(doc, ex["when"]["field"])
        if conf >= CONF_T and _compare(ex["when"]["op"], actual, ex["when"]["value"]):
            status = ex.get("action", "unknown")
            return {
                "condition_id": cond["condition_id"],
                "title": cond.get("title"),
                "status": status,
                "failures": failures,  # may include missing docs already
                "notes": ex.get("note", "")
            }

    # 4) Evaluate checks
    for rule in cond.get("checks", []):
        actual, conf, prov = _get_value(doc, rule["field"])
        if conf < CONF_T or actual is None:
            failures.append({
                "field": rule["field"],
                "expected": f"{rule['op']} {rule['value']}",
                "actual": "unknown",
                "provenance": prov
            })
            continue
        if not _compare(rule["op"], actual, rule["value"]):
            failures.append({
                "field": rule["field"],
                "expected": f"{rule['op']} {rule['value']}",
                "actual": actual,
                "provenance": prov
            })

    status = "satisfied" if len(failures) == 0 else "deficient"
    return {
        "condition_id": cond["condition_id"],
        "title": cond.get("title"),
        "status": status,
        "failures": failures,
        "notes": "; ".join(notes) if notes else ""
    }


# ---------- Run the evaluator on our sample inputs ----------

results = [evaluate_condition(DOC_JSON, c) for c in CONDITION_TEMPLATES]

print("=== DEFICIENCY RESULTS (Step 4) ===")
print(json.dumps(results, indent=2))
