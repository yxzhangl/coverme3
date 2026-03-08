#!/usr/bin/env python3
"""
BVA Main Entry Point - Python 3 Compatible Version
Wrapper script to configure and run src/mcmc.py

Modified: Add multi-distance strategy support for branch penalty calculation
"""

import argparse
import sys
import subprocess
import os

# ============================================================================
# Argument Parsing
# ============================================================================

distance_help = '''Distance strategy for branch penalty calculation:
  0: ABSOLUTE  - |x-y| (default, original)
  1: RELATIVE  - |x-y|/max(|x|,|y|,ε)
  2: LINEAR    - |x-y| (same as ABSOLUTE, for interface consistency)
  3: NORMALIZED- |x-y|/(1+|x|+|y|), output in [0,1)
  4: LOG       - |log(1+|x|)-log(1+|y|)|, good for large dynamic range
  99: AUTO     - adaptive selection based on value magnitude
'''

defaultMessage = '[BVA] config and run ... '
parser = argparse.ArgumentParser(description=defaultMessage)

# FIX: Use -V for version (free up -v for verbose level)
parser.add_argument('-V', '--version', help='print BVA version', 
                   required=False, action='store_true', default=False)

parser.add_argument('-r', '--run', help='run src/mcmc.py', 
                   required=False, action="store_true", default=False)

parser.add_argument('-n', '--niter', help='specify niter in scipy.optimize.basinhopping', 
                   required=False, type=int, default=None)

# FIX: -v now accepts integer verbose level (0-3)
parser.add_argument('-v', '--verbose', help='verbose level (0=quiet, 1=basic, 2=detailed, 3=debug)', 
                   required=False, type=int, default=0, choices=[0, 1, 2, 3])

# NEW: Distance strategy parameter
parser.add_argument('-d', '--distance', 
                   help=distance_help,
                   action='store', 
                   type=int, 
                   default=0, 
                   choices=[0, 1, 2, 3, 4, 99])

parser.add_argument('--dist-debug', 
                   help='print distance strategy info during run',
                   action='store_true', 
                   default=False)

# Parse arguments (variable name is 'results', NOT 'args'!)
results = parser.parse_args()

# ============================================================================
# Logic Flow
# ============================================================================

# 1. Handle Version
if results.version:
    print("BVA version: v_D2a")
    sys.exit(0)

# 2. Handle Verbose (show config before running)
if results.verbose > 0:
    print("[BVA] Configuration:")
    print("  run      =", results.run)
    print("  version  =", results.version)
    print("  niter    =", results.niter)
    print("  distance =", results.distance)
    print("  verbose  =", results.verbose)
    print("  dist_debug =", results.dist_debug)

# 3. Handle Run
if results.run:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mcmc_path = os.path.join(script_dir, 'src', 'mcmc.py')
    
    # Build command list
    cmd = [sys.executable, mcmc_path]
    
    # Add niter argument if specified
    if results.niter is not None:
        if results.niter < 0:
            print("Error: niter cannot be negative")
            sys.exit(1)
        cmd.extend(['-n', str(results.niter)])
    
    # Add verbose argument to mcmc.py if needed
    if results.verbose > 0:
        cmd.extend(['-v', str(results.verbose)])
    
    # ========================================================================
    # Set distance strategy in C library via ctypes
    # ========================================================================
    try:
        import ctypes
        lib_path = os.path.join(script_dir, 'build', 'libr.so')
        
        if os.path.exists(lib_path):
            lib = ctypes.CDLL(lib_path)
            if hasattr(lib, 'set_distance_strategy'):
                lib.set_distance_strategy(results.distance)
                if results.dist_debug or results.verbose >= 1:
                    strat_names = {0:'ABSOLUTE', 1:'RELATIVE', 2:'LINEAR', 
                                  3:'NORMALIZED', 4:'LOG', 99:'AUTO'}
                    name = strat_names.get(results.distance, 'UNKNOWN')
                    print(f"[BVA] ✓ Distance strategy set: {results.distance} ({name})")
            else:
                print("[BVA Warning] libr.so does not export set_distance_strategy()")
                print("  Please recompile: make clean && make build/libr.so")
        else:
            # Don't exit here - let mcmc.py handle its own errors
            if results.verbose >= 1:
                print(f"[BVA Info] libr.so not found at {lib_path}")
                print("  Distance strategy will use default (ABSOLUTE)")
    except Exception as e:
        if results.verbose >= 1:
            print(f"[BVA Warning] Failed to set distance strategy: {type(e).__name__}: {e}")
    # ========================================================================
    
    # Execute mcmc.py
    if results.verbose >= 2:
        print(f"[BVA] Executing: {' '.join(cmd)}")
    
    try:
        return_code = subprocess.call(cmd)
        if return_code != 0 and results.verbose >= 1:
            print(f"[BVA Warning] mcmc.py exited with code {return_code}")
    except FileNotFoundError:
        print(f"Error: Cannot find mcmc.py at {mcmc_path}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[BVA] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error running mcmc.py: {type(e).__name__}: {e}")
        sys.exit(1)
    
    sys.exit(0)

# 4. If no action specified, show help
if len(sys.argv) == 1:
    parser.print_help()
    print("\nQuick start examples:")
    print("  python3 bva.py -r -n 50          # Run with 50 iterations (default distance)")
    print("  python3 bva.py -r -d 4 -n 30     # Run with LOG distance strategy")
    print("  python3 bva.py -r -d 99 -v 2     # Run with AUTO strategy, verbose output")
    print("  python3 bva.py -V                 # Show version")
    sys.exit(1)

# 5. Exit gracefully
sys.exit(0)