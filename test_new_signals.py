"""
Quick Test Script for New Signal Logic
Tests BUY/SELL/HOLD detection with the improved algorithm
"""

import yfinance as yf
import pandas as pd
from app import TradingAnalyzer

# Test symbols representing different scenarios
TEST_SYMBOLS = {
    "AAPL": "Large cap, usually trending",
    "TSLA": "High volatility",
    "SPY": "Market benchmark",
    "NVDA": "Strong momentum",
    "GWH": "Client-mentioned symbol"
}

def test_symbol(symbol, description):
    """Test a single symbol"""
    print(f"\n{'='*60}")
    print(f"Testing: {symbol} - {description}")
    print(f"{'='*60}")
    
    try:
        # Download data
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y", interval="1d")
        
        if df.empty or len(df) < 250:
            print(f"❌ Insufficient data for {symbol}")
            return None
        
        # Standardize columns
        df.columns = [col.lower() for col in df.columns]
        
        # Analyze
        analyzer = TradingAnalyzer(symbol, df)
        result = analyzer.analyze()
        
        # Display results
        print(f"\n📊 RESULTS:")
        print(f"   Signal: {result['recommendation']}")
        print(f"   Confidence: {result['confidence_score']}%")
        print(f"   Raw Score: {result['raw_score']}")
        print(f"   Entry: ${result['entry_price']}")
        
        if result['stop_loss']:
            print(f"   Stop Loss: ${result['stop_loss']} ({result['risk_pct']:.1f}% risk)")
            print(f"   Take Profit: ${result['take_profit']} ({result['reward_pct']:.1f}% gain)")
            print(f"   Risk/Reward: {result['risk_reward_ratio']:.2f}:1")
        
        print(f"\n💡 TOP REASONS:")
        for i, reason in enumerate(result['rationale'].split(' | ')[:5], 1):
            print(f"   {i}. {reason}")
        
        print(f"\n🔑 KEY INDICATORS:")
        for ind in result['key_indicators'][:6]:
            print(f"   {ind['name']}: {ind['value']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error analyzing {symbol}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*60)
    print("🧪 TESTING NEW SIGNAL LOGIC")
    print("="*60)
    print("\nThis will test the improved algorithm on various stocks")
    print("Expected: Mix of BUY/SELL/HOLD (not 90% HOLD)")
    print("Expected: Confidence 30-80% (not 1-10%)")
    
    results = {}
    
    for symbol, description in TEST_SYMBOLS.items():
        result = test_symbol(symbol, description)
        if result:
            results[symbol] = result
    
    # Summary
    print(f"\n\n{'='*60}")
    print("📈 SUMMARY")
    print(f"{'='*60}")
    
    if not results:
        print("❌ No symbols analyzed successfully")
        return
    
    buy_count = sum(1 for r in results.values() if r['recommendation'] == 'BUY')
    sell_count = sum(1 for r in results.values() if r['recommendation'] == 'SELL')
    hold_count = sum(1 for r in results.values() if r['recommendation'] == 'HOLD')
    total = len(results)
    
    avg_confidence = sum(r['confidence_score'] for r in results.values()) / total
    
    print(f"\n📊 Signal Distribution:")
    print(f"   BUY:  {buy_count}/{total} ({buy_count/total*100:.0f}%)")
    print(f"   SELL: {sell_count}/{total} ({sell_count/total*100:.0f}%)")
    print(f"   HOLD: {hold_count}/{total} ({hold_count/total*100:.0f}%)")
    
    print(f"\n📈 Average Confidence: {avg_confidence:.0f}%")
    
    print(f"\n✅ TEST RESULTS:")
    if buy_count == 0 and sell_count == 0:
        print("   ❌ FAILED: All HOLD signals (algorithm too conservative)")
    elif avg_confidence < 20:
        print("   ❌ FAILED: Confidence too low (algorithm not confident)")
    else:
        print(f"   ✅ PASSED: {buy_count + sell_count} actionable signals generated")
        print(f"   ✅ PASSED: Average confidence is reasonable")
    
    print(f"\n{'='*60}")
    print("Testing complete! Review results above.")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
