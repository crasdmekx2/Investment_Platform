#!/usr/bin/env python3
"""
Test cycle runner for scheduler API tests.
Recreates containers, runs tests, saves results, and can rerun until all pass.
"""

import subprocess
import sys
import time
import json
import os
from datetime import datetime
from pathlib import Path


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command."""
    print(f"\n{'='*80}")
    print(f"Running: {cmd}")
    print(f"{'='*80}")
    
    result = subprocess.run(
        cmd,
        shell=True,
        check=check,
        capture_output=capture_output,
        text=True if capture_output else None
    )
    
    if capture_output:
        return result.stdout, result.stderr, result.returncode
    return result.returncode


def check_containers_running():
    """Check if docker containers are running."""
    print("\nChecking container status...")
    stdout, stderr, returncode = run_command(
        "docker-compose ps",
        check=False,
        capture_output=True
    )
    
    if returncode != 0:
        print("❌ Failed to check container status")
        return False
    
    # Check for key containers
    required_containers = [
        "investment_platform_db",
        "investment_platform_api",
        "investment_platform_scheduler"
    ]
    
    for container in required_containers:
        if container not in stdout:
            print(f"❌ Container {container} not found")
            return False
    
    print("✅ All required containers are running")
    return True


def recreate_containers():
    """Recreate docker containers."""
    print("\n" + "="*80)
    print("RECREATING DOCKER CONTAINERS")
    print("="*80)
    
    # Stop and remove containers
    print("\nStopping containers...")
    run_command("docker-compose down", check=False)
    
    # Remove volumes (optional - comment out if you want to keep data)
    # print("\nRemoving volumes...")
    # run_command("docker-compose down -v", check=False)
    
    # Build and start containers
    print("\nBuilding and starting containers...")
    run_command("docker-compose build", check=True)
    run_command("docker-compose up -d", check=True)
    
    # Wait for containers to be healthy
    print("\nWaiting for containers to be healthy...")
    max_wait = 120  # 2 minutes
    waited = 0
    
    while waited < max_wait:
        if check_containers_running():
            # Additional health check - wait for API to be ready
            print("Waiting for API to be ready...")
            time.sleep(10)
            
            # Try to connect to API
            try:
                import requests
                response = requests.get("http://localhost:8000/api/health", timeout=5)
                if response.status_code == 200:
                    print("✅ API is ready")
                    return True
            except Exception as e:
                print(f"API not ready yet: {e}")
        
        time.sleep(5)
        waited += 5
        print(f"Waiting... ({waited}s/{max_wait}s)")
    
    print("❌ Containers did not become healthy in time")
    return False


def run_tests():
    """Run the comprehensive test suite."""
    print("\n" + "="*80)
    print("RUNNING TEST SUITE")
    print("="*80)
    print("Note: Tests will stop after first failure for iterative debugging")
    print("      Use --run-all flag in test script to run all tests")
    
    # Check if test script exists
    test_script = Path("test_scheduler_api_comprehensive.py")
    if not test_script.exists():
        print(f"❌ Test script not found: {test_script}")
        return False
    
    # Run tests (default: stop on first failure)
    returncode = run_command(
        f"python {test_script}",
        check=False
    )
    
    return returncode == 0


def find_latest_results():
    """Find the latest test results file."""
    results_dir = Path(".")
    results_files = list(results_dir.glob("scheduler-api-test-results-*.json"))
    
    if not results_files:
        return None
    
    # Sort by modification time, get latest
    latest = max(results_files, key=lambda p: p.stat().st_mtime)
    return latest


def analyze_results(results_file):
    """Analyze test results and return summary."""
    if not results_file or not results_file.exists():
        return None
    
    with open(results_file, "r") as f:
        data = json.load(f)
    
    test_run = data.get("test_run", {})
    results = data.get("results", [])
    
    failed_tests = [
        r for r in results
        if r.get("status") == "FAIL"
    ]
    
    return {
        "total": test_run.get("total_tests", 0),
        "passed": test_run.get("passed", 0),
        "failed": test_run.get("failed", 0),
        "skipped": test_run.get("skipped", 0),
        "failed_tests": [
            {
                "test_id": t.get("test_id"),
                "test_name": t.get("test_name"),
                "error": t.get("error_message"),
            }
            for t in failed_tests
        ],
        "results_file": str(results_file),
    }


def print_summary(summary):
    """Print test summary."""
    if not summary:
        print("\n❌ No test results found")
        return
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    print(f"Total Tests: {summary['total']}")
    print(f"✅ Passed: {summary['passed']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"⏭️  Skipped: {summary['skipped']}")
    
    if summary['failed'] > 0:
        print("\nFailed Tests:")
        for test in summary['failed_tests']:
            print(f"  - {test['test_id']}: {test['test_name']}")
            if test['error']:
                print(f"    Error: {test['error']}")
    
    print(f"\nResults file: {summary['results_file']}")


def main():
    """Main test cycle runner."""
    print("\n" + "="*80)
    print("SCHEDULER API TEST CYCLE RUNNER")
    print("="*80)
    print(f"Start Time: {datetime.now().isoformat()}")
    
    # Check if we should recreate containers
    recreate = "--recreate" in sys.argv or "-r" in sys.argv
    
    if recreate:
        if not recreate_containers():
            print("\n❌ Failed to recreate containers")
            return 1
    else:
        if not check_containers_running():
            print("\n❌ Containers are not running. Use --recreate to recreate them.")
            return 1
    
    # Run tests
    success = run_tests()
    
    # Analyze results
    results_file = find_latest_results()
    summary = analyze_results(results_file)
    print_summary(summary)
    
    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Test failed. Review the results and fix the issue.")
        if summary and summary['failed'] > 0:
            first_failure = summary['failed_tests'][0]
            print(f"\nFocus on fixing: {first_failure['test_id']} - {first_failure['test_name']}")
            if first_failure['error']:
                print(f"Error: {first_failure['error']}")
        print("\nAfter fixing, remove the failing test from the script or fix the issue,")
        print("then rerun: python run_scheduler_api_tests_cycle.py --recreate")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

