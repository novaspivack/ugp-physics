#!/usr/bin/env python3
"""
Command-line interface for building UGP paper assets.
Usage: python build_paper.py [n_min] [n_max] [output_dir]
"""

import sys
import os
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Build UGP paper assets including figures and data files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_paper.py                    # Default: n=10-18, output=.
  python build_paper.py 10 15             # n=10-15, output=.
  python build_paper.py 10 22 ./assets    # n=10-22, output=./assets
        """
    )
    
    parser.add_argument('n_min', nargs='?', type=int, default=10,
                       help='Minimum n value (default: 10)')
    parser.add_argument('n_max', nargs='?', type=int, default=18,
                       help='Maximum n value (default: 18)')
    parser.add_argument('output_dir', nargs='?', type=str, default='.',
                       help='Output directory (default: current directory)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.n_min < 10:
        print("❌ Error: n_min must be >= 10")
        sys.exit(1)
    
    if args.n_max < args.n_min:
        print("❌ Error: n_max must be >= n_min")
        sys.exit(1)
    
    if args.n_max > 30:
        print("⚠️ Warning: Large n_max may take significant time")
        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            print("Build cancelled")
            sys.exit(0)
    
    # Ensure output directory exists
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Building UGP paper assets...")
    print(f"   Range: n = {args.n_min} to {args.n_max}")
    print(f"   Output: {output_path.absolute()}")
    print()
    
    try:
        # Import and run build_all
        from ugp_tools import build_all
        
        results = build_all(args.n_min, args.n_max, str(output_path))
        
        print("\n✅ Build completed successfully!")
        print(f"Generated {len(results)} files:")
        
        for key, path in results.items():
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"   {key}: {os.path.basename(path)} ({size:,} bytes)")
            else:
                print(f"   {key}: {os.path.basename(path)} (MISSING)")
        
        print(f"\n📁 All files saved to: {output_path.absolute()}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you have installed the requirements:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
