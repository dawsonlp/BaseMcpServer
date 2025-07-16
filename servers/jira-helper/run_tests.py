#!/usr/bin/env python3
"""
Test runner that sets up proper PYTHONPATH for src/ layout.

This script adds the src/ directory to Python path so that imports work correctly
during development, following the best practice src/ layout pattern.
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """Add src directory to Python path."""
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    src_dir = script_dir / "src"
    
    # Add src directory to Python path if it exists
    if src_dir.exists():
        src_path = str(src_dir.absolute())
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
            print(f"Added {src_path} to Python path")
    else:
        print(f"Warning: src directory not found at {src_dir}")

def run_test_file(test_file):
    """Run a specific test file."""
    if not os.path.exists(test_file):
        print(f"Error: Test file {test_file} not found")
        return False
    
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print(f"{'='*60}")
    
    try:
        # Execute the test file
        with open(test_file, 'r') as f:
            code = compile(f.read(), test_file, 'exec')
            exec(code)
        return True
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False

def main():
    """Main test runner."""
    # Setup Python path first
    setup_python_path()
    
    # List of test files to run
    test_files = [
        "test_phase4_application.py",
        "test_phase3_infrastructure.py",
        "test_phase3_complete.py"
    ]
    
    # If specific test file provided as argument, run only that
    if len(sys.argv) > 1:
        test_files = [sys.argv[1]]
    
    print("Python path:")
    for path in sys.path[:5]:  # Show first 5 paths
        print(f"  {path}")
    
    # Run tests
    passed = 0
    failed = 0
    
    for test_file in test_files:
        if run_test_file(test_file):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    
    if failed > 0:
        print(f"\n❌ {failed} test(s) failed")
        sys.exit(1)
    else:
        print(f"\n✅ All {passed} test(s) passed!")

if __name__ == "__main__":
    main()
