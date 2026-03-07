#!/usr/bin/env python3
"""
BVA Main Entry Point - Python 3 Compatible Version
Wrapper script to configure and run src/mcmc.py
"""

import argparse
import sys
import subprocess
import os

# ============================================================================
# Argument Parsing
# ============================================================================

defaultMessage = '[BVA] config and run ... '
parser = argparse.ArgumentParser(description=defaultMessage)

parser.add_argument('-v', '--version', help='print BVA version', 
                   required=False, action='store_true', default=False)

parser.add_argument('-r', '--run', help='run src/mcmc.py', 
                   required=False, action="store_true", default=False)

# Fix: Default should be None instead of False for integer argument
parser.add_argument('-n', '--niter', help='specify niter in scipy.optimize.basinhopping', 
                   required=False, type=int, default=None)

parser.add_argument('--verbose', help='output the parsed options', 
                   required=False, action='store_true', default=False)

# Parse arguments
results = parser.parse_args()

# ============================================================================
# Logic Flow
# ============================================================================

# 1. Handle Version (should be checked before run)
if results.version:
    print("BVA version: v_D2a")
    sys.exit(0)

# 2. Handle Verbose (show config before running)
if results.verbose:
    print("results.run     =", results.run)
    print("results.version =", results.version)
    print("results.niter   =", results.niter)
    # Don't exit here, allow run to proceed if --run is also set

# 3. Handle Run
if results.run:
    # Determine script path (ensure it works regardless of cwd)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mcmc_path = os.path.join(script_dir, 'src', 'mcmc.py')
    
    # Build command list
    # Use sys.executable to ensure same Python interpreter is used
    cmd = [sys.executable, mcmc_path]
    
    # Add niter argument if specified
    if results.niter is not None:
        if results.niter < 0:
            print("Error: niter cannot be negative")
            sys.exit(1)
        cmd.extend(['-n', str(results.niter)])
    
    # Execute
    try:
        # Fix: Original code had undefined variable 'niter' and missing str() conversion
        subprocess.call(cmd)
    except FileNotFoundError:
        print(f"Error: Cannot find mcmc.py at {mcmc_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running mcmc.py: {e}")
        sys.exit(1)
    
    sys.exit(0)

# 4. If no action specified, show help
if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

# 5. Exit gracefully if only verbose was specified without run
sys.exit(0)