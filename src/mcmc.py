#!/usr/bin/env python3
"""
BVA (Branch Coverage via Basin Hopping) - Python 3 Compatible Version
Migrated from Python 2, with bug fixes and compatibility improvements.
"""

import os
import sys
import time
import numpy as np
import scipy.optimize as op
import ctypes
from ctypes import cdll
import argparse
from configparser import ConfigParser  # Python 3: was ConfigParser
import collections

# ============================================================================
# Configuration & Constants
# ============================================================================

class Verbose:
    """Verbosity levels for logging"""
    Silent, Alert, Routine, Debug = range(4)

root_dir = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
sys.path.append(root_dir)
import config

loader_dir = config.loader_dir()
sys.path.append(loader_dir)
import loader

# Global storage for explored branches
bv_original = collections.OrderedDict()
bv = collections.OrderedDict()

# Load shared library
lib = cdll.LoadLibrary(config.libr_so_dir())
lib.foo_r.restype = ctypes.c_double

# ============================================================================
# Coverage Tracking Class (repf)
# ============================================================================

from collections import UserDict  # Python 3: was from UserDict import UserDict

class repf(UserDict):
    """Track explored branches and coverage metrics"""
    
    def __init__(self):
        UserDict.__init__(self)
        self['nExplored'] = lib.nExplored
        self['explored'] = self.getExplored

    def getExplored(self):
        """Get set of explored branches from C library"""
        lib.explored_part1.restype = ctypes.POINTER(ctypes.c_int)
        lib.explored_part2.restype = ctypes.POINTER(ctypes.c_int)

        a = lib.explored_part1()
        b = lib.explored_part2()

        ret = set()
        for i in range(lib.nExplored()):
            ret.add((a[i], (b[i] == 1)))
        return ret
    
    def get_nExplored(self):
        return lib.nExplored()
    
    def get_nCovered(self):
        return lib.nCovered()
          
    def get_nConditionStatement(self):
        with open(config.brInfo_dir(), 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    
    def exploredRatio(self):
        try:
            return self.get_nExplored() * 1.0 / (self.get_nConditionStatement() * 2.0)
        except ZeroDivisionError:
            print('No branches detected, considered as full coverage: 100%')
            return 1.0
    
    def coverage(self):
        try:
            return self.get_nCovered() * 1.0 / (self.get_nConditionStatement() * 2.0)
        except ZeroDivisionError:
            print('No branches detected, considered as full coverage: 100%')
            return 1.0

r = repf()

# ============================================================================
# Core Functions
# ============================================================================

def foo_py(x):
    """
    Objective function for basin hopping.
    Calls C library function and tracks branch exploration.
    
    Parameters:
        x: numpy array of input parameters
    Returns:
        float: objective value from C library
    """
    explored0 = r.get_nExplored()
    x2 = x.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    ret = lib.foo_r(x2)
    explored1 = r.get_nExplored()
    
    if explored1 > explored0:
        bv_original[tuple(x)] = ret
        y = [loader.load(n, x) for n in range(loader.inputDim())]
        bv[tuple(y)] = ret
    return ret


i_local = 0

def callback_local(x):
    """Callback after each local minimization step"""
    global i_local
    i_local += 1
    if args.verbose >= Verbose.Debug:
        print("%d: XXXX Local CALLBACK, with passStaged() of the round:" % i_local)
        lib.print_passStaged()
    lib.pushStaged()
    if args.verbose >= Verbose.Debug:
        print("nPass after pushStaged")
        lib.print_nPass()
        print("explored")
        print("lib.print_explored():")
        lib.print_explored()
  
i_global = 0

def callback_global(x, f, accepted):
    """
    Callback after each basin hopping iteration.
    
    Parameters:
        x: current position
        f: current function value
        accepted: whether step was accepted
    Returns:
        bool: True to stop optimization
    """
    global i_global
    i_global += 1
    if args.verbose >= Verbose.Debug:
        print("%s -th @@@@@ Global CALLBACK" % i_global)
    
    if i_global % args.abandon == 0:
        lib.addHardBranchAsExplored()

    # Stop early if objective coverage reached
    if r.exploredRatio() >= args.objective:
        return True


def demo(startPoint=10, niter=10, method='powell', stepSize=5):
    """Demo function for testing basin hopping"""
    res = op.basinhopping(
        foo_py, startPoint, 
        callback=callback_global,
        minimizer_kwargs={'method': method}, 
        niter=niter, 
        stepsize=stepSize, 
        niter_success=50
    )
    # To use local callback: minimizer_kwargs={'method': method, 'callback': callback_local}


def mybounds(**kwargs):
    """
    Acceptance test for basin hopping.
    Currently accepts all moves (can be customized).
    """
    # x_new = kwargs["x_new"]
    # x_old = kwargs["x_old"] 
    # f_new = kwargs["f_new"]
    # f_old = kwargs["f_old"]
    return True

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    message = '[BVA parameter parsing] ... '
    parser = argparse.ArgumentParser(description=message)

    # Version info
    parser.add_argument('--version', help='BVA version', required=False, 
                       action='store_true', default=False)

    # Algorithm flags
    parser.add_argument('-P', '--pushStaged', help='pushStaged activated', 
                       required=False, action='store_true', default=False)
    parser.add_argument('-n', '--niter', help='Iteration number of BasinHopping', 
                       required=False, type=int, default=5)
    parser.add_argument('-m', '--method', help='Local minimization procedure', 
                       required=False, default='powell')
    parser.add_argument('--methods', help='list of applicable local minimization methods', 
                       required=False, action='store_true', default=False)
    parser.add_argument('--run', help='force running', required=False, 
                       action='store_true', default=True)

    # Verbosity and output
    verboseInfo = '0:Silent; 1:Alert; 2:Routine; 3:Debug'
    parser.add_argument('-v', '--verbose', help=verboseInfo, action='store', 
                       required=False, type=int, default=Verbose.Routine)
    parser.add_argument('--stepSize', help='Step size', action='store', 
                       required=False, type=float, default=300.0)

    # Input configuration
    parser.add_argument('-s', '--startPoint', nargs='*', help='start point', 
                       action='store', type=float, default=[0.0])
    parser.add_argument('-t', '--tol', help='tolerance', action='store', 
                       type=float, default=1e-10)
    parser.add_argument('-N', help='iteration times to start over', action='store', 
                       required=False, type=int, default=500, dest='startOver')
    parser.add_argument('-S', '--seed', help='random seed', action='store', 
                       type=int, required=False, default=None)
    parser.add_argument('-i', '--inputDim', help='input dimension', action='store', 
                       required=False, default=loader.inputDim(), type=int)
    parser.add_argument('-a', '--abandon', help='how often you abandon hard branches', 
                       action='store', required=False, default=10, type=int)

    # Feature flags
    parser.add_argument('--rsse', dest='rsse', help="removeSingleSidedBranch enable", 
                       action='store_true')
    parser.add_argument('--no-rsse', dest='rsse', help="removeSingleSidedBranch disabled",
                       action='store_false')
    parser.set_defaults(rsse=True)

    # Coverage objective
    parser.add_argument('-c', '--objective', help='objective Coverage', action='store', 
                       required=False, type=float, default=1.0)

    args = parser.parse_args()

    # Handle version flag
    if args.version:
        logo_dir = os.path.join(root_dir, 'logo2.txt')
        with open(logo_dir, "r", encoding='utf-8') as logo_file:
            logo = logo_file.read().strip('\n')
        print()
        print(logo)
        print()
        print("BVA Deliverable D2b,  May 15 2015")
        print("Contributors: Zhoulai Fu and Zhendong Su")
        print("Copyright: University of California, Davis")
        args.run = False

    # List available methods
    if args.methods:
        print("[BVA applicable local minimization procedure list (case-insensitive)]")
        methods = ['Powell', 'CG', 'BFGS', 'Anneal', 'L-BFGS-B', 'TNC', 
                  'COBYLA', 'SLSQP', 'Nelder-Mead']
        print(methods)
        print("See more at http://docs.scipy.org/doc/scipy/reference/tutorial/optimize.html")
        args.run = False

    # Validate start point dimensions
    if len(args.startPoint) < args.inputDim:
        print("[BVA WARNING]: len(startPoint) = %s,  inputDim = %s" % 
              (len(args.startPoint), args.inputDim))
        if len(args.startPoint) == 1:
            args.startPoint = np.array(args.startPoint * args.inputDim)
            print("Your startPoint is tiled up to", args.startPoint)
        else:
            print("Mismatch of len(startPoint) and inputDim")
            sys.exit(1)

    # Early exit if not running
    if not args.run:
        sys.exit(0)
    
    if args.verbose >= Verbose.Routine:
        print("[BVA running]...")
    
    # Python 3 compatible timing (replaces deprecated time.clock())
    startTime = time.perf_counter()
    
    kw = {'method': args.method, 'callback': callback_local}
    if args.seed is not None:
        np.random.seed(args.seed)
    sp = np.array(args.startPoint)
    nfev = 0
    
    # Safe float generator with fallback for hypothesis compatibility
    def get_float():
        try:
            from hypothesis.strategies import floats
            return floats().example()
        except (ImportError, AttributeError, TypeError):
            # Fallback: use numpy random with reasonable bounds
            return np.random.uniform(-1e10, 1e10)
    
    # Main optimization loop
    for i in range(args.startOver):
        if args.verbose >= Verbose.Routine:
            print("StartOver i =", i)
        if args.verbose >= Verbose.Debug:
            print("startPoint =", sp)
        
        res = op.basinhopping(
            foo_py, sp, 
            callback=callback_global,
            minimizer_kwargs=kw, 
            niter=args.niter, 
            stepsize=args.stepSize, 
            accept_test=mybounds
        )
        nfev += res.nfev
        
        if args.verbose >= Verbose.Routine:
            ratio = r.exploredRatio()
            print("Explored ratio so far =", '{percent:.2%}'.format(percent=ratio))

        # Check termination condition
        if r.exploredRatio() >= args.objective:
            if args.verbose >= Verbose.Routine:
                print("Stop now as the objective coverage has been reached")
            break
        
        if args.verbose >= Verbose.Debug:
            print("Abandoned:")
            lib.print_abandoned()
        
        # Generate new random start point for next iteration
        sp = np.array([get_float() for _ in range(args.inputDim)])
        lib.reset()
        if args.rsse:
            lib.removeSingleSidedExploredBranch()

    endTime = time.perf_counter()
    
    # Write timing results
    with open(config.time_dir(), 'w', encoding='utf-8') as f:
        f.write(str(endTime - startTime) + '\n')
    
    # Write dimension info
    with open(config.dimension_dir(), 'w', encoding='utf-8') as f:
        f.write(str(loader.inputDim()) + '\n')
    
    if args.verbose >= Verbose.Routine:
        print("total nfev =", nfev)
    
    # Write function evaluation count
    with open(config.nfev_dir(), 'w', encoding='utf-8') as f:
        f.write(str(nfev) + '\n')
    
    # Write test cases (avoid variable name conflict: use f_val instead of f)
    with open(config.tests_dir(), 'w', encoding='utf-8') as f:
        for x, _ in bv.items():
            if len(x) == 0 and args.verbose >= Verbose.Alert:
                print("WARNING: Maybe change cov.c taking comma into account")
            for val in x:
                f.write(str(val) + ',\n')

    # Final summary output
    if args.verbose >= Verbose.Routine:
        print("You will be using the following basinhopping parameters:")
        print("[BVA config] args.niter      = ", args.niter)
        print("[BVA config] args.method     = ", args.method)
        print("[BVA config] args.stepSize   = ", args.stepSize)
        print("[BVA config] args.startPoint = ", args.startPoint)
        print("[BVA config] args.pushStaged = ", args.pushStaged)
        print("[BVA config] args.startOver  = ", args.startOver)
        print("[BVA config] args.abandon    = ", args.abandon)
        print()
        print("[BVA Summary]:")
        idx = 1
        print("%s: %-42s   %s" % ('#', 'x', 'f'))
        print("--------------------------------------------------------------")
        for x, f_val in bv.items():  # Renamed f -> f_val to avoid conflict
            print("%s: %-42s -> %s" % (idx, list(x), f_val))
            idx += 1
        print("--------------------------------------------------------------")
        print("Explored:")
        lib.print_explored()
        
        print()
        print("Total process time = ", endTime - startTime, 'seconds')

        with open(config.brInfo_dir(), 'r', encoding='utf-8') as f:
            nBr = sum(1 for _ in f) * 2.0
        try:
            c = len(r.getExplored()) * 1.0 / nBr
        except ZeroDivisionError:
            print('No branches detected, considered as c=1:')
            c = 1.0

        print("Explored ratio =", '{percent:.2%}'.format(percent=r.exploredRatio()))

        if args.verbose >= Verbose.Debug:
            print(res)
    
    sys.exit(0)