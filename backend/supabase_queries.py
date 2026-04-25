"""
supabase_queries.py

Low-level Supabase query helpers for evidence gathering.
All functions return citation-ready data with row IDs.

These are building blocks for evidence_gatherer.py
"""

from typing import Optional, Any
from datetime import datetime, timezone
from database import supabase

if supabase is None:
    raise RuntimeError("Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")


# ============================================================================
# DISPUTES TABLE QUERIES
# ============================================================================

def get_dispute_record(dispute_id: str) -> dict[str, Any] | None:
    """
    Fetch full dispute record by ID
    
    Returns:
        {
            "row_id": dispute_id,
            "table": "disputes",
            "data": { full record }
        }
    
    Supabase: SELECT * FROM disputes WHERE id = dispute_id
    """
    try:
        res = supabase.table("disputes").select("*").eq("id", dispute_id).execute()
        if res.data and len(res.data) > 0:
            return {
                "row_id": dispute_id,
                "table": "disputes",
                "citation_path": None,
                "data": res.data[0]
            }
        return None
    except Exception as e:
        print(f"Error fetching dispute {dispute_id}: {e}")
        return None


def get_dispute_customer_info(dispute_id: str) -> dict[str, Any] | None:
    """
    Extract customer_info JSONB field from dispute
    
    Returns customer_email, account_id, order_id, amount, issue_type
    """
    dispute = get_dispute_record(dispute_id)
    if dispute:
        return {
            "row_id": dispute_id,
            "table": "disputes",
            "json_path": "customer_info",
            "data": dispute["data"].get("customer_info", {})
        }
    return None


def get_dispute_status(dispute_id: str) -> str | None:
    """Get current status of dispute"""
    try:
        res = supabase.table("disputes").select("status").eq("id", dispute_id).execute()
        if res.data:
            return res.data[0].get("status")
        return None
    except Exception as e:
        print(f"Error fetching dispute status: {e}")
        return None


# ============================================================================
# SYSTEM LOGS QUERIES
# ============================================================================

def get_dispute_logs(dispute_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    """
    Fetch all system logs for a dispute, ordered by timestamp
    
    Supabase: SELECT * FROM system_logs 
              WHERE payload->dispute_id = dispute_id 
              ORDER BY created_at ASC
              LIMIT limit OFFSET offset
    
    Returns:
        [{
            "row_id": log_id,
            "table": "system_logs",
            "event_name": string,
            "visibility": "PUBLIC" | "INTERNAL",
            "timestamp": ISO8601,
            "payload": JSONB,
            "citation_example": "table='system_logs', row_id='log-123', json_path='payload.event_type'"
        }]
    """
    try:
        res = (
            supabase.table("system_logs")
            .select("id, event_name, visibility, payload, created_at")
            .filter("payload->dispute_id", "eq", dispute_id)
            .order("created_at", desc=False)
            .limit(limit)
            .offset(offset)
            .execute()
        )
        
        logs = []
        for row in res.data or []:
            logs.append({
                "row_id": row.get("id"),
                "table": "system_logs",
                "event_name": row.get("event_name"),
                "visibility": row.get("visibility"),
                "timestamp": row.get("created_at"),
                "payload": row.get("payload", {}),
                "citation_path": None
            })
        return logs
    except Exception as e:
        print(f"Error fetching dispute logs: {e}")
        return []


def search_logs_by_event(dispute_id: str, event_pattern: str) -> list[dict]:
    """
    Search system logs by event type
    
    Examples: "DELIVERY", "REFUND", "CHARGE", "DISPUTE", "COMPLAINT"
    
    Returns: Filtered logs matching event_name pattern
    """
    try:
        res = (
            supabase.table("system_logs")
            .select("id, event_name, visibility, payload, created_at")
            .filter("payload->dispute_id", "eq", dispute_id)
            .ilike("event_name", f"%{event_pattern}%")
            .order("created_at", desc=False)
            .execute()
        )
        
        logs = []
        for row in res.data or []:
            logs.append({
                "row_id": row.get("id"),
                "table": "system_logs",
                "event_name": row.get("event_name"),
                "timestamp": row.get("created_at"),
                "payload": row.get("payload", {}),
            })
        return logs
    except Exception as e:
        print(f"Error searching logs by event: {e}")
        return []


def get_log_by_id(log_id: str) -> dict[str, Any] | None:
    """Fetch a specific system log by row ID"""
    try:
        res = supabase.table("system_logs").select("*").eq("id", log_id).execute()
        if res.data:
            return {
                "row_id": log_id,
                "table": "system_logs",
                "data": res.data[0]
            }
        return None
    except Exception as e:
        print(f"Error fetching log {log_id}: {e}")
        return None


# ============================================================================
# TRANSACTIONS TABLE QUERIES
# ============================================================================

def get_transaction_by_id(transaction_id: str) -> dict[str, Any] | None:
    """
    Fetch transaction record by transaction_id
    
    Supabase: SELECT * FROM transactions 
              WHERE ledger_data->transaction_id = transaction_id
    
    Returns: Full transaction with ledger_data JSONB
    """
    try:
        res = (
            supabase.table("transactions")
            .select("*")
            .filter("ledger_data->transaction_id", "eq", transaction_id)
            .execute()
        )
        
        if res.data and len(res.data) > 0:
            row = res.data[0]
            return {
                "row_id": row.get("id"),
                "table": "transactions",
                "transaction_id": transaction_id,
                "citation_path": "ledger_data.transaction_id",
                "data": row
            }
        return None
    except Exception as e:
        print(f"Error fetching transaction: {e}")
        return None


def get_transaction_hashes(transaction_id: str) -> list[dict]:
    """
    Extract all hash values from transaction ledger_data
    
    Returns:
        [{
            "hash": "0x...",
            "field": "tx_hash" | "audit_hash" | etc,
            "row_id": transaction_id,
            "table": "transactions",
            "json_path": "ledger_data.tx_hash"
        }]
    """
    txn = get_transaction_by_id(transaction_id)
    if not txn:
        return []
    
    ledger_data = txn.get("data", {}).get("ledger_data", {})
    hashes = []
    
    # Common hash field names in transaction ledgers
    hash_fields = ["tx_hash", "transaction_hash", "audit_hash", "capture_hash", "settlement_hash"]
    
    for field in hash_fields:
        if field in ledger_data and ledger_data[field]:
            hashes.append({
                "hash": ledger_data[field],
                "field": field,
                "row_id": transaction_id,
                "table": "transactions",
                "json_path": f"ledger_data.{field}"
            })
    
    return hashes


def get_transactions_by_order_id(order_id: str) -> list[dict]:
    """
    Fetch all transactions matching order_id
    
    Useful for detecting duplicate charges
    """
    try:
        res = (
            supabase.table("transactions")
            .select("*")
            .filter("ledger_data->>order_id", "eq", order_id)
            .execute()
        )
        
        txns = []
        for row in res.data or []:
            txns.append({
                "row_id": row.get("id"),
                "table": "transactions",
                "ledger_data": row.get("ledger_data", {}),
                "data": row
            })
        return txns
    except Exception as e:
        print(f"Error fetching transactions by order: {e}")
        return []


def get_merchant_status(transaction_id: str) -> str | None:
    """
    Get merchant_status from transaction ledger
    
    Status values: "pending", "captured", "settled", "failed", "refunded", etc.
    """
    txn = get_transaction_by_id(transaction_id)
    if txn:
        return txn.get("data", {}).get("ledger_data", {}).get("merchant_status")
    return None


# ============================================================================
# TIMELINE QUERIES
# ============================================================================

def get_timeline(dispute_id: str, max_events: int = 100) -> list[dict]:
    """
    Build chronological timeline of all events for dispute
    
    Merges data from:
    - disputes table (creation)
    - system_logs (events)
    - transactions (if order_id available)
    
    Returns:
        [{
            "timestamp": ISO8601,
            "event_type": string,
            "source": "disputes" | "system_logs" | "transactions",
            "row_id": string,
            "table": string,
            "description": string,
            "data": dict
        }]
    """
    timeline = []
    
    # 1. Add dispute creation event
    dispute = get_dispute_record(dispute_id)
    if dispute:
        timeline.append({
            "timestamp": dispute["data"].get("created_at"),
            "event_type": "DISPUTE_CREATED",
            "source": "disputes",
            "row_id": dispute_id,
            "table": "disputes",
            "description": f"Dispute created for order {dispute['data'].get('customer_info', {}).get('order_id')}",
            "data": dispute["data"]
        })
    
    # 2. Add system logs (ordered)
    logs = get_dispute_logs(dispute_id, limit=max_events)
    for log in logs:
        timeline.append({
            "timestamp": log.get("timestamp"),
            "event_type": log.get("event_name"),
            "source": "system_logs",
            "row_id": log.get("row_id"),
            "table": "system_logs",
            "description": log.get("payload", {}).get("message", log.get("event_name")),
            "data": log.get("payload")
        })
    
    # 3. Get related transactions if order_id exists
    if dispute:
        order_id = dispute["data"].get("customer_info", {}).get("order_id")
        if order_id:
            txns = get_transactions_by_order_id(order_id)
            for txn in txns:
                ledger = txn.get("ledger_data", {})
                timeline.append({
                    "timestamp": txn["data"].get("created_at"),
                    "event_type": "TRANSACTION",
                    "source": "transactions",
                    "row_id": txn.get("row_id"),
                    "table": "transactions",
                    "description": f"Transaction {ledger.get('transaction_id')} - {ledger.get('merchant_status')}",
                    "data": ledger
                })
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x.get("timestamp") or "")
    
    return timeline


# ============================================================================
# HASH CROSS-REFERENCE QUERIES
# ============================================================================

def find_matching_hashes(dispute_id: str) -> dict[str, list]:
    """
    Cross-reference all hashes found in system_logs and transactions
    
    Returns:
        {
            "hash_value": [
                { "table": "system_logs", "row_id": "...", "json_path": "..." },
                { "table": "transactions", "row_id": "...", "json_path": "..." }
            ]
        }
    """
    hash_index = {}
    
    # Collect hashes from system logs
    logs = get_dispute_logs(dispute_id, limit=100)
    for log in logs:
        payload = log.get("payload", {})
        
        # Common hash field names in payloads
        for key in ["audit_hash", "txn_hash", "transaction_hash", "hash", "delivery_hash"]:
            if key in payload and payload[key]:
                hash_val = payload[key]
                if hash_val not in hash_index:
                    hash_index[hash_val] = []
                hash_index[hash_val].append({
                    "table": "system_logs",
                    "row_id": log.get("row_id"),
                    "json_path": f"payload.{key}"
                })
    
    # Collect hashes from transactions
    dispute = get_dispute_record(dispute_id)
    if dispute:
        order_id = dispute["data"].get("customer_info", {}).get("order_id")
        if order_id:
            txns = get_transactions_by_order_id(order_id)
            for txn in txns:
                ledger = txn.get("ledger_data", {})
                for key in ["tx_hash", "transaction_hash", "audit_hash", "hash"]:
                    if key in ledger and ledger[key]:
                        hash_val = ledger[key]
                        if hash_val not in hash_index:
                            hash_index[hash_val] = []
                        hash_index[hash_val].append({
                            "table": "transactions",
                            "row_id": txn.get("row_id"),
                            "json_path": f"ledger_data.{key}"
                        })
    
    return hash_index


# ============================================================================
# CUSTOMER HISTORY QUERIES
# ============================================================================

def get_customer_dispute_history(customer_email: str, limit: int = 10) -> list[dict]:
    """
    Fetch all disputes for a customer (for fraud detection patterns)
    
    Supabase: SELECT * FROM disputes 
              WHERE customer_info->email = customer_email
              ORDER BY created_at DESC
    """
    try:
        res = (
            supabase.table("disputes")
            .select("id, created_at, status, customer_info, amount")
            .filter("customer_info->email", "eq", customer_email)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        disputes = []
        for row in res.data or []:
            disputes.append({
                "dispute_id": row.get("id"),
                "created_at": row.get("created_at"),
                "status": row.get("status"),
                "amount": row.get("amount", 0),
                "customer_info": row.get("customer_info", {})
            })
        return disputes
    except Exception as e:
        print(f"Error fetching customer history: {e}")
        return []


# ============================================================================
# MERCHANT RECORDS QUERIES
# ============================================================================

def get_merchant_record_by_order_id(order_id: str) -> dict[str, Any] | None:
    """
    Fetch merchant record by order_id
    
    Returns merchant fulfillment data:
    - order_id
    - prep_status (e.g., "pending", "preparing", "ready", "picked_up")
    - items_prepared (list of items)
    - timestamps (prep_start, prep_end, pickup_time)
    - merchant_id
    - delivery_partner
    
    Returns:
        {
            "row_id": merchant_record_id,
            "table": "merchant_records",
            "order_id": order_id,
            "data": { full merchant record }
        }
    """
    try:
        res = (
            supabase.table("merchant_records")
            .select("*")
            .eq("order_id", order_id)
            .execute()
        )
        
        if res.data and len(res.data) > 0:
            row = res.data[0]
            return {
                "row_id": row.get("id"),
                "table": "merchant_records",
                "order_id": order_id,
                "citation_path": "order_id",
                "data": row
            }
        return None
    except Exception as e:
        print(f"Error fetching merchant record for order {order_id}: {e}")
        return None


def get_merchant_fulfillment_status(order_id: str) -> dict[str, Any] | None:
    """
    Get merchant fulfillment status (preparation + pickup)
    
    Returns:
        {
            "prep_status": "pending" | "preparing" | "ready" | "picked_up",
            "items_prepared": [list of items],
            "prep_start_time": ISO 8601,
            "prep_end_time": ISO 8601,
            "pickup_time": ISO 8601
        }
    """
    merchant_record = get_merchant_record_by_order_id(order_id)
    if not merchant_record:
        return None
    
    data = merchant_record.get("data", {})
    return {
        "prep_status": data.get("prep_status"),
        "items_prepared": data.get("items_prepared", []),
        "prep_start_time": data.get("prep_start_time"),
        "prep_end_time": data.get("prep_end_time"),
        "pickup_time": data.get("pickup_time"),
        "merchant_id": data.get("merchant_id"),
        "delivery_partner": data.get("delivery_partner")
    }


def get_all_merchant_records_for_merchant_id(merchant_id: str) -> list[dict]:
    """
    Get all orders/fulfillment records for a specific merchant
    
    Useful for checking merchant reputation/pattern
    """
    try:
        res = (
            supabase.table("merchant_records")
            .select("*")
            .eq("merchant_id", merchant_id)
            .order("created_at", desc=False)
            .limit(50)
            .execute()
        )
        
        records = []
        for row in res.data or []:
            records.append({
                "row_id": row.get("id"),
                "table": "merchant_records",
                "order_id": row.get("order_id"),
                "data": row
            })
        return records
    except Exception as e:
        print(f"Error fetching merchant records for {merchant_id}: {e}")
        return []


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def verify_row_exists(table: str, row_id: str) -> bool:
    """
    Verify a row exists in Supabase (for citation validation)
    """
    try:
        res = supabase.table(table).select("id").eq("id", row_id).execute()
        return len(res.data or []) > 0
    except Exception as e:
        print(f"Error verifying row {table}.{row_id}: {e}")
        return False


def verify_json_path(table: str, row_id: str, json_path: str) -> bool:
    """
    Verify a JSON path exists in a JSONB column
    
    Example: verify_json_path("system_logs", "log-123", "payload.audit_hash")
    """
    try:
        parts = json_path.split(".")
        res = supabase.table(table).select("*").eq("id", row_id).execute()
        
        if not res.data:
            return False
        
        data = res.data[0]
        for part in parts:
            if isinstance(data, dict):
                data = data.get(part)
            else:
                return False
        
        return data is not None
    except Exception as e:
        print(f"Error verifying json_path: {e}")
        return False
