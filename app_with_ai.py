"""
AI-Enhanced Trading Analysis System
Combines 52+ indicators with AI-powered analysis

Usage:
1. Set your AI API key: set OPENAI_API_KEY=your_key_here
2. Run: python app_with_ai.py
"""
import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
import yaml
import eel
from datetime import datetime, timedelta
import ta
from ai_analyzer import AITradingAnalyzer, format_ai_result_for_display

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create folders
DATA_FOLDER = 'data'
RESULTS_FOLDER = 'results'
INDICATORS_FOLDER = 'results/indicators'
AI_RESULTS_FOLDER = 'results/ai_analysis'

for folder in [DATA_FOLDER, RESULTS_FOLDER, INDICATORS_FOLDER, AI_RESULTS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Initialize AI analyzer (optional)
AI_ENABLED = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY') or os.getenv('GEMINI_API_KEY')
if AI_ENABLED:
    print("✅ AI Analysis: ENABLED")
    ai_analyzer = AITradingAnalyzer()
else:
    print("⚠️ AI Analysis: DISABLED (No API key found)")
    print("   Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY to enable")
    ai_analyzer = None

eel.init('web')

# Import all indicator and analysis code from app.py
exec(open('app.py').read())

# Override the analyze_symbol function to add AI analysis
original_analyze_symbol = analyze_symbol

@eel.expose
def analyze_symbol(symbol, timeframe="1d", use_ai=True):
    """Enhanced analysis with optional AI insights"""
    try:
        # Get traditional analysis
        traditional_result = original_analyze_symbol(symbol, timeframe)
        
        if 'error' in traditional_result:
            return traditional_result
        
        # Add AI analysis if enabled
        if AI_ENABLED and use_ai and ai_analyzer:
            try:
                eel.send_status(f"🤖 AI analyzing {symbol}...")()
                
                # Prepare data for AI
                indicators = traditional_result.get('all_indicators', {})
                price_data = {
                    'close': traditional_result['entry_price'],
                    'daily_change': traditional_result.get('raw_score', 0),
                    'volume': indicators.get('Volume_SMA', 0),
                    'avg_volume': indicators.get('Volume_SMA', 0)
                }
                
                # Get AI analysis
                ai_result = ai_analyzer.analyze(symbol, indicators, price_data)
                
                # Compare with traditional
                comparison = ai_analyzer.compare_with_traditional(traditional_result, ai_result)
                
                # Add to result
                traditional_result['ai_analysis'] = ai_result
                traditional_result['ai_vs_traditional'] = comparison
                traditional_result['has_ai'] = True
                
                # Save AI analysis to file
                ai_file = os.path.join(AI_RESULTS_FOLDER, f"{symbol}_ai_analysis.json")
                import json
                with open(ai_file, 'w') as f:
                    json.dump(ai_result, f, indent=2)
                
                eel.send_status(f"✅ AI analysis complete for {symbol}")()
                
            except Exception as ai_error:
                traditional_result['ai_error'] = str(ai_error)
                traditional_result['has_ai'] = False
                eel.send_status(f"⚠️ AI analysis failed for {symbol}: {str(ai_error)}")()
        else:
            traditional_result['has_ai'] = False
        
        return traditional_result
        
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def get_ai_status():
    """Check if AI is enabled"""
    return {
        "enabled": AI_ENABLED is not None,
        "provider": os.getenv('AI_PROVIDER', 'openai'),
        "model": ai_analyzer.model if ai_analyzer else None
    }

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🤖 AI-ENHANCED TRADING ANALYSIS SYSTEM")
    print("="*80)
    print(f"AI Status: {'✅ ENABLED' if AI_ENABLED else '❌ DISABLED'}")
    if ai_analyzer:
        print(f"AI Provider: {ai_analyzer.provider}")
        print(f"AI Model: {ai_analyzer.model}")
    print("="*80 + "\n")
    
    eel.start('dashboard.html', size=(1400, 900), port=8080)
