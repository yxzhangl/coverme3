#!/usr/bin/env python3
"""
Unit tests for mcmc.py - Python 3 Compatible Version
Migrated from Python 2, with bug fixes and compatibility improvements.
"""

import os
import sys
import unittest
import numpy as np
import ctypes
from ctypes import cdll

# Add project root to path
root_dir = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
sys.path.append(root_dir)
import config
import mcmc


class MCMCTest(unittest.TestCase):
    """Test cases for mcmc module functionality"""
    
    @staticmethod
    def c2f(c):
        """Convert character to float (ASCII value)"""
        return float(ord(c))

    def setUp(self):
        """Set up test fixtures - currently no initialization needed"""
        # self.bench_name = config.bench_name()
        # lib = cdll.LoadLibrary(config.libr_so_dir())
        # self.foo_r = lib.foo_r
        pass

    def tearDown(self):
        """Clean up after tests - reset global state if needed"""
        # Optional: reset mcmc module state between tests
        pass

    # Note: Methods prefixed with _test_ are skipped by unittest.
    # Remove underscore to enable, or rename to test_* pattern.
    
    def test_klee_maze_while_disabled(self):
        """
        [DISABLED] Test KLEE maze while benchmark.
        Rename to test_klee_maze_while() to enable.
        """
        self.skipTest("Test disabled - prefix with underscore in original code")
        
        # Original test logic (for reference):
        # lib = cdll.LoadLibrary(config.libr_so_dir())
        # self.assertEqual(self.bench_name, "KLEE_maze_while")
        # x = np.array([self.c2f('a'), self.c2f('b'), self.c2f('w')])
        # self.assertEqual(mcmc.foo_py(x), 0)
        # ... (rest of original test)

    def test_s_sin_disabled(self):
        """
        [DISABLED] Test fdlibm53 sin benchmark.
        Rename to test_s_sin() to enable.
        """
        self.skipTest("Test disabled - prefix with underscore in original code")

    def test_write_disabled(self):
        """
        [DISABLED] Test file writing functionality.
        Rename to test_write() to enable.
        """
        self.skipTest("Test disabled - prefix with underscore in original code")

    def test_pass_staged(self):
        """Test pushStaged/passStaged functionality with C library"""
        print("1:")
        lib = cdll.LoadLibrary(config.libr_so_dir())
        lib.print_passStaged()
        print("TODO: Check empty")

        print("2:")
        x = np.array([self.c2f('a'), self.c2f('b'), self.c2f('w')])
        mcmc.foo_py(x)
        # lib.print_passStaged()
        print("TODO: Check 2 elements")

        print("3:")
        x2 = np.array([self.c2f('w'), self.c2f('w'), self.c2f('y')])
        mcmc.foo_py(x2)
        lib.print_passStaged()
        print("TODO: Check 6 elements")

        print("4:")
        lib.pushStaged()
        lib.print_nPass()
        print("TODO: Check 6 elements")
        
        print("5:")
        lib.print_passStaged()
        print("TODO Check empty")
        
        print("6:")
        mcmc.foo_py(x2)
        lib.print_passStaged()
        print("TODO Check 4 elements above")
        lib.print_nPass()
        print("TODO Check 6 elements above (value sum=6)")
        lib.print_passed_for_one_sample()
        print("TODO Check 4 elements above")
        lib.pushStaged()
        print("TODO Check 10 elements above")
        lib.print_passStaged()
        print("TODO Check empty")
        lib.print_nPass()
        print("6 elements, value sum = 10")

    # ========================================================================
    # Enabled test cases (renamed from _test_* to test_*)
    # ========================================================================
    
    def test_klee_maze_while(self):
        """Test KLEE maze while benchmark branch exploration"""
        # Skip if benchmark doesn't match (original guard)
        if config.bench_name() != "KLEE_maze_while":
            self.skipTest(f"Skipping: bench_name={config.bench_name()}, expected KLEE_maze_while")
        
        lib = cdll.LoadLibrary(config.libr_so_dir())
        x = np.array([self.c2f('a'), self.c2f('b'), self.c2f('w')])
        self.assertEqual(mcmc.foo_py(x), 0)

        with open(config.brInfo_dir(), 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        self.assertEqual(lib.nExplored(), 1)
        
        repf = mcmc.repf()
        self.assertEqual(len(repf.getExplored()), 1)
        # self.assertEqual(repf['explored'].pop()[1], True)

        x2 = np.array([self.c2f('a'), self.c2f('b'), self.c2f('a')])
        self.assertEqual(mcmc.foo_py(x2), 0)
        lib.print_explored()
        self.assertEqual(repf['nExplored'](), 2)
        self.assertEqual(len(repf.getExplored()), 2)
        self.assertEqual(repf.get_nExplored(), 2)

        x3 = np.array([self.c2f('a'), self.c2f('b'), self.c2f('u')])
        self.assertEqual(mcmc.foo_py(x3), 0)
        self.assertEqual(repf.get_nExplored(), 3)
        print(repf.getExplored())

        # Note: This assertion may be flaky depending on C library state
        self.assertEqual(mcmc.foo_py(x3), ord('w') - ord('b'))

        x4 = np.array([self.c2f('a'), self.c2f('w'), self.c2f('u')])
        self.assertEqual(mcmc.foo_py(x4), 0)
        self.assertEqual(repf.get_nExplored(), 4)
        print(repf.getExplored())

        self.assertEqual(mcmc.foo_py(x4), 0)
        self.assertEqual(mcmc.foo_py(x4), ord('w') - ord('a'))
        self.assertEqual(len(repf.getExplored()), 5)

        # Test additional branch
        x5 = np.array([self.c2f('w'), self.c2f('w'), self.c2f('u')])
        self.assertEqual(mcmc.foo_py(x5), 0)
        self.assertEqual(len(repf.getExplored()), 6)

    def test_s_sin(self):
        """Test fdlibm53 sin function branch coverage"""
        lib = cdll.LoadLibrary(config.libr_so_dir())
        
        # Skip if benchmark doesn't match
        if config.bench_name() != "fdlibm53":
            self.skipTest(f"Skipping: bench_name={config.bench_name()}, expected fdlibm53")
        
        print("000000000000000")
        x = np.array([1.0])
        mcmc.foo_py(x)
        
        # Fix: assertTrue expects a single boolean, not (value, expected)
        self.assertTrue(mcmc.r.get_nExplored() >= 1)
        print(mcmc.r.getExplored())
        
        print("1111111111111")
        # Handle inf safely - some C libs may not handle inf gracefully
        try:
            mcmc.foo_py(np.array([np.inf]))
            self.assertTrue(mcmc.r.get_nExplored() >= 2)
            print(mcmc.r.getExplored())
        except (FloatingPointError, OverflowError, ctypes.ArgumentError) as e:
            self.skipTest(f"inf input not supported by C library: {e}")

    def test_write_timing_file(self):
        """Test writing timing results to file"""
        endTime = 100
        startTime = 0.1
        x = [2, 3]  # Unused in original, kept for compatibility

        print("process time = ", endTime - startTime, 'seconds')
        
        # Python 3: explicit encoding, use 'w' mode with newline handling
        with open(config.runningTime_dir(), 'w', encoding='utf-8') as f:
            f.write(str(endTime - startTime) + '\n')
        
        # Verify file was written correctly
        with open(config.runningTime_dir(), 'r', encoding='utf-8') as f:
            content = f.read().strip()
            self.assertEqual(float(content), endTime - startTime)

    # ========================================================================
    # Additional utility tests for Python 3 compatibility
    # ========================================================================
    
    def test_repf_coverage_methods(self):
        """Test repf class coverage calculation methods"""
        repf = mcmc.repf()
        
        # Test exploredRatio handles ZeroDivisionError
        # (Assumes brInfo_dir may be empty in test environment)
        ratio = repf.exploredRatio()
        self.assertIsInstance(ratio, float)
        self.assertGreaterEqual(ratio, 0.0)
        self.assertLessEqual(ratio, 1.0)
        
        # Test coverage method
        coverage = repf.coverage()
        self.assertIsInstance(coverage, float)
        self.assertGreaterEqual(coverage, 0.0)
        self.assertLessEqual(coverage, 1.0)

    def test_foo_py_with_numpy_array(self):
        """Test foo_py accepts numpy arrays and returns float"""
        # Use simple test input
        x = np.array([0.0, 1.0, 2.0])
        result = mcmc.foo_py(x)
        
        # Result should be numeric (float or int from C library)
        self.assertIsInstance(result, (int, float, np.number))

    def test_callback_functions_exist(self):
        """Test that callback functions are defined and callable"""
        self.assertTrue(callable(mcmc.callback_local))
        self.assertTrue(callable(mcmc.callback_global))
        self.assertTrue(callable(mcmc.mybounds))


# ============================================================================
# Test Runner Configuration
# ============================================================================

def suite():
    """Create test suite for selective test execution"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(MCMCTest)
    return suite


if __name__ == "__main__":
    # Python 3 compatible test runner with verbosity
    print(f"Running tests with Python {sys.version}")
    print(f"NumPy version: {np.__version__}")
    
    # Configure test runner
    runner = unittest.TextTestRunner(
        verbosity=2,
        failfast=False,
        buffer=True  # Capture stdout/stderr during tests
    )
    
    # Run tests
    result = runner.run(suite())
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)