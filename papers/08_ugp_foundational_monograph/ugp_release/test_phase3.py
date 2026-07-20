#!/usr/bin/env python3
"""
Test script for Phase 3 UGP Tools functionality.
This script tests all the new plotting and build functions.
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from ugp_tools import (
        build_all, 
        generate_basin_plot, 
        generate_fib_index_histogram, 
        generate_transition_diagram
    )
    print("✅ Successfully imported all Phase 3 functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_individual_functions():
    """Test each plotting function individually."""
    print("\n🧪 Testing individual plotting functions...")
    
    # Test basin plot
    try:
        generate_basin_plot(10, 12, "test_basin.png")
        if os.path.exists("test_basin.png"):
            print("✅ Basin plot generation successful")
            os.remove("test_basin.png")  # Clean up
        else:
            print("❌ Basin plot file not created")
    except Exception as e:
        print(f"❌ Basin plot generation failed: {e}")
    
    # Test Fibonacci histogram
    try:
        generate_fib_index_histogram(10, 12, "test_fib.png")
        if os.path.exists("test_fib.png"):
            print("✅ Fibonacci histogram generation successful")
            os.remove("test_fib.png")  # Clean up
        else:
            print("❌ Fibonacci histogram file not created")
    except Exception as e:
        print(f"❌ Fibonacci histogram generation failed: {e}")
    
    # Test transition diagram
    try:
        generate_transition_diagram(10, 12, "test_trans.png")
        if os.path.exists("test_trans.png"):
            print("✅ Transition diagram generation successful")
            os.remove("test_trans.png")  # Clean up
        else:
            print("❌ Transition diagram file not created")
    except Exception as e:
        print(f"❌ Transition diagram generation failed: {e}")

def test_build_all():
    """Test the comprehensive build_all function."""
    print("\n🏗️ Testing build_all function...")
    
    try:
        # Create test output directory
        test_dir = "test_output"
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
        
        # Run build_all
        results = build_all(10, 12, test_dir)
        
        # Check that all expected files were created
        expected_files = [
            'survivors.csv',
            'orders.csv', 
            'basin_plot.png',
            'fib_index_hist.png',
            'transition_diagram.png'
        ]
        
        all_created = True
        for filename in expected_files:
            filepath = os.path.join(test_dir, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"✅ {filename}: {size} bytes")
            else:
                print(f"❌ {filename}: Missing")
                all_created = False
        
        if all_created:
            print("✅ build_all function completed successfully")
            
            # Clean up test directory
            import shutil
            shutil.rmtree(test_dir)
            print("🧹 Test output directory cleaned up")
        else:
            print("❌ Some files were not created")
            
    except Exception as e:
        print(f"❌ build_all function failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests."""
    print("🚀 Starting Phase 3 UGP Tools testing...")
    print("=" * 50)
    
    # Test individual functions
    test_individual_functions()
    
    # Test comprehensive build
    test_build_all()
    
    print("\n" + "=" * 50)
    print("🎉 Phase 3 testing complete!")
    
    # Check for matplotlib and numpy
    try:
        import matplotlib
        import numpy
        print(f"📊 Matplotlib version: {matplotlib.__version__}")
        print(f"🔢 NumPy version: {numpy.__version__}")
    except ImportError as e:
        print(f"⚠️ Warning: {e}")

if __name__ == "__main__":
    main()
