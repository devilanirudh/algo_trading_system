#!/usr/bin/env python3
"""
Test script to verify funds initialization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fake_trading import FakeTradingSystem

def test_funds_initialization():
    """Test that funds are initialized to 0"""
    try:
        # Initialize fake trading system
        fake_system = FakeTradingSystem()
        
        # Get funds
        funds = fake_system.get_funds()
        
        print("Current funds:")
        print(f"Cash Balance: ₹{funds.get('cash_balance', 0):,.2f}")
        print(f"Equity Balance: ₹{funds.get('equity_balance', 0):,.2f}")
        print(f"FNO Balance: ₹{funds.get('fno_balance', 0):,.2f}")
        print(f"Total Balance: ₹{funds.get('total_balance', 0):,.2f}")
        
        # Check if all balances are 0
        all_zero = all(
            funds.get(key, 0) == 0 
            for key in ['cash_balance', 'equity_balance', 'fno_balance', 'total_balance']
        )
        
        if all_zero:
            print("\n✅ SUCCESS: All funds initialized to ₹0")
        else:
            print("\n❌ FAILED: Some funds are not zero")
            
        return all_zero
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_funds_initialization()
