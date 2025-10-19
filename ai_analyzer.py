"""
AI-Enhanced Trading Analysis
Uses Google Gemini to analyze indicators and provide intelligent insights
"""
import os
import re
from datetime import datetime
import json
import google.generativeai as genai

class AITradingAnalyzer:
    """
    AI-powered analysis using Google Gemini
    Provides intelligent entry/exit/stop-loss recommendations
    """
    
    def __init__(self, api_key=None):
        self.provider = 'gemini'
        
        # Hardcoded API key (FREE - 1500 requests/day)
        self.api_key = api_key or "AIzaSyDEDuKKKV0YlM53yo6-KYs9FxajOLW6Q4w"
        
        # Initialize Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def _safe_format(self, value, format_spec='.2f', default='N/A'):
        """Safely format a value, returning default if None"""
        if value is None or (isinstance(value, float) and (value != value)):  # Check for NaN
            return default
        try:
            if format_spec == ',':
                return f"{value:,}"
            elif format_spec == ',.0f':
                return f"{value:,.0f}"
            else:
                return f"{value:{format_spec}}"
        except:
            return str(value) if value is not None else default
    
    def build_analysis_prompt(self, symbol, indicators, price_data):
        """
        Build comprehensive prompt for AI analysis - handles None values safely
        """
        # Helper to get indicator with default
        def get_ind(key, default=0):
            val = indicators.get(key)
            return val if val is not None else default
        
        prompt = f"""You are an expert quantitative trader analyzing {symbol}. 

**CURRENT MARKET DATA:**
- Current Price: ${self._safe_format(price_data.get('close', 0))}
- Daily Change: {self._safe_format(price_data.get('daily_change', 0))}%
- Volume: {self._safe_format(price_data.get('volume', 0), ',.0f')}
- Average Volume (20-day): {self._safe_format(price_data.get('avg_volume', 0), ',.0f')}

**TECHNICAL INDICATORS (52+ calculated):**

**TREND INDICATORS:**
- EMA 9: ${self._safe_format(get_ind('EMA_9'))} | EMA 20: ${self._safe_format(get_ind('EMA_20'))} | EMA 50: ${self._safe_format(get_ind('EMA_50'))}
- EMA 100: ${self._safe_format(get_ind('EMA_100'))} | EMA 200: ${self._safe_format(get_ind('EMA_200'))}
- SMA 20: ${self._safe_format(get_ind('SMA_20'))} | SMA 50: ${self._safe_format(get_ind('SMA_50'))} | SMA 200: ${self._safe_format(get_ind('SMA_200'))}
- MACD: {self._safe_format(get_ind('MACD'))} | Signal: {self._safe_format(get_ind('MACD_Signal'))} | Histogram: {self._safe_format(get_ind('MACD_Histogram'))}
- ADX: {self._safe_format(get_ind('ADX'))} | DI+: {self._safe_format(get_ind('DI_Positive'))} | DI-: {self._safe_format(get_ind('DI_Negative'))}
- Aroon Up: {self._safe_format(get_ind('Aroon_Up'))} | Aroon Down: {self._safe_format(get_ind('Aroon_Down'))}
- Parabolic SAR: ${self._safe_format(get_ind('Parabolic_SAR'))}

**MOMENTUM INDICATORS:**
- RSI: {self._safe_format(get_ind('RSI'))}
- Stochastic %K: {self._safe_format(get_ind('Stochastic_K'))} | %D: {self._safe_format(get_ind('Stochastic_D'))}
- Williams %R: {self._safe_format(get_ind('Williams_R'))}
- ROC: {self._safe_format(get_ind('ROC'))}%
- CCI: {self._safe_format(get_ind('CCI'))}
- Ultimate Oscillator: {self._safe_format(get_ind('Ultimate_Oscillator'))}

**VOLATILITY INDICATORS:**
- ATR: ${self._safe_format(get_ind('ATR'))}
- Bollinger Upper: ${self._safe_format(get_ind('Bollinger_Upper'))} | Middle: ${self._safe_format(get_ind('Bollinger_Middle'))} | Lower: ${self._safe_format(get_ind('Bollinger_Lower'))}
- Bollinger Width: {self._safe_format(get_ind('Bollinger_Width'))}
- Bollinger %: {self._safe_format(get_ind('Bollinger_Percent'))}

**VOLUME INDICATORS:**
- OBV: {self._safe_format(get_ind('OBV'), ',.0f')}
- CMF: {self._safe_format(get_ind('CMF'))}
- MFI: {self._safe_format(get_ind('MFI'))}
- Volume Ratio: {self._safe_format(get_ind('Volume_Ratio'))}x average

**PRICE ACTION:**
- Price vs SMA20: {self._safe_format(get_ind('Price_vs_SMA20_Pct'))}%
- Price vs SMA50: {self._safe_format(get_ind('Price_vs_SMA50_Pct'))}%
- Price vs SMA200: {self._safe_format(get_ind('Price_vs_SMA200_Pct'))}%

**YOUR TASK:**
You are a professional trader who PRIORITIZES ACCURACY and RISK MANAGEMENT over frequent trading.

**CRITICAL ANALYSIS RULES:**
1. **HIGH VOLATILITY = CAUTION**: If ATR > 8% of price, significantly reduce confidence
2. **RECENT SURGE = WAIT**: If price moved >15% in 5 days, recommend WAIT for pullback
3. **CONFLICTING SIGNALS = HOLD**: If trend and momentum disagree, recommend HOLD
4. **VOLUME MATTERS**: Weak volume = lower confidence, regardless of other signals
5. **REALISTIC TARGETS**: Don't overestimate profit potential, use ATR-based targets

**PROVIDE:**

1. **RECOMMENDATION**: BUY, SELL, or HOLD
   - BUY only if: Strong trend + good momentum + reasonable volatility + volume confirmation
   - HOLD if: Any conflicting signals OR high volatility OR recent surge
   - SELL only if: Clear downtrend + weak momentum + volume confirmation

2. **CONFIDENCE** (0-100%):
   - 80-100%: All indicators align, low volatility, perfect setup
   - 60-80%: Most indicators align, acceptable risk
   - 40-60%: Mixed signals, proceed with caution
   - 0-40%: Too risky, recommend HOLD

3. **ENTRY STRATEGY**:
   - Optimal entry price (exact number based on support/resistance)
   - Timing: NOW (if all clear) or WAIT (if needs pullback/breakout)
   - Specific trigger to watch

4. **STOP LOSS**:
   - Price: Based on recent support + ATR cushion
   - Risk %: Maximum 5-8%, reduce in high volatility
   - Clear reasoning with technical levels

5. **TAKE PROFIT**:
   - Target 1 (conservative): 1.5-2x ATR from entry
   - Target 2 (aggressive): 3-4x ATR from entry
   - Based on resistance levels, not wishful thinking

6. **RISK ASSESSMENT**:
   - Level: LOW (ATR<3%), MEDIUM (3-6%), HIGH (>6%)
   - Key risks: Volatility, overextension, weak volume
   - Market favorable: Only if volatility is manageable

7. **PATTERN & PROBABILITY**:
   - Specific pattern (breakout, reversal, consolidation, etc.)
   - Realistic success probability based on historical patterns
   - Expected timeline to targets

8. **PLAIN ENGLISH** (2-3 sentences):
   - What's happening and why
   - Should I trade now or wait?
   - What's the main risk?

**IMPORTANT:**
- BE HONEST about risks and uncertainties
- Recommend HOLD if you're not confident
- Accuracy > Trading frequency
- Consider context: recent surge, high volatility, weak volume
- Use technical levels (support/resistance) for prices

**FORMAT YOUR RESPONSE AS JSON:**
```json
{{
  "recommendation": "BUY/SELL/HOLD",
  "confidence": 85,
  "entry_strategy": {{
    "price": 192.50,
    "timing": "NOW/WAIT",
    "trigger": "wait for price to break above $193"
  }},
  "stop_loss": {{
    "price": 187.20,
    "risk_pct": 2.75,
    "reasoning": "Below recent support and 2.5x ATR"
  }},
  "take_profit": {{
    "target_1": {{"price": 202.50, "gain_pct": 5.2}},
    "target_2": {{"price": 215.00, "gain_pct": 11.7}}
  }},
  "risk_assessment": {{
    "level": "MEDIUM",
    "key_risks": ["Overbought RSI", "Weak volume"],
    "market_favorable": true
  }},
  "pattern": {{
    "type": "Bullish breakout",
    "probability": 70,
    "timeline_days": "3-7"
  }},
  "plain_summary": "Stock is breaking out of consolidation with strong momentum. Good entry point with manageable risk. Expect 5-11% upside in the next week."
}}
```
"""
        return prompt
    
    def analyze(self, symbol, indicators, price_data):
        """
        Get AI analysis of trading opportunity using Gemini
        """
        try:
            prompt = self.build_analysis_prompt(symbol, indicators, price_data)
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            text = response.text
            
            # Try to find JSON in response
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                # Return error with full response for debugging
                return {
                    "error": "No JSON found in AI response",
                    "recommendation": "HOLD",
                    "confidence": 0,
                    "plain_summary": f"AI did not return valid JSON. Response: {text[:200]}...",
                    "raw_response": text
                }
            
            json_text = text[json_start:json_end]
            
            # Clean JSON - remove markdown code blocks
            json_text = json_text.replace('```json', '').replace('```', '').strip()
            
            # Try to fix common JSON issues
            # Remove trailing commas before closing braces/brackets
            json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
            
            try:
                result = json.loads(json_text)
            except json.JSONDecodeError as je:
                # Try alternative: extract just the visible JSON structure
                try:
                    # More aggressive cleaning
                    json_text_clean = json_text.replace('\n', ' ').replace('\r', '')
                    result = json.loads(json_text_clean)
                except:
                    return {
                        "error": f"Invalid JSON: {str(je)}",
                        "recommendation": "HOLD",
                        "confidence": 0,
                        "plain_summary": f"AI returned malformed JSON. Error at line {je.lineno}, col {je.colno}: {je.msg}",
                        "raw_json": json_text[:500],
                        "entry_strategy": {"price": price_data.get('close', 0), "timing": "WAIT", "trigger": "JSON parse error"},
                        "stop_loss": {"price": 0, "risk_pct": 0, "reasoning": "Error"},
                        "take_profit": {"target_1": {"price": 0, "gain_pct": 0}},
                        "risk_assessment": {"level": "HIGH", "key_risks": ["AI error"], "market_favorable": False},
                        "pattern": {"type": "Error", "probability": 0, "timeline_days": "N/A"}
                    }
            
            # Validate required fields
            required_fields = ['recommendation', 'confidence']
            missing_fields = [f for f in required_fields if f not in result]
            
            if missing_fields:
                return {
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "recommendation": result.get('recommendation', 'HOLD'),
                    "confidence": result.get('confidence', 0),
                    "plain_summary": f"AI response incomplete. Missing: {', '.join(missing_fields)}",
                    "partial_result": result
                }
            
            # Add metadata
            result['ai_model'] = 'gemini-2.0-flash-exp'
            result['analyzed_at'] = datetime.now().isoformat()
            result['symbol'] = symbol
            
            # Add defaults for optional fields if missing
            if 'entry_strategy' not in result:
                result['entry_strategy'] = {
                    'price': price_data['close'],
                    'timing': 'NOW',
                    'trigger': 'Immediate entry'
                }
            
            if 'stop_loss' not in result:
                result['stop_loss'] = {
                    'price': price_data['close'] * 0.95,
                    'risk_pct': 5.0,
                    'reasoning': 'Default 5% stop loss'
                }
            
            if 'take_profit' not in result:
                result['take_profit'] = {
                    'target_1': {
                        'price': price_data['close'] * 1.10,
                        'gain_pct': 10.0
                    }
                }
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "recommendation": "HOLD",
                "confidence": 0,
                "plain_summary": f"AI analysis failed: {type(e).__name__}: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def compare_with_traditional(self, traditional_signal, ai_analysis):
        """
        Compare traditional indicator-based signal with AI analysis
        Show where they agree/disagree
        """
        comparison = {
            "agreement": traditional_signal['recommendation'] == ai_analysis['recommendation'],
            "traditional": {
                "signal": traditional_signal['recommendation'],
                "confidence": traditional_signal.get('confidence_score', 0),
                "entry": traditional_signal.get('entry_price'),
                "stop": traditional_signal.get('stop_loss'),
                "target": traditional_signal.get('take_profit')
            },
            "ai_enhanced": {
                "signal": ai_analysis['recommendation'],
                "confidence": ai_analysis['confidence'],
                "entry": ai_analysis['entry_strategy']['price'],
                "stop": ai_analysis['stop_loss']['price'],
                "target": ai_analysis['take_profit']['target_1']['price']
            },
            "improvements": []
        }
        
        # Calculate improvements
        if comparison['agreement']:
            comparison['improvements'].append("✅ Signals align - high confidence trade")
        else:
            comparison['improvements'].append("⚠️ Signals conflict - review carefully")
        
        # Entry improvement
        if ai_analysis['entry_strategy']['timing'] == 'WAIT':
            comparison['improvements'].append(f"🎯 Better entry: Wait for {ai_analysis['entry_strategy'].get('trigger', 'confirmation')}")
        
        # Stop loss comparison
        trad_risk = abs(traditional_signal.get('entry_price', 0) - traditional_signal.get('stop_loss', 0))
        ai_risk = abs(ai_analysis['entry_strategy']['price'] - ai_analysis['stop_loss']['price'])
        if ai_risk < trad_risk:
            comparison['improvements'].append(f"🛡️ Tighter stop loss: ${ai_risk:.2f} vs ${trad_risk:.2f}")
        
        return comparison

def format_ai_result_for_display(ai_result):
    """
    Format AI analysis for beautiful dashboard display
    """
    html = f"""
    <div class="ai-analysis-panel" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; margin: 20px 0;">
        <h2 style="margin: 0 0 15px 0;">🤖 AI-Enhanced Analysis</h2>
        
        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h3 style="margin: 0 0 10px 0;">Recommendation: {ai_result['recommendation']}</h3>
            <div style="font-size: 2em; font-weight: bold;">{ai_result['confidence']}% Confidence</div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 15px;">
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px;">
                <strong>Entry:</strong><br/>
                ${ai_result['entry_strategy']['price']:.2f}<br/>
                <small>{ai_result['entry_strategy']['timing']}</small>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px;">
                <strong>Stop Loss:</strong><br/>
                ${ai_result['stop_loss']['price']:.2f}<br/>
                <small>{ai_result['stop_loss']['risk_pct']:.2f}% risk</small>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px;">
                <strong>Target:</strong><br/>
                ${ai_result['take_profit']['target_1']['price']:.2f}<br/>
                <small>+{ai_result['take_profit']['target_1']['gain_pct']:.1f}%</small>
            </div>
        </div>
        
        <div style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 8px;">
            <strong>📊 Pattern Detected:</strong> {ai_result['pattern']['type']}<br/>
            <strong>⏱️ Timeline:</strong> {ai_result['pattern']['timeline_days']} days<br/>
            <strong>📈 Success Probability:</strong> {ai_result['pattern']['probability']}%<br/>
            <strong>⚠️ Risk Level:</strong> {ai_result['risk_assessment']['level']}
        </div>
        
        <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; margin-top: 15px;">
            <strong>💡 Plain English:</strong><br/>
            {ai_result['plain_summary']}
        </div>
    </div>
    """
    return html
