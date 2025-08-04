# test_streamlit.py - Test the Streamlit UI functionality

import requests
import json
import time
from typing import Dict, Any

class StreamlitUITester:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.test_user = {
            "username": "streamlit_tester",
            "email": "streamlit@test.com",
            "password": "testpass123"
        }
        self.access_token = None
    
    def test_api_connectivity(self) -> Dict[str, Any]:
        """Test API connectivity"""
        print("🔍 Testing API connectivity...")
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API is healthy and reachable")
                return {"success": True, "data": response.json()}
            else:
                print(f"❌ API returned status {response.status_code}")
                return {"success": False, "error": f"Status {response.status_code}"}
        except Exception as e:
            print(f"❌ API connectivity failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_user_registration(self) -> Dict[str, Any]:
        """Test user registration"""
        print("📝 Testing user registration...")
        try:
            # Clean up existing test user first
            self.cleanup_test_user()
            
            response = requests.post(
                f"{self.api_base_url}/auth/register",
                data=self.test_user,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ User registration successful")
                return {"success": True, "data": response.json()}
            else:
                print(f"❌ Registration failed: {response.status_code}")
                return {"success": False, "error": response.text}
        except Exception as e:
            print(f"❌ Registration error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_user_login(self) -> Dict[str, Any]:
        """Test user login"""
        print("🔐 Testing user login...")
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/login",
                data={
                    "username": self.test_user["username"],
                    "password": self.test_user["password"]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                print("✅ User login successful")
                return {"success": True, "data": data}
            else:
                print(f"❌ Login failed: {response.status_code}")
                return {"success": False, "error": response.text}
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_document_listing(self) -> Dict[str, Any]:
        """Test document listing"""
        print("📚 Testing document listing...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.api_base_url}/documents",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Document listing successful - Found {len(data.get('documents', []))} documents")
                return {"success": True, "data": data}
            else:
                print(f"❌ Document listing failed: {response.status_code}")
                return {"success": False, "error": response.text}
        except Exception as e:
            print(f"❌ Document listing error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_system_stats(self) -> Dict[str, Any]:
        """Test system statistics"""
        print("📊 Testing system statistics...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.api_base_url}/stats",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ System statistics retrieved successfully")
                return {"success": True, "data": data}
            else:
                print(f"❌ System stats failed: {response.status_code}")
                return {"success": False, "error": response.text}
        except Exception as e:
            print(f"❌ System stats error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_api_key_creation(self) -> Dict[str, Any]:
        """Test API key creation"""
        print("🔑 Testing API key creation...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            data = {
                "name": "Streamlit Test Key",
                "expires_days": 7
            }
            response = requests.post(
                f"{self.api_base_url}/auth/api-keys",
                data=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API key creation successful")
                return {"success": True, "data": data}
            else:
                print(f"❌ API key creation failed: {response.status_code}")
                return {"success": False, "error": response.text}
        except Exception as e:
            print(f"❌ API key creation error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def cleanup_test_user(self):
        """Clean up test user if exists"""
        try:
            # Try to login and delete any existing test data
            response = requests.post(
                f"{self.api_base_url}/auth/login",
                data={
                    "username": self.test_user["username"],
                    "password": self.test_user["password"]
                },
                timeout=5
            )
            
            if response.status_code == 200:
                print("🧹 Cleaning up existing test user...")
                # User exists, could clean up here if needed
        except:
            pass  # User doesn't exist, which is fine
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Streamlit UI Backend Tests")
        print("=" * 50)
        
        tests = [
            ("API Connectivity", self.test_api_connectivity),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Document Listing", self.test_document_listing),
            ("System Statistics", self.test_system_stats),
            ("API Key Creation", self.test_api_key_creation),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result
                if result["success"]:
                    passed += 1
                print()
            except Exception as e:
                print(f"❌ {test_name} crashed: {str(e)}")
                results[test_name] = {"success": False, "error": str(e)}
                print()
        
        # Summary
        print("📋 Test Summary")
        print("=" * 50)
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        print(f"📊 Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! Streamlit UI should work correctly.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check the API configuration.")
        
        return results

def main():
    """Main test function"""
    tester = StreamlitUITester()
    results = tester.run_all_tests()
    
    # Print detailed results if any tests failed
    failed_tests = [name for name, result in results.items() if not result["success"]]
    if failed_tests:
        print(f"\n🔍 Failed Test Details:")
        for test_name in failed_tests:
            error = results[test_name]["error"]
            print(f"  • {test_name}: {error}")

if __name__ == "__main__":
    main()
