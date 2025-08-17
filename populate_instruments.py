#!/usr/bin/env python3
"""
Script to manually download and populate instruments database
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from instruments_manager import InstrumentsManager

async def main():
    print("🔄 Starting instruments download and population...")
    
    try:
        # Initialize instruments manager
        instruments_mgr = InstrumentsManager()
        
        # Check if database has existing data
        stats = instruments_mgr.get_database_stats()
        if stats.get('total_instruments', 0) > 0:
            print(f"⚠️  Database already has {stats.get('total_instruments', 0)} instruments")
            print("🔄 Clearing existing data and re-downloading...")
            
            # Clear existing data
            instruments_mgr.conn.execute("DELETE FROM instruments")
            instruments_mgr.conn.execute("DELETE FROM instruments_metadata")
            instruments_mgr.conn.commit()
            print("✅ Cleared existing data")
        
        # Force refresh instruments (bypass cache)
        print("📥 Downloading instruments file...")
        
        # Temporarily reduce download interval to force download
        original_interval = instruments_mgr.download_interval
        instruments_mgr.download_interval = 0  # Force download
        
        success = await instruments_mgr.refresh_instruments()
        
        # Restore original interval
        instruments_mgr.download_interval = original_interval
        
        if success:
            # Get stats
            stats = instruments_mgr.get_database_stats()
            print("✅ Instruments populated successfully!")
            print(f"📊 Database Stats:")
            print(f"   Total instruments: {stats.get('total_instruments', 0)}")
            print(f"   NSE: {stats.get('nse_count', 0)}")
            print(f"   BSE: {stats.get('bse_count', 0)}")
            print(f"   NFO: {stats.get('nfo_count', 0)}")
            print(f"   BFO: {stats.get('bfo_count', 0)}")
            print(f"   Last download: {stats.get('last_download', 'N/A')}")
            
            # Test search
            print("\n🔍 Testing search functionality...")
            results = instruments_mgr.search_instruments("RELIANCE", 5)
            print(f"Found {len(results)} instruments for 'RELIANCE':")
            for result in results:
                print(f"   {result['short_name']} ({result['exchange_code']}) - {result['company_name']}")
                
        else:
            print("❌ Failed to populate instruments")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close database connection
        if 'instruments_mgr' in locals():
            instruments_mgr.close()

if __name__ == "__main__":
    asyncio.run(main())
