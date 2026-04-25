#!/usr/bin/env python3
"""
Setup script for SeqSeg Vessel Segmentation (SeqSegVesselSegmentation) Slicer extension dependencies
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required Python packages for the SeqSeg Vessel Segmentation extension."""
    
    requirements = [
        "seqseg==1.0.1",
        "numpy>=1.19.0",
        "torch>=2.9.0",
    ]
    
    print("Installing SeqSeg Vessel Segmentation extension dependencies...")
    
    for package in requirements:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            return False
    
    print("\n✓ All dependencies installed successfully!")
    print("\nYou can now use the SeqSeg Vessel Segmentation extension in 3D Slicer.")
    return True

def check_dependencies():
    """Check if dependencies are already installed."""
    
    print("Checking SeqSeg Vessel Segmentation extension dependencies...")
    
    try:
        import seqseg
        print("✓ seqseg package is available")
        return True
    except ImportError:
        print("✗ seqseg package not found")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        success = check_dependencies()
    else:
        success = install_dependencies()
    
    sys.exit(0 if success else 1)