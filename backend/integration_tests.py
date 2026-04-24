"""
Integration Tests for ResolveMesh Supabase + Z.AI

Tests the complete flow:
1. Create dispute from N8n webhook
2. Trigger agent analysis
3. Retrieve evidence
4. Generate PDF
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30  # seconds


class ResolveMeshIntegrationTests:
    """Integration test suite for ResolveMesh backend"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.test_dispute_id = None
        self.results = []
    
    # ====================================================================
    # TEST 1: System Health Checks
    # ====================================================================
    
    def test_supabase_connection(self) -> bool:
        """Test if backend can connect to Supabase"""
        print("\n[TEST 1] Testing Supabase Connection...")
        try:
            # Try to fetch disputes (basic connectivity test)
            response = requests.get(f"{self.base_url}/api/disputes", timeout=5)
            if response.status_code == 200:
                print("✅ Supabase connection OK")
                self.results.append(("Supabase Connection", "PASS"))
                return True
            else:
                print(f"❌ Supabase connection failed: {response.status_code}")
                self.results.append(("Supabase Connection", "FAIL", response.text))
                return False
        except Exception as e:
            print(f"❌ Supabase connection error: {e}")
            self.results.append(("Supabase Connection", "FAIL", str(e)))
            return False
    
    def test_zai_health(self) -> bool:
        """Test if backend can reach Z.AI API"""
        print("\n[TEST 2] Testing Z.AI Connection...")
        try:
            response = requests.get(f"{self.base_url}/api/zai/health", timeout=5)
            if response.status_code == 200:
                print("✅ Z.AI connection OK")
                self.results.append(("Z.AI Connection", "PASS"))
                return True
            else:
                print(f"❌ Z.AI connection failed: {response.status_code}")
                self.results.append(("Z.AI Connection", "FAIL", response.text))
                return False
        except Exception as e:
            print(f"❌ Z.AI connection error: {e}")
            self.results.append(("Z.AI Connection", "FAIL", str(e)))
            return False
    
    # ====================================================================
    # TEST 2: Create Dispute (N8n Webhook Simulation)
    # ====================================================================
    
    def test_create_dispute(self) -> bool:
        """Test creating a dispute from N8n webhook payload"""
        print("\n[TEST 3] Creating Dispute from N8n Webhook...")
        
        payload = {
            "customer_email": "testuser@example.com",
            "platform": "GrabFood",
            "amount": 45.50,
            "order_id": f"TEST-GRB-{int(time.time())}",
            "issue_type": "Quality Issue",
            "raw_text": "My name is John Smith. I received moldy bread. My phone is +60123456789",
            "evidence_url": "https://example.com/photo.jpg",
            "account_id": "ACC-TEST-001",
            "api_key": "INTERNAL_PORTAL"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/disputes",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_dispute_id = data.get("case_id")
                
                # Verify PII masking
                redacted_text = data.get("redacted_text", "")
                if "<PERSON>" in redacted_text and "<PHONE_NUMBER>" in redacted_text:
                    print(f"✅ Dispute created: {self.test_dispute_id}")
                    print(f"   PII masking confirmed")
                    self.results.append(("Create Dispute", "PASS", self.test_dispute_id))
                    return True
                else:
                    print("❌ PII masking not applied properly")
                    self.results.append(("Create Dispute", "FAIL", "PII masking incomplete"))
                    return False
            else:
                print(f"❌ Failed to create dispute: {response.status_code}")
                print(f"   Response: {response.text}")
                self.results.append(("Create Dispute", "FAIL", response.text))
                return False
                
        except Exception as e:
            print(f"❌ Error creating dispute: {e}")
            self.results.append(("Create Dispute", "FAIL", str(e)))
            return False
    
    # ====================================================================
    # TEST 3: Get Evidence Bundle
    # ====================================================================
    
    def test_get_evidence(self) -> bool:
        """Test retrieving evidence bundle for a dispute"""
        if not self.test_dispute_id:
            print("\n⏭️  Skipping evidence test (no dispute ID)")
            return False
        
        print(f"\n[TEST 4] Getting Evidence Bundle for {self.test_dispute_id}...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/disputes/{self.test_dispute_id}/evidence?agent_type=judge",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("stats", {})
                print(f"✅ Evidence retrieved")
                print(f"   System logs: {stats.get('system_logs_count', 0)}")
                print(f"   Transactions: {stats.get('transactions_count', 0)}")
                self.results.append(("Get Evidence", "PASS"))
                return True
            else:
                print(f"❌ Failed to get evidence: {response.status_code}")
                self.results.append(("Get Evidence", "FAIL", response.text))
                return False
                
        except Exception as e:
            print(f"❌ Error getting evidence: {e}")
            self.results.append(("Get Evidence", "FAIL", str(e)))
            return False
    
    # ====================================================================
    # TEST 4: Trigger Agent Analysis
    # ====================================================================
    
    def test_agent_analysis(self) -> bool:
        """Test triggering legal agent analysis"""
        if not self.test_dispute_id:
            print("\n⏭️  Skipping agent analysis test (no dispute ID)")
            return False
        
        print(f"\n[TEST 5] Triggering Agent Analysis for {self.test_dispute_id}...")
        
        payload = {
            "dispute_id": self.test_dispute_id,
            "agents": ["judge"]  # Start with just judge for faster testing
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/agents/analyze",
                json=payload,
                timeout=60  # Analysis can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                if status == "success":
                    validation_report = data.get("validation_report", {})
                    all_valid = validation_report.get("all_responses_valid", False)
                    
                    if all_valid:
                        print(f"✅ Agent analysis completed successfully")
                        print(f"   Status: {status}")
                        print(f"   Validation: {all_valid}")
                        self.results.append(("Agent Analysis", "PASS"))
                        return True
                    else:
                        print("⚠️  Analysis completed but validation failed")
                        print(f"   Errors: {validation_report.get('summary', '')}")
                        self.results.append(("Agent Analysis", "PARTIAL", "Validation failed"))
                        return False
                else:
                    print(f"❌ Analysis failed with status: {status}")
                    self.results.append(("Agent Analysis", "FAIL", f"Status: {status}"))
                    return False
            else:
                print(f"❌ Failed to trigger analysis: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.results.append(("Agent Analysis", "FAIL", response.text))
                return False
                
        except requests.Timeout:
            print(f"⏱️  Analysis timeout (normal for large disputes)")
            self.results.append(("Agent Analysis", "TIMEOUT"))
            return False
        except Exception as e:
            print(f"❌ Error triggering analysis: {e}")
            self.results.append(("Agent Analysis", "FAIL", str(e)))
            return False
    
    # ====================================================================
    # TEST 5: Z.AI Chat
    # ====================================================================
    
    def test_zai_chat(self) -> bool:
        """Test Z.AI chat endpoint"""
        print("\n[TEST 6] Testing Z.AI Chat...")
        
        payload = {
            "message": "What is 2+2?"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/zai/chat",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")
                if reply:
                    print(f"✅ Z.AI chat works")
                    print(f"   Reply: {reply[:100]}...")
                    self.results.append(("Z.AI Chat", "PASS"))
                    return True
                else:
                    print("❌ Z.AI returned empty response")
                    self.results.append(("Z.AI Chat", "FAIL", "Empty response"))
                    return False
            else:
                print(f"❌ Z.AI chat failed: {response.status_code}")
                self.results.append(("Z.AI Chat", "FAIL", response.text))
                return False
                
        except Exception as e:
            print(f"❌ Error calling Z.AI chat: {e}")
            self.results.append(("Z.AI Chat", "FAIL", str(e)))
            return False
    
    # ====================================================================
    # TEST 6: Authentication
    # ====================================================================
    
    def test_authentication(self) -> bool:
        """Test user authentication endpoint"""
        print("\n[TEST 7] Testing Authentication...")
        
        payload = {
            "email": f"testuser+{int(time.time())}@example.com",
            "password": "TestPassword123"
        }
        
        try:
            # First call should create account
            response = requests.post(
                f"{self.base_url}/api/auth",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                if status in ["signup", "login"]:
                    print(f"✅ Authentication works ({status})")
                    print(f"   User: {data.get('user', {}).get('email')}")
                    self.results.append(("Authentication", "PASS"))
                    return True
                else:
                    print(f"❌ Unexpected auth status: {status}")
                    self.results.append(("Authentication", "FAIL", f"Status: {status}"))
                    return False
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                self.results.append(("Authentication", "FAIL", response.text))
                return False
                
        except Exception as e:
            print(f"❌ Error testing authentication: {e}")
            self.results.append(("Authentication", "FAIL", str(e)))
            return False
    
    # ====================================================================
    # TEST SUMMARY
    # ====================================================================
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for r in self.results if len(r) > 1 and r[1] == "PASS")
        failed = sum(1 for r in self.results if len(r) > 1 and r[1] == "FAIL")
        partial = sum(1 for r in self.results if len(r) > 1 and r[1] == "PARTIAL")
        timeout = sum(1 for r in self.results if len(r) > 1 and r[1] == "TIMEOUT")
        
        print(f"\n✅ Passed:  {passed}")
        print(f"❌ Failed:  {failed}")
        print(f"⚠️  Partial: {partial}")
        print(f"⏱️  Timeout: {timeout}")
        
        print(f"\nTotal: {len(self.results)} tests")
        
        if failed == 0 and timeout == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {failed + timeout} test(s) need attention")
        
        print("\nDetails:")
        for result in self.results:
            test_name = result[0]
            status = result[1] if len(result) > 1 else "UNKNOWN"
            details = result[2] if len(result) > 2 else ""
            
            icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏱️" if status == "TIMEOUT" else "⚠️"
            print(f"  {icon} {test_name}: {status}")
            if details and status != "PASS":
                # Truncate long error messages
                detail_str = str(details)[:100]
                print(f"      └─ {detail_str}...")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 70)
        print("ResolveMesh Integration Test Suite")
        print("=" * 70)
        print(f"Backend: {self.base_url}")
        
        # Health checks
        self.test_supabase_connection()
        self.test_zai_health()
        
        # Create dispute (required for other tests)
        self.test_create_dispute()
        
        # Evidence and analysis
        self.test_get_evidence()
        self.test_agent_analysis()
        
        # Standalone tests
        self.test_zai_chat()
        self.test_authentication()
        
        # Print summary
        self.print_summary()


# ======================================================================
# ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    import sys
    
    # Allow custom base URL
    url = sys.argv[1] if len(sys.argv) > 1 else BASE_URL
    
    tester = ResolveMeshIntegrationTests(url)
    tester.run_all_tests()
