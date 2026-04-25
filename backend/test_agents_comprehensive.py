#!/usr/bin/env python3
"""
test_agents_comprehensive.py

Comprehensive testing suite for all ResolveMesh agents.
Tests: Customer Lawyer, Company Lawyer, Judge, Independent Lawyer, Auditor, Guardian, Summarizer

Usage:
    python test_agents_comprehensive.py --smoke        # Quick 2-min health check
    python test_agents_comprehensive.py --individual   # Test each agent separately
    python test_agents_comprehensive.py --evidence     # Test evidence bundles
    python test_agents_comprehensive.py --workflow     # End-to-end workflow
    python test_agents_comprehensive.py --all          # All tests
"""

import requests
import json
import time
import argparse
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

BASE_URL = "http://localhost:8000"
TIMEOUT = 60

# Color codes for terminal output
class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


@dataclass
class TestResult:
    name: str
    status: str  # "PASS", "FAIL", "SKIP", "TIMEOUT"
    message: str = ""
    details: Dict = None


class TestRunner:
    def __init__(self):
        self.results: List[TestResult] = []
        self.dispute_id: Optional[str] = None
    
    def log(self, level: str, message: str):
        """Print formatted log message"""
        if level == "SUCCESS":
            print(f"{Color.GREEN}✅ {message}{Color.END}")
        elif level == "FAIL":
            print(f"{Color.RED}❌ {message}{Color.END}")
        elif level == "INFO":
            print(f"{Color.BLUE}ℹ️  {message}{Color.END}")
        elif level == "WARN":
            print(f"{Color.YELLOW}⚠️  {message}{Color.END}")
        elif level == "HEADER":
            print(f"\n{Color.BOLD}{Color.CYAN}{'='*60}{Color.END}")
            print(f"{Color.BOLD}{Color.CYAN}{message}{Color.END}")
            print(f"{Color.BOLD}{Color.CYAN}{'='*60}{Color.END}\n")
        elif level == "SUBHEADER":
            print(f"\n{Color.BOLD}→ {message}{Color.END}")
    
    def add_result(self, result: TestResult):
        """Add test result"""
        self.results.append(result)
    
    def print_summary(self):
        """Print test summary"""
        self.log("HEADER", "TEST SUMMARY")
        
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        timeout = sum(1 for r in self.results if r.status == "TIMEOUT")
        
        print(f"Total: {len(self.results)}")
        print(f"{Color.GREEN}PASS: {passed}{Color.END}")
        print(f"{Color.RED}FAIL: {failed}{Color.END}")
        print(f"{Color.YELLOW}SKIP: {skipped}{Color.END}")
        print(f"{Color.YELLOW}TIMEOUT: {timeout}{Color.END}")
        
        print(f"\nDetails:")
        for r in self.results:
            if r.status == "PASS":
                status_str = f"{Color.GREEN}PASS{Color.END}"
            elif r.status == "FAIL":
                status_str = f"{Color.RED}FAIL{Color.END}"
            elif r.status == "SKIP":
                status_str = f"{Color.YELLOW}SKIP{Color.END}"
            else:
                status_str = f"{Color.YELLOW}TIMEOUT{Color.END}"
            
            print(f"  {status_str}  {r.name}")
            if r.message:
                print(f"       {r.message}")
    
    # ========================================================================
    # SMOKE TESTS (2 minutes)
    # ========================================================================
    
    def test_supabase_health(self) -> bool:
        """Test Supabase connectivity"""
        self.log("SUBHEADER", "[SMOKE] Testing Supabase Connection")
        try:
            r = requests.get(f"{BASE_URL}/api/disputes", timeout=5)
            if r.status_code == 200:
                self.log("SUCCESS", "Supabase connected")
                self.add_result(TestResult("Supabase Health", "PASS"))
                return True
            else:
                msg = f"Status {r.status_code}"
                self.log("FAIL", f"Supabase: {msg}")
                self.add_result(TestResult("Supabase Health", "FAIL", msg))
                return False
        except Exception as e:
            self.log("FAIL", f"Supabase error: {str(e)}")
            self.add_result(TestResult("Supabase Health", "FAIL", str(e)))
            return False
    
    def test_zai_health(self) -> bool:
        """Test Z.AI connectivity"""
        self.log("SUBHEADER", "[SMOKE] Testing Z.AI Connection")
        try:
            r = requests.get(f"{BASE_URL}/api/zai/health", timeout=5)
            if r.status_code == 200:
                self.log("SUCCESS", "Z.AI connected")
                self.add_result(TestResult("Z.AI Health", "PASS"))
                return True
            else:
                msg = f"Status {r.status_code}"
                self.log("FAIL", f"Z.AI: {msg}")
                self.add_result(TestResult("Z.AI Health", "FAIL", msg))
                return False
        except Exception as e:
            self.log("FAIL", f"Z.AI error: {str(e)}")
            self.add_result(TestResult("Z.AI Health", "FAIL", str(e)))
            return False
    
    def test_agent_list(self) -> bool:
        """Test agent list endpoint"""
        self.log("SUBHEADER", "[SMOKE] Testing Agent List")
        try:
            r = requests.get(f"{BASE_URL}/api/agents", timeout=5)
            if r.status_code == 200:
                agents = r.json()
                operational = len([a for a in agents if a.get("system") == "operational"])
                legal = len([a for a in agents if a.get("system") == "legal"])
                self.log("SUCCESS", f"Found {operational} operational + {legal} legal agents")
                self.add_result(TestResult("Agent List", "PASS", f"Operational: {operational}, Legal: {legal}"))
                return True
            else:
                self.log("FAIL", f"Agent list: {r.status_code}")
                self.add_result(TestResult("Agent List", "FAIL", f"Status {r.status_code}"))
                return False
        except Exception as e:
            self.log("FAIL", f"Agent list error: {str(e)}")
            self.add_result(TestResult("Agent List", "FAIL", str(e)))
            return False
    
    def run_smoke_tests(self):
        """Run all smoke tests"""
        self.log("HEADER", "SMOKE TESTS (System Health)")
        self.test_supabase_health()
        self.test_zai_health()
        self.test_agent_list()
    
    # ========================================================================
    # INDIVIDUAL AGENT TESTS
    # ========================================================================
    
    def test_individual_agent(self, agent_type: str, dispute_id: Optional[str] = None) -> bool:
        """Test a single agent"""
        if not dispute_id:
            if not self.dispute_id:
                self.log("WARN", f"Skipping {agent_type}: No dispute ID")
                self.add_result(TestResult(f"Agent: {agent_type}", "SKIP", "No dispute ID"))
                return False
            dispute_id = self.dispute_id
        
        try:
            payload = {
                "dispute_id": dispute_id,
                "agents": [agent_type]
            }
            
            r = requests.post(
                f"{BASE_URL}/api/agents/analyze",
                json=payload,
                timeout=TIMEOUT
            )
            
            if r.status_code == 200:
                data = r.json()
                status = data.get("status")
                validation = data.get("validation_report", {})
                valid = validation.get("all_responses_valid", False)
                
                if valid or status == "success":
                    self.log("SUCCESS", f"{agent_type}: {status}")
                    self.add_result(TestResult(f"Agent: {agent_type}", "PASS", f"Status: {status}"))
                    return True
                else:
                    errors = validation.get("summary", "Unknown error")
                    self.log("FAIL", f"{agent_type}: Validation failed - {errors}")
                    self.add_result(TestResult(f"Agent: {agent_type}", "FAIL", errors))
                    return False
            else:
                msg = f"HTTP {r.status_code}"
                self.log("FAIL", f"{agent_type}: {msg}")
                self.add_result(TestResult(f"Agent: {agent_type}", "FAIL", msg))
                return False
        
        except requests.Timeout:
            self.log("WARN", f"{agent_type}: Timeout (>60s)")
            self.add_result(TestResult(f"Agent: {agent_type}", "TIMEOUT", "Analysis took >60s"))
            return False
        except Exception as e:
            self.log("FAIL", f"{agent_type}: {str(e)}")
            self.add_result(TestResult(f"Agent: {agent_type}", "FAIL", str(e)))
            return False
    
    def run_individual_agent_tests(self, dispute_id: Optional[str] = None):
        """Test all agents individually"""
        self.log("HEADER", "INDIVIDUAL AGENT TESTS")
        
        if not dispute_id:
            dispute_id = input("Enter dispute ID to test: ").strip()
        
        if not dispute_id:
            self.log("FAIL", "No dispute ID provided")
            return
        
        self.dispute_id = dispute_id
        
        # Legal agents
        legal_agents = ["customerLawyer", "companyLawyer", "judge", "independentLawyer"]
        self.log("SUBHEADER", "Testing Legal Agents")
        for agent in legal_agents:
            self.test_individual_agent(agent, dispute_id)
        
        # Operational agents
        operational_agents = ["advocate", "auditor", "summarizer"]
        self.log("SUBHEADER", "Testing Operational Agents")
        for agent in operational_agents:
            self.test_individual_agent(agent, dispute_id)
    
    # ========================================================================
    # EVIDENCE BUNDLE TESTS
    # ========================================================================
    
    def test_evidence_bundle(self, agent_type: str, dispute_id: Optional[str] = None) -> Tuple[bool, Dict]:
        """Test evidence bundle for an agent"""
        if not dispute_id:
            dispute_id = self.dispute_id
        
        if not dispute_id:
            return False, {}
        
        try:
            r = requests.get(
                f"{BASE_URL}/api/disputes/{dispute_id}/evidence",
                params={"agent_type": agent_type},
                timeout=10
            )
            
            if r.status_code != 200:
                return False, {"error": f"HTTP {r.status_code}"}
            
            data = r.json()
            bundle = data.get("bundle", {})
            stats = data.get("stats", {})
            
            # Check for all three tables
            checks = {
                "disputes_table": bool(bundle.get("dispute_record")),
                "transactions_table": bool(len(bundle.get("transactions", [])) > 0),
                "merchant_records_table": bool(bundle.get("merchant_record")),
                "system_logs": len(bundle.get("system_logs", [])) > 0
            }
            
            return all(checks.values()), {
                "checks": checks,
                "stats": stats,
                "bundle_keys": list(bundle.keys())
            }
        
        except Exception as e:
            return False, {"error": str(e)}
    
    def run_evidence_bundle_tests(self, dispute_id: Optional[str] = None):
        """Test evidence bundles for all agents"""
        self.log("HEADER", "EVIDENCE BUNDLE TESTS")
        
        if not dispute_id:
            dispute_id = input("Enter dispute ID: ").strip()
        
        if not dispute_id:
            self.log("FAIL", "No dispute ID provided")
            return
        
        self.dispute_id = dispute_id
        
        all_agents = ["customerLawyer", "companyLawyer", "judge", "independentLawyer"]
        
        for agent in all_agents:
            success, details = self.test_evidence_bundle(agent, dispute_id)
            
            if success:
                self.log("SUCCESS", f"{agent}: Complete evidence bundle")
                checks = details.get("checks", {})
                print(f"    Disputes: {checks.get('disputes_table', False)}")
                print(f"    Transactions: {checks.get('transactions_table', False)}")
                print(f"    Merchant Records: {checks.get('merchant_records_table', False)}")
                self.add_result(TestResult(f"Evidence: {agent}", "PASS", "All tables present"))
            else:
                error = details.get("error", "Unknown error")
                self.log("FAIL", f"{agent}: {error}")
                self.add_result(TestResult(f"Evidence: {agent}", "FAIL", error))
    
    # ========================================================================
    # FULL WORKFLOW TEST
    # ========================================================================
    
    def create_test_dispute(self) -> Optional[str]:
        """Create a test dispute"""
        self.log("SUBHEADER", "[WORKFLOW] Creating Test Dispute")
        
        payload = {
            "customer_email": f"test+{int(time.time())}@example.com",
            "platform": "GrabFood",
            "amount": 45.50,
            "order_id": f"TEST-{int(time.time())}",
            "issue_type": "Not Delivered",
            "raw_text": "Never received my order. My name is John Smith. Phone: +60123456789",
            "evidence_url": "https://example.com/photo.jpg",
            "account_id": "ACC-TEST",
            "api_key": "INTERNAL_PORTAL"
        }
        
        try:
            r = requests.post(f"{BASE_URL}/api/disputes", json=payload, timeout=10)
            
            if r.status_code == 200:
                dispute_id = r.json().get("case_id")
                self.log("SUCCESS", f"Dispute created: {dispute_id}")
                self.add_result(TestResult("Workflow: Create Dispute", "PASS", dispute_id))
                return dispute_id
            else:
                self.log("FAIL", f"Failed to create: {r.status_code}")
                self.add_result(TestResult("Workflow: Create Dispute", "FAIL", f"HTTP {r.status_code}"))
                return None
        except Exception as e:
            self.log("FAIL", f"Error creating dispute: {str(e)}")
            self.add_result(TestResult("Workflow: Create Dispute", "FAIL", str(e)))
            return None
    
    def run_full_workflow_test(self):
        """Test complete end-to-end workflow"""
        self.log("HEADER", "FULL END-TO-END WORKFLOW TEST")
        
        # Step 1: Create dispute
        dispute_id = self.create_test_dispute()
        if not dispute_id:
            return
        
        self.dispute_id = dispute_id
        
        # Step 2: Test evidence
        self.log("SUBHEADER", "[WORKFLOW] Retrieving Evidence")
        success, details = self.test_evidence_bundle("judge", dispute_id)
        if success:
            self.log("SUCCESS", "Evidence retrieved")
            self.add_result(TestResult("Workflow: Get Evidence", "PASS"))
        else:
            self.log("FAIL", f"Evidence failed: {details}")
            self.add_result(TestResult("Workflow: Get Evidence", "FAIL", details.get("error", "")))
        
        # Step 3: Run judge analysis
        self.log("SUBHEADER", "[WORKFLOW] Running Judge Analysis")
        self.test_individual_agent("judge", dispute_id)
        
        # Step 4: Run all legal agents
        self.log("SUBHEADER", "[WORKFLOW] Running All Legal Agents")
        for agent in ["customerLawyer", "companyLawyer", "independentLawyer"]:
            self.test_individual_agent(agent, dispute_id)


def main():
    parser = argparse.ArgumentParser(description="ResolveMesh Agent Testing Suite")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run smoke tests (2 min)"
    )
    parser.add_argument(
        "--individual",
        action="store_true",
        help="Test each agent individually"
    )
    parser.add_argument(
        "--evidence",
        action="store_true",
        help="Test evidence bundles"
    )
    parser.add_argument(
        "--workflow",
        action="store_true",
        help="Test full end-to-end workflow"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests"
    )
    parser.add_argument(
        "--dispute-id",
        type=str,
        help="Dispute ID to use (for testing specific dispute)"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # If no specific test selected, default to smoke
    if not any([args.smoke, args.individual, args.evidence, args.workflow, args.all]):
        args.smoke = True
    
    if args.smoke or args.all:
        runner.run_smoke_tests()
    
    if args.individual or args.all:
        runner.run_individual_agent_tests(args.dispute_id)
    
    if args.evidence or args.all:
        runner.run_evidence_bundle_tests(args.dispute_id)
    
    if args.workflow or args.all:
        runner.run_full_workflow_test()
    
    # Print summary
    runner.print_summary()


if __name__ == "__main__":
    main()
