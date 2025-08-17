#!/usr/bin/env python3
"""
Test NSE file parsing
"""
import csv

def test_nse_parsing():
    print("Testing NSE file parsing...")
    
    with open('NSEScripMaster.txt', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Print field names
        print("Field names:", reader.fieldnames)
        
        # Read first few rows
        for i, row in enumerate(reader):
            if i >= 3:  # Only first 3 rows
                break
                
            print(f"\nRow {i+1}:")
            print(f"  Token: '{row.get('Token', 'NOT_FOUND')}'")
            print(f"  ShortName: '{row.get('ShortName', 'NOT_FOUND')}'")
            print(f"  CompanyName: '{row.get('CompanyName', 'NOT_FOUND')}'")
            print(f"  Series: '{row.get('Series', 'NOT_FOUND')}'")
            print(f"  InstrumentType: '{row.get('InstrumentType', 'NOT_FOUND')}'")
            print(f"  ISINCode: '{row.get('ISINCode', 'NOT_FOUND')}'")
            print(f"  Lotsize: '{row.get('Lotsize', 'NOT_FOUND')}'")
            print(f"  ticksize: '{row.get('ticksize', 'NOT_FOUND')}'")
            print(f"  FaceValue: '{row.get('FaceValue', 'NOT_FOUND')}'")
            print(f"  PermittedToTrade: '{row.get('PermittedToTrade', 'NOT_FOUND')}'")
            
            # Check if this is RELIANCE
            if 'RELIANCE' in str(row):
                print("  *** FOUND RELIANCE! ***")

if __name__ == "__main__":
    test_nse_parsing()
