"""
Test Configuration Settings
Verifies that risk composition settings from config.py are correctly applied and accessible.
"""

import asyncio
import sys
import os
from typing import Dict, Any
import structlog

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_settings, RiskConfig

logger = structlog.get_logger()


def test_risk_config_settings():
    """Test that risk composition settings are correctly loaded from config.py."""
    
    print("🧪 Testing Risk Configuration Settings")
    print("=" * 60)
    
    # Get settings
    settings = get_settings()
    risk_config = settings.risk
    
    print(f"\n📊 Risk Configuration Settings:")
    print(f"   Base Leverage: 1:{risk_config.base_leverage}")
    print(f"   Max Leverage Risk: 1:{risk_config.max_leverage_risk}")
    print(f"   Risk Compounding: {'Enabled' if risk_config.risk_compounding else 'Disabled'}")
    print(f"   Profit Multiplier Cap: {risk_config.profit_multiplier_cap}x")
    print(f"   Max Position Size: {risk_config.max_position_size_pct*100:.1f}%")
    print(f"   Dynamic Leverage: {'Enabled' if risk_config.enable_dynamic_leverage else 'Disabled'}")
    print(f"   Winning Streak Threshold: {risk_config.winning_streak_threshold}")
    print(f"   Losing Streak Threshold: {risk_config.losing_streak_threshold}")
    print(f"   Leverage Increase Factor: {risk_config.leverage_increase_factor}")
    print(f"   Leverage Decrease Factor: {risk_config.leverage_decrease_factor}")
    print(f"   Margin Call 50% Threshold: {risk_config.margin_call_threshold_50*100:.1f}%")
    print(f"   Margin Call 80% Threshold: {risk_config.margin_call_threshold_80*100:.1f}%")
    print(f"   Extreme Value Threshold: {risk_config.extreme_value_threshold}x")
    print(f"   Safety Balance Threshold: {risk_config.safety_balance_threshold}x")
    
    # Test validation
    assert risk_config.base_leverage >= 1.0, "Base leverage should be >= 1.0"
    assert risk_config.max_leverage_risk >= risk_config.base_leverage, "Max leverage should be >= base leverage"
    assert 0 < risk_config.profit_multiplier_cap <= 10, "Profit multiplier cap should be between 0 and 10"
    assert 0 < risk_config.max_position_size_pct <= 1, "Max position size should be between 0 and 1"
    assert risk_config.winning_streak_threshold > 0, "Winning streak threshold should be positive"
    assert risk_config.losing_streak_threshold > 0, "Losing streak threshold should be positive"
    assert 0 < risk_config.margin_call_threshold_50 < 1, "Margin call 50% threshold should be between 0 and 1"
    assert 0 < risk_config.margin_call_threshold_80 < 1, "Margin call 80% threshold should be between 0 and 1"
    assert risk_config.extreme_value_threshold > 0, "Extreme value threshold should be positive"
    assert risk_config.safety_balance_threshold > 0, "Safety balance threshold should be positive"
    
    print(f"\n✅ All risk configuration settings are valid!")
    return True


def test_main_app_import():
    """Test that main.py can be imported and access the risk configuration settings."""
    
    print(f"\n🔧 Testing Main App Import and Risk Settings Access")
    print("=" * 60)
    
    try:
        # Import main app
        from main import app, get_settings as main_get_settings
        
        # Test that we can get settings from main
        settings = main_get_settings()
        risk_config = settings.risk
        
        print(f"✅ Main app imported successfully!")
        print(f"   Base Leverage: 1:{risk_config.base_leverage}")
        print(f"   Max Leverage: 1:{risk_config.max_leverage_risk}")
        print(f"   Risk Compounding: {'Enabled' if risk_config.risk_compounding else 'Disabled'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Main app import test failed: {e}")
        return False


def test_risk_settings_integration():
    """Test that risk settings can be used in a simulated trading scenario."""
    
    print(f"\n🎯 Testing Risk Settings Integration")
    print("=" * 60)
    
    settings = get_settings()
    risk_config = settings.risk
    
    # Simulate initial balance
    initial_balance = 100000.0
    portfolio_value = initial_balance
    
    print(f"   Initial Balance: ${initial_balance:,.2f}")
    print(f"   Base Leverage: 1:{risk_config.base_leverage}")
    print(f"   Max Leverage: 1:{risk_config.max_leverage_risk}")
    
    # Simulate dynamic leverage calculation
    current_leverage = risk_config.base_leverage
    winning_streak = 0
    losing_streak = 0
    
    # Test winning streak scenario
    print(f"\n📈 Testing Winning Streak Scenario:")
    for i in range(5):
        winning_streak += 1
        losing_streak = 0
        
        if (risk_config.enable_dynamic_leverage and 
            winning_streak >= risk_config.winning_streak_threshold):
            leverage_increase = min(winning_streak - (risk_config.winning_streak_threshold - 1), 2)
            current_leverage = min(risk_config.base_leverage + leverage_increase, risk_config.max_leverage_risk)
        else:
            current_leverage = risk_config.base_leverage
            
        print(f"   Win {i+1}: Streak={winning_streak}, Leverage=1:{current_leverage}")
    
    # Test losing streak scenario
    print(f"\n📉 Testing Losing Streak Scenario:")
    for i in range(5):
        losing_streak += 1
        winning_streak = 0
        
        if (risk_config.enable_dynamic_leverage and 
            losing_streak >= risk_config.losing_streak_threshold):
            leverage_decrease = min(losing_streak - (risk_config.losing_streak_threshold - 1), 2)
            current_leverage = max(risk_config.base_leverage - leverage_decrease, 1)
        else:
            current_leverage = risk_config.base_leverage
            
        print(f"   Loss {i+1}: Streak={losing_streak}, Leverage=1:{current_leverage}")
    
    # Test risk compounding
    print(f"\n💰 Testing Risk Compounding:")
    if risk_config.risk_compounding and portfolio_value > initial_balance:
        profit_multiplier = min(portfolio_value / initial_balance, risk_config.profit_multiplier_cap)
        print(f"   Portfolio Value: ${portfolio_value:,.2f}")
        print(f"   Profit Multiplier: {profit_multiplier:.2f}x (capped at {risk_config.profit_multiplier_cap}x)")
    else:
        print(f"   Risk Compounding: Disabled or no profit")
    
    # Test margin call simulation
    print(f"\n⚠️ Testing Margin Call Simulation:")
    test_balances = [initial_balance * 0.3, initial_balance * 0.6, initial_balance * 0.9, initial_balance * 1.2]
    
    for balance in test_balances:
        leverage_risk_factor = 1.0
        if balance < initial_balance * risk_config.margin_call_threshold_50:
            leverage_risk_factor = 0.5
        elif balance < initial_balance * risk_config.margin_call_threshold_80:
            leverage_risk_factor = 0.8
            
        print(f"   Balance: ${balance:,.2f} ({balance/initial_balance*100:.1f}%) -> Risk Factor: {leverage_risk_factor}")
    
    print(f"\n✅ Risk settings integration test completed!")
    return True


def test_single_test_integration():
    """Test that single_test.py can use the risk configuration settings."""
    
    print(f"\n🧪 Testing Single Test Integration with Risk Settings")
    print("=" * 60)
    
    try:
        # Import single test components
        from single_test import SingleParameterTester
        
        # Create tester instance
        tester = SingleParameterTester()
        
        # Test that the tester can access risk settings
        settings = tester.settings
        risk_config = settings.risk
        
        print(f"✅ Single test can access risk configuration!")
        print(f"   Base Leverage: 1:{risk_config.base_leverage}")
        print(f"   Max Leverage: 1:{risk_config.max_leverage_risk}")
        print(f"   Risk Compounding: {'Enabled' if risk_config.risk_compounding else 'Disabled'}")
        print(f"   Dynamic Leverage: {'Enabled' if risk_config.enable_dynamic_leverage else 'Disabled'}")
        
        # Test that the tester's leverage settings match config
        assert tester.base_leverage == risk_config.base_leverage, "Base leverage mismatch"
        assert tester.max_leverage == risk_config.max_leverage_risk, "Max leverage mismatch"
        assert tester.risk_compounding == risk_config.risk_compounding, "Risk compounding mismatch"
        
        print(f"✅ Single test leverage settings match config!")
        
        return True
        
    except Exception as e:
        print(f"❌ Single test integration failed: {e}")
        return False


async def main():
    """Main test function."""
    
    print("🧪 Configuration Settings Test Suite")
    print("=" * 80)
    
    # Run all tests
    tests = [
        ("Risk Config Settings", test_risk_config_settings),
        ("Main App Import", test_main_app_import),
        ("Risk Settings Integration", test_risk_settings_integration),
        ("Single Test Integration", test_single_test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Configuration settings are correctly applied.")
    else:
        print("⚠️ Some tests failed. Please check the configuration.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main()) 