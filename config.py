#!/usr/bin/env python3
"""
BVA Configuration Module - Python 3 Compatible Version
Provides path resolution and configuration file access.
"""

import argparse
import os
import sys
# Python 3: ConfigParser moved to configparser, SafeConfigParser merged into ConfigParser
from configparser import ConfigParser  

# ============================================================================
# Path Resolution Functions
# ============================================================================

def this_dir():
    """Get the directory where this config.py file resides"""
    return os.path.abspath(os.path.dirname(__file__))

def root_dir():
    """Get the project root directory based on root.txt"""
    root_file_dir = os.path.join(this_dir(), 'root.txt')
    
    if not os.path.isfile(root_file_dir):
        print(f"Error: root.txt not found at {root_file_dir}")
        sys.exit(1)
    
    # Python 3: Specify encoding
    with open(root_file_dir, "r", encoding='utf-8') as f:
        root_file_content = f.read().strip('\n')
    
    if not root_file_content == this_dir():
        print(f"Something wrong! \nroot_file_content = {root_file_content}, but this_dir() = {this_dir()}")
        sys.exit(1)
    return root_file_content

def src_dir():
    """Get source code directory"""
    res = os.path.join(root_dir(), 'src')
    if not os.path.isdir(res):
        print(f"Something wrong! `{res}` is not a directory")
        sys.exit(1)
    return res

def benchs_dir():
    """Get benchmarks directory"""
    res = os.path.join(root_dir(), 'benchs')
    if not os.path.isdir(res):
        print(f"Something wrong! `{res}` is not a directory")
        sys.exit(1)
    return res

def output_dir():
    """Get output directory"""
    res = os.path.join(root_dir(), 'output')
    # Note: Output dir might be created at runtime, but original code checks existence
    if not os.path.isdir(res):
        # Create it if it doesn't exist instead of exiting (more robust)
        try:
            os.makedirs(res, exist_ok=True)
        except OSError as e:
            print(f"Something wrong! Cannot create `{res}`: {e}")
            sys.exit(1)
    return res

def config_dir():
    """Get config directory"""
    res = os.path.join(root_dir(), 'config')
    if not os.path.isdir(res):
        print(f"Something wrong! `{res}` is not a directory")
        sys.exit(1)
    return res

def pp_ini_dir():
    """Get pp.ini configuration file path"""
    res = os.path.join(config_dir(), 'pp.ini')
    if not os.path.isfile(res):
        print(f"Something wrong! `{res}` is not a file")
        sys.exit(1)
    return res

def bench_name():
    """Get current benchmark name from theBench.txt"""
    theBench_txt_dir = os.path.join(root_dir(), 'theBench.txt')
    if not os.path.isfile(theBench_txt_dir):
        # Fix: Original code used undefined variable 'res' in error message
        print(f"Something wrong (001)! `{theBench_txt_dir}` is not a file")
        sys.exit(1)

    # Python 3: Specify encoding
    with open(theBench_txt_dir, "r", encoding='utf-8') as f:
        res = f.read().strip('\n')
    return res

def bench_dir():
    """Get specific benchmark directory"""
    res = os.path.join(benchs_dir(), bench_name())
    if not os.path.isdir(res):
        print(f"Something wrong (002)! `{res}` is not a directory")
        sys.exit(1)
    return res

def loader_dir():
    """Get build/loader directory"""
    res = os.path.join(root_dir(), 'build')
    if not os.path.isdir(res):
        print(f"Something wrong! `{res}` is not a directory")
        sys.exit(1)
    return res

def libr_so_dir():
    """Get path to the shared library (libr.so)"""
    res = os.path.join(root_dir(), 'build', 'libr.so')
    if not os.path.isfile(res):
        print(f"Something wrong! `{res}` is not a file")
        sys.exit(1)
    return res

def brInfo_dir():
    """Get branch info file path"""
    res = os.path.join(output_dir(), 'brInfo.txt')
    if not os.path.isfile(res):
        print(f"Something wrong! `{res}` is not a file")
        sys.exit(1)
    return res

def time_dir():
    """Get timing output file path"""
    res = os.path.join(output_dir(), 'time.txt')
    return res

def tests_dir():
    """Get tests output file path"""
    res = os.path.join(output_dir(), 'tests.txt')
    return res

def dimension_dir():
    """Get dimension output file path"""
    res = os.path.join(output_dir(), 'dimension.txt')
    return res

def nfev_dir():
    """Get function evaluation count output file path"""
    res = os.path.join(output_dir(), 'nfev.txt')
    return res

def runningTime_dir():
    """Get running time file path (used by tests)"""
    res = os.path.join(output_dir(), 'runningTime.txt')
    return res

# ============================================================================
# Main Entry Point (Debug/Verification)
# ============================================================================

if __name__ == "__main__":
    message = '[BVA config setting] ... '
    print(message)

    # Print all resolved paths for verification
    print("this_dir()    =", this_dir())
    print("root_dir()    =", root_dir())
    print("src_dir()     =", src_dir())
    print("benchs_dir()  =", benchs_dir())
    print("pp_ini_dir()  =", pp_ini_dir())
    print("bench_name()  =", bench_name())
    print("bench_dir()   =", bench_dir())
    print("loader_dir()  =", loader_dir())
    print("libr_so_dir() =", libr_so_dir())
    print("loader_dir    =", loader_dir())