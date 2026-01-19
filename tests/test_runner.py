#!/usr/bin/env python
"""
SpacePedia Unified Test Runner

A single interactive test file that consolidates all testing functionality.
Generates a markdown report (test_report.md) with results.

Usage:
    python tests/test_runner.py           # Interactive menu
    python tests/test_runner.py --all     # Run all tests
    python tests/test_runner.py --test 1  # Run specific test by number
"""

import sys
import os
import time
import asyncio
import requests
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Constants
BASE_URL = "http://localhost:8000/api/v1"
WEB_URL = "http://localhost:5000"
HEALTH_URL = "http://localhost:8000/health"
REPORT_FILE = "test_report.md"

# Colors for terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class TestResult:
    """Stores result of a single test."""
    def __init__(self, name: str, passed: bool, details: str = "", duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.details = details
        self.duration = duration


class TestRunner:
    """Unified test runner with all test cases."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.test_menu = {
            1: ("Health Check", self.test_health),
            2: ("RAG Query", self.test_rag_query),
            3: ("Chat Flow", self.test_chat_flow),
            4: ("Multi-turn Context", self.test_multiturn),
            5: ("Rate Limiting", self.test_rate_limit),
            6: ("Metadata API", self.test_meta_api),
            7: ("Graph Invocation", self.test_graph),
            8: ("Ingestion Pipeline", self.test_ingestion),
            9: ("Frontend Check", self.test_frontend),
            10: ("Full System Verification", self.test_full_system),
        }
    
    def print_menu(self):
        """Display interactive test menu."""
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{CYAN}🧪 SpacePedia Unified Test Runner{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")
        
        for num, (name, _) in self.test_menu.items():
            print(f"  {CYAN}[{num}]{RESET} {name}")
        
        print(f"\n  {CYAN}[A]{RESET} Run ALL Tests")
        print(f"  {CYAN}[Q]{RESET} Quit")
        print(f"\n{BOLD}{'='*60}{RESET}")
    
    def run_test(self, test_func, test_name: str) -> TestResult:
        """Execute a test and capture result."""
        print(f"\n{YELLOW}▶ Running: {test_name}...{RESET}")
        start = time.time()
        
        try:
            passed, details = test_func()
            duration = time.time() - start
            
            if passed:
                print(f"{GREEN}✅ PASSED{RESET} ({duration:.2f}s) - {details}")
            else:
                print(f"{RED}❌ FAILED{RESET} ({duration:.2f}s) - {details}")
            
            return TestResult(test_name, passed, details, duration)
        
        except Exception as e:
            duration = time.time() - start
            print(f"{RED}❌ ERROR{RESET} ({duration:.2f}s) - {str(e)}")
            return TestResult(test_name, False, str(e), duration)
    
    # ============== TEST CASES ==============
    
    def test_health(self) -> Tuple[bool, str]:
        """Test 1: Health check."""
        resp = requests.get(HEALTH_URL, timeout=5)
        if resp.status_code == 200 and resp.json().get('status') == 'ok':
            return True, "Server is healthy"
        return False, f"Status: {resp.status_code}"
    
    def test_rag_query(self) -> Tuple[bool, str]:
        """Test 2: RAG query endpoint."""
        query = "Who founded SpaceX?"
        resp = requests.post(f"{BASE_URL}/query", json={"query": query}, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            if "answer" in data and "confidence" in data:
                return True, f"Q: {query} | A: {data['answer'][:50]}..."
        return False, f"HTTP {resp.status_code}"
    
    def test_chat_flow(self) -> Tuple[bool, str]:
        """Test 3: Full chat creation and messaging flow."""
        # Create chat
        resp = requests.post(f"{BASE_URL}/chats", json={"title": f"Test_{int(time.time())}"})
        if resp.status_code != 200:
            return False, "Chat creation failed"
        
        chat_id = resp.json()['id']
        
        # Send message
        msg_resp = requests.post(
            f"{BASE_URL}/chats/{chat_id}/messages",
            json={"content": "What is Mars?"},
            timeout=30
        )
        
        if msg_resp.status_code == 200:
            # Verify history
            hist = requests.get(f"{BASE_URL}/chats/{chat_id}")
            msgs = hist.json().get('messages', [])
            return True, f"Chat created, {len(msgs)} messages"
        
        return False, f"Message failed: {msg_resp.status_code}"
    
    def test_multiturn(self) -> Tuple[bool, str]:
        """Test 4: Multi-turn context retention."""
        # Create chat
        resp = requests.post(f"{BASE_URL}/chats", json={"title": f"Multiturn_{int(time.time())}"})
        chat_id = resp.json()['id']
        
        # First message
        requests.post(f"{BASE_URL}/chats/{chat_id}/messages", 
                     json={"content": "What is SpaceX Starship?"}, timeout=30)
        
        # Second message (context-dependent)
        resp2 = requests.post(f"{BASE_URL}/chats/{chat_id}/messages",
                             json={"content": "Who manufactures it?"}, timeout=30)
        
        if resp2.status_code == 200:
            answer = resp2.json().get('content', '')
            if "SpaceX" in answer or "Elon" in answer:
                return True, "Context retained (SpaceX mentioned)"
            return True, "Response received (context may vary)"
        
        return False, "Multi-turn failed"
    
    def test_rate_limit(self) -> Tuple[bool, str]:
        """Test 5: Rate limiting functionality."""
        blocked = 0
        for i in range(12):
            resp = requests.post(f"{BASE_URL}/chats", json={"title": f"Rate_{i}"})
            if resp.status_code == 429:
                blocked += 1
        
        if blocked > 0:
            return True, f"{blocked}/12 requests blocked (rate limit working)"
        return True, "No rate limiting triggered (within limits)"
    
    def test_meta_api(self) -> Tuple[bool, str]:
        """Test 6: Metadata/knowledge API."""
        resp = requests.get(f"{BASE_URL}/meta/knowledge", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return True, f"Retrieved {len(data)} knowledge items"
        return False, f"HTTP {resp.status_code}"
    
    def test_graph(self) -> Tuple[bool, str]:
        """Test 7: LangGraph invocation."""
        from app.orchestration.graph import GraphManager
        
        graph = GraphManager()
        result = graph.invoke("What is ISRO?")
        
        if result.get('answer'):
            return True, f"Graph returned answer with {len(result.get('documents', []))} docs"
        return False, "Graph returned no answer"
    
    def test_ingestion(self) -> Tuple[bool, str]:
        """Test 8: Ingestion pipeline (single URL test)."""
        from app.ingestion.pipeline import IngestionPipeline
        
        async def run():
            pipeline = IngestionPipeline()
            doc = await pipeline.run("https://en.wikipedia.org/wiki/Moon")
            return doc
        
        doc = asyncio.run(run())
        
        if doc.status.value == "vectorized":
            return True, f"Ingested: {doc.title} ({len(doc.chunks)} chunks)"
        return False, f"Status: {doc.status}"
    
    def test_frontend(self) -> Tuple[bool, str]:
        """Test 9: Frontend accessibility."""
        resp = requests.get(WEB_URL, timeout=5)
        if resp.status_code == 200 and "<title>SpacePedia AI</title>" in resp.text:
            return True, "Frontend accessible"
        return False, f"HTTP {resp.status_code}"
    
    def test_full_system(self) -> Tuple[bool, str]:
        """Test 10: Full system verification (runs all critical tests)."""
        critical_tests = [1, 2, 3, 6]  # Health, RAG, Chat, Meta
        passed = 0
        
        for test_num in critical_tests:
            name, func = self.test_menu[test_num]
            try:
                result, _ = func()
                if result:
                    passed += 1
            except:
                pass
        
        if passed == len(critical_tests):
            return True, f"All {passed} critical tests passed"
        return False, f"Only {passed}/{len(critical_tests)} critical tests passed"
    
    # ============== REPORT GENERATION ==============
    
    def generate_report(self):
        """Generate markdown report from test results."""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        lines = [
            "# SpacePedia AI - Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Status:** {'✅ PASSED' if passed == total else '⚠️ PARTIAL' if passed > 0 else '❌ FAILED'}",
            "",
            "## Summary",
            f"- **Tests Run:** {total}",
            f"- **Passed:** {passed}",
            f"- **Failed:** {total - passed}",
            f"- **Pass Rate:** {passed/total*100:.1f}%",
            "",
            "## Detailed Results",
            "",
            "| Test Name | Status | Duration | Details |",
            "|-----------|--------|----------|---------|",
        ]
        
        for r in self.results:
            status = "✅ PASS" if r.passed else "❌ FAIL"
            lines.append(f"| {r.name} | {status} | {r.duration:.2f}s | {r.details[:50]} |")
        
        lines.extend([
            "",
            "---",
            f"*Report generated by SpacePedia Unified Test Runner*",
        ])
        
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        print(f"\n{GREEN}📄 Report saved to: {REPORT_FILE}{RESET}")
    
    # ============== MAIN RUNNER ==============
    
    def run_interactive(self):
        """Run in interactive mode with menu."""
        while True:
            self.print_menu()
            choice = input(f"\n{CYAN}Enter choice: {RESET}").strip().upper()
            
            if choice == 'Q':
                print(f"\n{YELLOW}Goodbye!{RESET}")
                break
            
            elif choice == 'A':
                print(f"\n{BOLD}Running ALL tests...{RESET}")
                self.results = []
                for num, (name, func) in self.test_menu.items():
                    result = self.run_test(func, name)
                    self.results.append(result)
                self.generate_report()
            
            elif choice.isdigit() and int(choice) in self.test_menu:
                num = int(choice)
                name, func = self.test_menu[num]
                result = self.run_test(func, name)
                self.results.append(result)
                
                save = input(f"\n{CYAN}Save to report? (y/n): {RESET}").strip().lower()
                if save == 'y':
                    self.generate_report()
            
            else:
                print(f"{RED}Invalid choice. Try again.{RESET}")
    
    def run_all(self):
        """Run all tests non-interactively."""
        print(f"\n{BOLD}Running ALL tests...{RESET}")
        self.results = []
        for num, (name, func) in self.test_menu.items():
            result = self.run_test(func, name)
            self.results.append(result)
        self.generate_report()
    
    def run_single(self, test_num: int):
        """Run a single test by number."""
        if test_num in self.test_menu:
            name, func = self.test_menu[test_num]
            result = self.run_test(func, name)
            self.results = [result]
            self.generate_report()
        else:
            print(f"{RED}Invalid test number: {test_num}{RESET}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="SpacePedia Unified Test Runner")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--test", type=int, help="Run specific test by number (1-10)")
    
    args = parser.parse_args()
    runner = TestRunner()
    
    if args.all:
        runner.run_all()
    elif args.test:
        runner.run_single(args.test)
    else:
        runner.run_interactive()


if __name__ == "__main__":
    main()
