"""
evidence_validator.py

Validates agent outputs to ensure:
1. All evidence citations reference real Supabase rows
2. JSON paths are correct
3. Confidence scores are reasonable
4. Creates audit trail for compliance

Zero tolerance for hallucinated citations.
"""

import json
from typing import Optional, TypedDict
from datetime import datetime, timezone
from supabase_queries import verify_row_exists, verify_json_path
from database import supabase


class ValidationResult(TypedDict):
    """Result of evidence validation"""
    valid: bool
    errors: list[str]
    warnings: list[str]
    hallucination_risk: bool


class EvidenceCitation(TypedDict):
    """A single evidence citation"""
    table: str
    row_id: str
    json_path: Optional[str]
    transaction_id: Optional[str]
    hash: Optional[str]
    details: str


class AgentOutput(TypedDict):
    """Agent's investigation summary output"""
    dispute_id: str
    agent: str
    confidence_score: int
    reasoning: str
    evidence: list[dict]
    summary_tldr: str
    created_at: str


# ============================================================================
# EVIDENCE CITATION VALIDATION
# ============================================================================

def validate_supabase_reference(evidence_item: dict) -> ValidationResult:
    """
    Validate a single evidence citation
    
    Checks:
    1. Table exists (disputes, transactions, system_logs)
    2. Row exists in Supabase
    3. JSON path exists (if specified)
    4. At least transaction_id or hash provided
    """
    errors = []
    warnings = []
    
    try:
        supabase_ref = evidence_item.get("supabase", {})
        table = supabase_ref.get("table")
        row_id = supabase_ref.get("row_id")
        json_path = supabase_ref.get("json_path")
        
        # Validate table
        valid_tables = ["disputes", "transactions", "system_logs"]
        if not table:
            errors.append("Missing 'table' in supabase reference")
            return {"valid": False, "errors": errors, "warnings": warnings, "hallucination_risk": True}
        
        if table not in valid_tables:
            errors.append(f"Invalid table '{table}'. Must be one of: {valid_tables}")
            return {"valid": False, "errors": errors, "warnings": warnings, "hallucination_risk": True}
        
        # Validate row exists
        if not row_id:
            errors.append("Missing 'row_id' in supabase reference")
            return {"valid": False, "errors": errors, "warnings": warnings, "hallucination_risk": True}
        
        if not verify_row_exists(table, row_id):
            errors.append(f"Row does not exist: {table}.{row_id} (POTENTIAL HALLUCINATION)")
            return {"valid": False, "errors": errors, "warnings": warnings, "hallucination_risk": True}
        
        # Validate JSON path (if specified)
        if json_path:
            if not verify_json_path(table, row_id, json_path):
                warnings.append(f"JSON path may not exist: {table}.{row_id}.{json_path}")
        
        # Check for transaction_id or hash
        transaction_id = evidence_item.get("transaction_id")
        hash_val = evidence_item.get("hash")
        
        if not transaction_id and not hash_val:
            warnings.append("No transaction_id or hash provided (makes cross-reference harder)")
        
        # Check details are provided
        details = evidence_item.get("details", "").strip()
        if not details:
            warnings.append("Missing 'details' explaining why this evidence matters")
        
        return {
            "valid": True,
            "errors": errors,
            "warnings": warnings,
            "hallucination_risk": False
        }
        
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return {"valid": False, "errors": errors, "warnings": warnings, "hallucination_risk": True}


def validate_all_evidence(evidence_items: list[dict]) -> ValidationResult:
    """
    Validate all evidence citations in agent output
    
    Returns failure if ANY citation is hallucinated
    """
    all_errors = []
    all_warnings = []
    hallucination_risk = False
    
    if not evidence_items or len(evidence_items) == 0:
        all_errors.append("No evidence provided (minimum 1 required)")
        return {"valid": False, "errors": all_errors, "warnings": all_warnings, "hallucination_risk": True}
    
    for i, item in enumerate(evidence_items):
        result = validate_supabase_reference(item)
        
        if not result["valid"]:
            all_errors.append(f"Evidence item #{i+1}: {'; '.join(result['errors'])}")
            hallucination_risk = result.get("hallucination_risk", False)
        
        all_warnings.extend([f"Evidence #{i+1}: {w}" for w in result["warnings"]])
    
    # Overall result: valid only if all items valid AND at least 1 error-free
    valid = len(all_errors) == 0 and len(evidence_items) > 0
    
    return {
        "valid": valid,
        "errors": all_errors,
        "warnings": all_warnings,
        "hallucination_risk": hallucination_risk
    }


# ============================================================================
# AGENT OUTPUT VALIDATION
# ============================================================================

def validate_agent_output(output: dict) -> ValidationResult:
    """
    Validate complete agent output
    
    Checks:
    1. Required fields present
    2. confidence_score in [0, 100]
    3. summary_tldr <= 30 words
    4. All evidence citations valid
    """
    errors = []
    warnings = []
    
    # Check required fields
    required_fields = ["dispute_id", "agent", "confidence_score", "reasoning", "evidence", "summary_tldr", "created_at"]
    for field in required_fields:
        if field not in output:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "hallucination_risk": False}
    
    # Validate confidence_score
    confidence = output.get("confidence_score")
    if not isinstance(confidence, (int, float)):
        errors.append(f"confidence_score must be numeric, got {type(confidence)}")
    elif confidence < 0 or confidence > 100:
        errors.append(f"confidence_score must be in [0, 100], got {confidence}")
    
    # Validate summary_tldr word count
    tldr = output.get("summary_tldr", "")
    word_count = len(tldr.split())
    if word_count > 30:
        errors.append(f"summary_tldr exceeds 30 words (got {word_count}): '{tldr[:50]}...'")
    
    # Validate evidence
    evidence = output.get("evidence", [])
    evidence_result = validate_all_evidence(evidence)
    
    if not evidence_result["valid"]:
        errors.extend(evidence_result["errors"])
    warnings.extend(evidence_result["warnings"])
    
    # Overall result
    valid = len(errors) == 0 and len(evidence) > 0
    hallucination_risk = evidence_result.get("hallucination_risk", False)
    
    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "hallucination_risk": hallucination_risk
    }


# ============================================================================
# AUDIT TRAIL STORAGE
# ============================================================================

def store_evidence_audit_trail(
    dispute_id: str,
    agent_name: str,
    evidence_items: list[dict],
    validation_result: ValidationResult,
    confidence_score: int
) -> bool:
    """
    Store evidence citations in audit table for compliance
    
    Creates record: agent_evidence_citations
    Columns: dispute_id, agent, supabase_table, row_id, json_path, 
             details, confidence_used, validation_passed, timestamp
    """
    try:
        if supabase is None:
            print("Supabase not configured")
            return False
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        for i, item in enumerate(evidence_items):
            supabase_ref = item.get("supabase", {})
            
            audit_record = {
                "dispute_id": dispute_id,
                "agent": agent_name,
                "evidence_index": i + 1,
                "supabase_table": supabase_ref.get("table"),
                "row_id": supabase_ref.get("row_id"),
                "json_path": supabase_ref.get("json_path"),
                "transaction_id": item.get("transaction_id"),
                "hash": item.get("hash"),
                "details": item.get("details"),
                "confidence_used": confidence_score,
                "validation_passed": validation_result["valid"],
                "validation_errors": ";".join(validation_result["errors"]),
                "validation_warnings": ";".join(validation_result["warnings"]),
                "hallucination_risk": validation_result.get("hallucination_risk", False),
                "created_at": timestamp
            }
            
            # Insert into audit table
            supabase.table("agent_evidence_citations").insert(audit_record).execute()
        
        return True
        
    except Exception as e:
        print(f"Error storing audit trail: {e}")
        return False


# ============================================================================
# RESPONSE ENRICHMENT
# ============================================================================

def enrich_agent_response(
    agent_output: dict,
    dispute_data: dict
) -> dict:
    """
    Enrich agent response with validation metadata
    
    Adds:
    - validation_result
    - citation_count
    - confidence_justification (brief)
    """
    validation = validate_agent_output(agent_output)
    
    enriched = agent_output.copy()
    enriched["validation_metadata"] = {
        "valid": validation["valid"],
        "error_count": len(validation["errors"]),
        "warning_count": len(validation["warnings"]),
        "hallucination_risk": validation.get("hallucination_risk", False),
        "errors": validation["errors"],
        "warnings": validation["warnings"]
    }
    enriched["citation_count"] = len(agent_output.get("evidence", []))
    enriched["confidence_justification"] = (
        f"Based on {enriched['citation_count']} evidence citation(s) from "
        f"Supabase ({', '.join([e.get('supabase', {}).get('table', 'unknown') for e in agent_output.get('evidence', [])])})"
    )
    
    return enriched


# ============================================================================
# BATCH VALIDATION
# ============================================================================

def validate_agent_responses(
    dispute_id: str,
    responses: dict[str, dict]  # agent_name -> output
) -> dict[str, ValidationResult]:
    """
    Validate all agent responses for a dispute
    
    Returns:
        {
            "customerLawyer": ValidationResult,
            "companyLawyer": ValidationResult,
            "judge": ValidationResult,
            "independentLawyer": ValidationResult
        }
    """
    results = {}
    
    for agent_name, output in responses.items():
        # Validate output
        validation = validate_agent_output(output)
        results[agent_name] = validation
        
        # Store audit trail if valid
        if validation["valid"]:
            evidence_items = output.get("evidence", [])
            confidence = output.get("confidence_score", 0)
            
            store_evidence_audit_trail(
                dispute_id,
                agent_name,
                evidence_items,
                validation,
                confidence
            )
    
    return results


# ============================================================================
# VALIDATION REPORTING
# ============================================================================

def generate_validation_report(
    dispute_id: str,
    responses: dict[str, dict]
) -> dict:
    """
    Generate comprehensive validation report
    """
    validation_results = validate_agent_responses(dispute_id, responses)
    
    all_valid = all(r["valid"] for r in validation_results.values())
    hallucination_risk = any(r.get("hallucination_risk", False) for r in validation_results.values())
    total_errors = sum(len(r["errors"]) for r in validation_results.values())
    total_warnings = sum(len(r["warnings"]) for r in validation_results.values())
    
    report = {
        "dispute_id": dispute_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_responses_valid": all_valid,
        "hallucination_detected": hallucination_risk,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "agent_results": {},
        "summary": ""
    }
    
    for agent_name, result in validation_results.items():
        report["agent_results"][agent_name] = {
            "valid": result["valid"],
            "errors": result["errors"],
            "warnings": result["warnings"],
            "hallucination_risk": result.get("hallucination_risk", False)
        }
    
    # Generate summary
    if all_valid:
        report["summary"] = f"✅ All {len(responses)} agent responses valid. No hallucination detected."
    else:
        invalid_agents = [name for name, r in validation_results.items() if not r["valid"]]
        report["summary"] = (
            f"⚠️ {len(invalid_agents)} agent response(s) invalid: {', '.join(invalid_agents)}. "
            f"Total errors: {total_errors}. Hallucination risk: {hallucination_risk}"
        )
    
    return report


# ============================================================================
# CITATION QUALITY CHECK
# ============================================================================

def check_citation_quality(evidence_items: list[dict]) -> dict:
    """
    Check quality of evidence citations
    
    Metrics:
    - Citation specificity (% with json_path)
    - Cross-referencing (% with transaction_id or hash)
    - Detail level (avg detail text length)
    """
    if not evidence_items:
        return {
            "quality_score": 0,
            "metrics": {},
            "recommendation": "No evidence provided"
        }
    
    with_json_path = sum(1 for e in evidence_items if e.get("supabase", {}).get("json_path"))
    with_transaction_id = sum(1 for e in evidence_items if e.get("transaction_id"))
    with_hash = sum(1 for e in evidence_items if e.get("hash"))
    avg_detail_length = sum(len(e.get("details", "")) for e in evidence_items) / len(evidence_items)
    
    specificity_score = (with_json_path / len(evidence_items)) * 100
    cross_ref_score = ((with_transaction_id + with_hash) / len(evidence_items)) * 100
    detail_score = min((avg_detail_length / 100) * 100, 100)  # 100 chars = max score
    
    quality_score = (specificity_score * 0.3 + cross_ref_score * 0.3 + detail_score * 0.4) / 100
    
    recommendation = "Excellent citations" if quality_score > 0.8 else \
                    "Good citations" if quality_score > 0.6 else \
                    "Acceptable citations" if quality_score > 0.4 else \
                    "Weak citations - need more detail and cross-references"
    
    return {
        "quality_score": round(quality_score, 2),
        "metrics": {
            "specificity_pct": round(specificity_score, 1),
            "cross_reference_pct": round(cross_ref_score, 1),
            "detail_score": round(detail_score, 1),
            "avg_detail_length": round(avg_detail_length)
        },
        "recommendation": recommendation
    }
