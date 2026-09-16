"""
Run all tests for the Coastal Watch project.
"""

import os
import sys
import unittest

# Add the project root to the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the project root to the path
sys.path.insert(0, PROJECT_ROOT)


def run_tests():
    """Run all tests in the project."""
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Discover root-level, unit, and integration tests.
    suite.addTests(loader.discover("tests", pattern="test_*.py"))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return the result
    return result

if __name__ == "__main__":
    result = run_tests()
    
    # Exit with error code if tests failed
    if not result.wasSuccessful():
        sys.exit(1)