#!/usr/bin/env python3
"""
Fix FX file headers - add DATETIME column name
The system expects 'DATETIME' column but FX files have unnamed index
"""

import pandas as pd
from pathlib import Path

def fix_fx_headers():
    """Add DATETIME header to all FX CSV files"""
    
    print("🔧 FIXING FX FILE HEADERS")
    print("=" * 50)
    
    fx_dir = Path("data/futures/fx_prices_csv")
    
    # Get all CSV files in FX directory
    fx_files = list(fx_dir.glob("*.csv"))
    
    fixed_count = 0
    
    for fx_file in fx_files:
        print(f"\n📄 Processing {fx_file.name}...")
        
        try:
            # Read the file
            df = pd.read_csv(fx_file, index_col=0, parse_dates=True)
            
            # Check if index has a name
            if df.index.name is None or df.index.name != 'DATETIME':
                print(f"   🔍 Index name: {df.index.name} -> needs fixing")
                
                # Set the index name to DATETIME
                df.index.name = 'DATETIME'
                
                # Save back to CSV
                df.to_csv(fx_file)
                
                print(f"   ✅ Fixed: added DATETIME column name")
                fixed_count += 1
            else:
                print(f"   ✅ Already has DATETIME column")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎉 FX HEADER FIX COMPLETE!")
    print(f"✅ Fixed {fixed_count}/{len(fx_files)} files")
    
    # Verify the fix
    print(f"\n🔍 VERIFICATION:")
    for fx_file in fx_files[:3]:  # Check first 3 files
        df = pd.read_csv(fx_file, nrows=2)
        print(f"   {fx_file.name}: columns = {list(df.columns)}")

if __name__ == "__main__":
    fix_fx_headers()