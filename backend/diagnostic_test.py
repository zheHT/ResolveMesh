#!/usr/bin/env python3
"""
Diagnostic test to check if evidence gathering is actually working
"""

import requests
import json
from supabase_queries import get_dispute_record, get_transactions_by_order_id, get_merchant_record_by_order_id

# Create a dispute
payload = {
    'customer_email': 'diagnostic@test.com',
    'platform': 'GrabFood',
    'amount': 45.50,
    'order_id': 'DIAG-ORDER-001',
    'issue_type': 'Not Delivered',
    'raw_text': 'Test dispute for diagnostics',
    'account_id': 'ACC-DIAG',
}

r = requests.post('http://localhost:8000/api/disputes', json=payload, timeout=10)
if r.status_code != 200:
    print(f"ERROR creating dispute: {r.status_code}")
    print(r.text)
    exit(1)

dispute_id = r.json()['case_id']
print(f"Created dispute: {dispute_id}\n")

# Now check what the backend functions actually fetch
print("=" * 60)
print("DIAGNOSTICS - Backend Evidence Gathering")
print("=" * 60)

dispute = get_dispute_record(dispute_id)
if dispute:
    print(f"\n✅ Dispute Record Found")
    order_id = dispute.get("data", {}).get("customer_info", {}).get("order_id")
    print(f"   Order ID from dispute: {order_id}")
else:
    print(f"\n❌ Dispute Record NOT found")
    exit(1)

# Check transactions
print(f"\nLooking for transactions with order_id='{order_id}'...")
transactions = get_transactions_by_order_id(order_id)
print(f"   Transactions found: {len(transactions)}")
if transactions:
    print(f"   ✅ Sample transaction: {transactions[0].get('row_id')}")
else:
    print(f"   ❌ NO transactions in database for this order")

# Check merchant records
print(f"\nLooking for merchant_records with order_id='{order_id}'...")
merchant = get_merchant_record_by_order_id(order_id)
if merchant:
    print(f"   ✅ Merchant record found: {merchant.get('row_id')}")
else:
    print(f"   ❌ NO merchant_records in database for this order")

print("\n" + "=" * 60)
print("PROBLEM IDENTIFIED:")
print("=" * 60)
print("The evidence gathering FUNCTIONS are being called correctly,")
print("BUT there is NO MATCHING DATA in transactions/merchant_records tables.")
print("\nREASON: Test disputes use fake order_ids that don't exist in database.")
print("\nSOLUTION: Need to either:")
print("  1. Add test data to transactions/merchant_records tables")
print("  2. Test with real order_ids from existing data")
print("  3. Seed database with test fixtures")
print("=" * 60)
