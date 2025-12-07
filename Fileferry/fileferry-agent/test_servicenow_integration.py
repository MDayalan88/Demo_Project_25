"""
ServiceNow Integration Test Script
Tests connection and ticket creation with your ServiceNow instance
"""

import os
import sys
import asyncio
import aiohttp
import json
from typing import Dict, Any

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'


class ServiceNowTester:
    """Test ServiceNow integration"""
    
    def __init__(self, instance_url: str, username: str, password: str):
        self.instance_url = instance_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth = aiohttp.BasicAuth(username, password)
        
    async def test_connection(self) -> bool:
        """Test basic connection to ServiceNow"""
        print(f"\n{YELLOW}🔍 Testing ServiceNow Connection...{RESET}")
        print(f"   Instance: {self.instance_url}")
        print(f"   Username: {self.username}")
        
        url = f"{self.instance_url}/api/now/table/incident?sysparm_limit=1"
        
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"{GREEN}✅ Connection successful!{RESET}")
                        print(f"   Status Code: {response.status}")
                        return True
                    else:
                        print(f"{RED}❌ Connection failed!{RESET}")
                        print(f"   Status Code: {response.status}")
                        text = await response.text()
                        print(f"   Response: {text}")
                        return False
        except Exception as e:
            print(f"{RED}❌ Connection error: {str(e)}{RESET}")
            return False
    
    async def check_assignment_group(self, group_name: str = "DataOps") -> Dict[str, Any]:
        """Check if assignment group exists"""
        print(f"\n{YELLOW}🔍 Checking Assignment Group: {group_name}...{RESET}")
        
        url = f"{self.instance_url}/api/now/table/sys_user_group"
        params = {"sysparm_query": f"name={group_name}"}
        
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('result', [])
                        
                        if results:
                            group = results[0]
                            print(f"{GREEN}✅ Group found!{RESET}")
                            print(f"   Group Name: {group.get('name')}")
                            print(f"   Group Sys ID: {group.get('sys_id')}")
                            return group
                        else:
                            print(f"{YELLOW}⚠️  Group '{group_name}' not found{RESET}")
                            print(f"   You'll need to create this group in ServiceNow")
                            return {}
                    else:
                        print(f"{RED}❌ Failed to check group{RESET}")
                        return {}
        except Exception as e:
            print(f"{RED}❌ Error checking group: {str(e)}{RESET}")
            return {}
    
    async def create_test_ticket(self) -> Dict[str, Any]:
        """Create a test incident ticket"""
        print(f"\n{YELLOW}🎫 Creating Test Ticket...{RESET}")
        
        url = f"{self.instance_url}/api/now/table/incident"
        
        payload = {
            "short_description": "FileFerry Test - Integration Test",
            "description": """This is a test ticket created by FileFerry agent.
            
Test Details:
- Source: test-bucket/sample-file.csv
- Destination: ftp://ftp.example.com/uploads/
- Status: Testing ServiceNow integration
- Timestamp: """ + str(asyncio.get_event_loop().time()),
            "urgency": "2",
            "impact": "2",
            "assignment_group": "DataOps",
            "caller_id": self.username
        }
        
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 201:
                        data = await response.json()
                        result = data.get('result', {})
                        print(f"{GREEN}✅ Test ticket created successfully!{RESET}")
                        print(f"   Ticket Number: {CYAN}{result.get('number')}{RESET}")
                        print(f"   Sys ID: {result.get('sys_id')}")
                        print(f"   State: {result.get('state')}")
                        print(f"   View: {self.instance_url}/incident.do?sys_id={result.get('sys_id')}")
                        return result
                    else:
                        print(f"{RED}❌ Failed to create ticket{RESET}")
                        print(f"   Status Code: {response.status}")
                        text = await response.text()
                        print(f"   Response: {text}")
                        return {}
        except Exception as e:
            print(f"{RED}❌ Error creating ticket: {str(e)}{RESET}")
            return {}
    
    async def update_test_ticket(self, sys_id: str) -> bool:
        """Update the test ticket"""
        print(f"\n{YELLOW}📝 Updating Test Ticket...{RESET}")
        
        url = f"{self.instance_url}/api/now/table/incident/{sys_id}"
        
        payload = {
            "work_notes": "FileFerry Integration Test - Ticket updated successfully!",
            "state": "2"  # In Progress
        }
        
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.patch(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get('result', {})
                        print(f"{GREEN}✅ Ticket updated successfully!{RESET}")
                        print(f"   State: In Progress")
                        print(f"   Work notes added")
                        return True
                    else:
                        print(f"{RED}❌ Failed to update ticket{RESET}")
                        return False
        except Exception as e:
            print(f"{RED}❌ Error updating ticket: {str(e)}{RESET}")
            return False
    
    async def close_test_ticket(self, sys_id: str) -> bool:
        """Close the test ticket"""
        print(f"\n{YELLOW}✔️  Closing Test Ticket...{RESET}")
        
        url = f"{self.instance_url}/api/now/table/incident/{sys_id}"
        
        payload = {
            "state": "6",  # Resolved
            "close_notes": "FileFerry integration test completed successfully.",
            "close_code": "Resolved by Caller"
        }
        
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.patch(url, json=payload) as response:
                    if response.status == 200:
                        print(f"{GREEN}✅ Ticket closed successfully!{RESET}")
                        return True
                    else:
                        print(f"{RED}❌ Failed to close ticket{RESET}")
                        return False
        except Exception as e:
            print(f"{RED}❌ Error closing ticket: {str(e)}{RESET}")
            return False
    
    async def run_full_test(self):
        """Run complete test suite"""
        print(f"\n{CYAN}{'='*60}{RESET}")
        print(f"{CYAN}  FileFerry ServiceNow Integration Test{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        
        # Test 1: Connection
        if not await self.test_connection():
            print(f"\n{RED}❌ Connection test failed. Please check your credentials.{RESET}")
            return False
        
        # Test 2: Check assignment group
        await self.check_assignment_group("DataOps")
        
        # Test 3: Create ticket
        ticket = await self.create_test_ticket()
        if not ticket:
            print(f"\n{RED}❌ Failed to create test ticket{RESET}")
            return False
        
        sys_id = ticket.get('sys_id')
        
        # Test 4: Update ticket
        await self.update_test_ticket(sys_id)
        
        # Test 5: Close ticket
        await self.close_test_ticket(sys_id)
        
        print(f"\n{CYAN}{'='*60}{RESET}")
        print(f"{GREEN}✅ All tests passed! ServiceNow integration is working.{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"\n{YELLOW}Next Steps:{RESET}")
        print(f"  1. Update your .env file with ServiceNow credentials")
        print(f"  2. Restart the FileFerry backend API")
        print(f"  3. Create transfers to automatically generate tickets")
        print(f"\n{YELLOW}View tickets in ServiceNow:{RESET}")
        print(f"  {self.instance_url}/incident_list.do")
        print()
        
        return True


async def main():
    """Main test execution"""
    print(f"\n{CYAN}FileFerry ServiceNow Integration Tester{RESET}\n")
    
    # Get credentials from environment or user input
    instance_url = os.getenv('SERVICENOW_INSTANCE_URL')
    username = os.getenv('SERVICENOW_USERNAME')
    password = os.getenv('SERVICENOW_PASSWORD')
    
    if not instance_url:
        instance_url = input("Enter ServiceNow Instance URL (e.g., https://dev12345.service-now.com): ").strip()
    
    if not username:
        username = input("Enter ServiceNow Username (default: admin): ").strip() or "admin"
    
    if not password:
        import getpass
        password = getpass.getpass("Enter ServiceNow Password: ")
    
    if not instance_url or not username or not password:
        print(f"{RED}❌ Missing credentials. Please provide all required information.{RESET}")
        return
    
    # Run tests
    tester = ServiceNowTester(instance_url, username, password)
    await tester.run_full_test()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}❌ Unexpected error: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
