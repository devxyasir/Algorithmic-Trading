import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
import yaml
import eel
from datetime import datetime, timedelta
import ta
import json

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create data and results folders if not exist
DATA_FOLDER = 'data'
RESULTS_FOLDER = 'results'
INDICATORS_FOLDER = 'results/indicators'
AI_RESULTS_FOLDER = 'results/ai_analysis'

for folder in [DATA_FOLDER, RESULTS_FOLDER, INDICATORS_FOLDER, AI_RESULTS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Initialize AI analyzer (optional)
AI_ENABLED = False
ai_analyzer = None

try:
    from ai_analyzer import AITradingAnalyzer
    ai_analyzer = AITradingAnalyzer()
    AI_ENABLED = True
    print("✅ AI Analysis: ENABLED (Google Gemini)")
    print(f"   Provider: {ai_analyzer.provider}")
    print(f"   Model: gemini-2.0-flash-exp")
    print(f"   API Key: Hardcoded (FREE - 1500 requests/day)")
except Exception as e:
    print(f"⚠️ AI Analysis: DISABLED ({str(e)})")
    print("   Error initializing AI analyzer")
    print(f"   Details: {str(e)}")

eel.init('web')

class IndicatorEngine:
    """Calculates 52+ technical indicators"""
    
    def __init__(self, df):
        self.df = df.copy()
        self.indicators = {}
        
    def calculate_all(self):
        """Calculate all 52+ indicators"""
        df = self.df
        
        # TREND INDICATORS (14)
        for period in config['indicators']['ema_periods']:
            df[f'EMA_{period}'] = ta.trend.ema_indicator(df['close'], window=int(period), fillna=True)
        
        df['SMA_20'] = ta.trend.sma_indicator(df['close'], window=20, fillna=True)
        df['SMA_50'] = ta.trend.sma_indicator(df['close'], window=50, fillna=True)
        df['SMA_200'] = ta.trend.sma_indicator(df['close'], window=200, fillna=True)
        
        # MACD
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9, fillna=True)
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_diff'] = macd.macd_diff()
        
        # Ichimoku Cloud
        ichimoku = ta.trend.IchimokuIndicator(df['high'], df['low'], window1=9, window2=26, window3=52, fillna=True)
        df['Ichimoku_a'] = ichimoku.ichimoku_a()
        df['Ichimoku_b'] = ichimoku.ichimoku_b()
        df['Ichimoku_base'] = ichimoku.ichimoku_base_line()
        df['Ichimoku_conversion'] = ichimoku.ichimoku_conversion_line()
        
        # Parabolic SAR
        df['PSAR'] = ta.trend.PSARIndicator(df['high'], df['low'], df['close'], step=0.02, max_step=0.2, fillna=True).psar()
        
        # Aroon (does NOT use close price, only high/low)
        aroon = ta.trend.AroonIndicator(df['high'], df['low'], window=25, fillna=True)
        df['Aroon_up'] = aroon.aroon_up()
        df['Aroon_down'] = aroon.aroon_down()
        
        # ADX
        df['ADX'] = ta.trend.adx(df['high'], df['low'], df['close'], window=14, fillna=True)
        df['DI_pos'] = ta.trend.adx_pos(df['high'], df['low'], df['close'], window=14, fillna=True)
        df['DI_neg'] = ta.trend.adx_neg(df['high'], df['low'], df['close'], window=14, fillna=True)
        
        # MOMENTUM INDICATORS (12)
        df['RSI'] = ta.momentum.rsi(df['close'], window=14, fillna=True)
        df['Stoch_K'] = ta.momentum.stoch(df['high'], df['low'], df['close'], window=14, smooth_window=3, fillna=True)
        df['Stoch_D'] = ta.momentum.stoch_signal(df['high'], df['low'], df['close'], window=14, smooth_window=3, fillna=True)
        df['Williams_R'] = ta.momentum.williams_r(df['high'], df['low'], df['close'], lbp=14, fillna=True)
        df['ROC'] = ta.momentum.roc(df['close'], window=12, fillna=True)
        df['TSI'] = ta.momentum.tsi(df['close'], window_slow=25, window_fast=13, fillna=True)
        df['UO'] = ta.momentum.ultimate_oscillator(df['high'], df['low'], df['close'], window1=7, window2=14, window3=28, fillna=True)
        df['Momentum'] = df['close'].diff(10).fillna(0)
        df['CCI'] = ta.trend.cci(df['high'], df['low'], df['close'], window=20, fillna=True)
        
        # VOLATILITY INDICATORS (8)
        df['ATR'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14, fillna=True)
        
        bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2, fillna=True)
        df['BB_upper'] = bb.bollinger_hband()
        df['BB_middle'] = bb.bollinger_mavg()
        df['BB_lower'] = bb.bollinger_lband()
        df['BB_width'] = bb.bollinger_wband()
        df['BB_pct'] = bb.bollinger_pband()
        
        kc = ta.volatility.KeltnerChannel(df['high'], df['low'], df['close'], window=20, fillna=True)
        df['KC_upper'] = kc.keltner_channel_hband()
        df['KC_lower'] = kc.keltner_channel_lband()
        
        df['DC_upper'] = ta.volatility.donchian_channel_hband(df['high'], df['low'], df['close'], window=20, fillna=True)
        df['DC_lower'] = ta.volatility.donchian_channel_lband(df['high'], df['low'], df['close'], window=20, fillna=True)
        
        # VOLUME INDICATORS (10)
        df['OBV'] = ta.volume.on_balance_volume(df['close'], df['volume'], fillna=True)
        df['CMF'] = ta.volume.chaikin_money_flow(df['high'], df['low'], df['close'], df['volume'], window=20, fillna=True)
        df['MFI'] = ta.volume.money_flow_index(df['high'], df['low'], df['close'], df['volume'], window=14, fillna=True)
        df['FI'] = ta.volume.force_index(df['close'], df['volume'], window=13, fillna=True)
        df['EOM'] = ta.volume.ease_of_movement(df['high'], df['low'], df['volume'], window=14, fillna=True)
        df['VPT'] = ta.volume.volume_price_trend(df['close'], df['volume'], fillna=True)
        df['NVI'] = ta.volume.negative_volume_index(df['close'], df['volume'], fillna=True)
        df['VWAP'] = ta.volume.volume_weighted_average_price(df['high'], df['low'], df['close'], df['volume'], window=14, fillna=True)
        
        df['Volume_SMA'] = df['volume'].rolling(window=20, min_periods=1).mean()
        df['Volume_Ratio'] = (df['volume'] / df['Volume_SMA']).fillna(1.0)
        
        # PIVOT POINTS (Classic Formula)
        df['Pivot'] = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
        df['R1'] = (2 * df['Pivot']) - df['low'].shift(1)
        df['S1'] = (2 * df['Pivot']) - df['high'].shift(1)
        df['R2'] = df['Pivot'] + (df['high'].shift(1) - df['low'].shift(1))
        df['S2'] = df['Pivot'] - (df['high'].shift(1) - df['low'].shift(1))
        df['R3'] = df['high'].shift(1) + 2 * (df['Pivot'] - df['low'].shift(1))
        df['S3'] = df['low'].shift(1) - 2 * (df['high'].shift(1) - df['Pivot'])
        
        # STANDARD DEVIATION BANDS (Price Mean-Reversion)
        price_mean = df['close'].rolling(window=20, min_periods=1).mean()
        price_std = df['close'].rolling(window=20, min_periods=1).std()
        df['Mean_Price'] = price_mean
        df['StdDev_1_Upper'] = price_mean + (1 * price_std)
        df['StdDev_1_Lower'] = price_mean - (1 * price_std)
        df['StdDev_2_Upper'] = price_mean + (2 * price_std)
        df['StdDev_2_Lower'] = price_mean - (2 * price_std)
        df['StdDev_3_Upper'] = price_mean + (3 * price_std)
        df['StdDev_3_Lower'] = price_mean - (3 * price_std)
        
        # MOVING AVERAGE CROSSOVERS
        df['SMA_3'] = ta.trend.sma_indicator(df['close'], window=3, fillna=True)
        df['SMA_10'] = ta.trend.sma_indicator(df['close'], window=10, fillna=True)
        df['MA_3_10_Diff'] = df['SMA_3'] - df['SMA_10']
        
        # PRICE ACTION PATTERNS (8)
        df['Higher_High'] = ((df['high'] > df['high'].shift(1)) & (df['high'].shift(1) > df['high'].shift(2))).fillna(False)
        df['Lower_Low'] = ((df['low'] < df['low'].shift(1)) & (df['low'].shift(1) < df['low'].shift(2))).fillna(False)
        df['Inside_Bar'] = ((df['high'] < df['high'].shift(1)) & (df['low'] > df['low'].shift(1))).fillna(False)
        df['Outside_Bar'] = ((df['high'] > df['high'].shift(1)) & (df['low'] < df['low'].shift(1))).fillna(False)
        
        df['Price_vs_SMA20'] = ((df['close'] / df['SMA_20'] - 1) * 100).fillna(0)
        df['Price_vs_SMA50'] = ((df['close'] / df['SMA_50'] - 1) * 100).fillna(0)
        df['Price_vs_SMA200'] = ((df['close'] / df['SMA_200'] - 1) * 100).fillna(0)
        df['Close_vs_Open'] = ((df['close'] / df['open'] - 1) * 100).fillna(0)
        
        self.df = df
        return df
    
    def get_latest_values(self):
        """Get latest indicator values"""
        latest = self.df.iloc[-1]
        return latest.to_dict()
    
    def get_all_indicators_for_export(self):
        """Get all 52+ indicators in readable format"""
        latest = self.df.iloc[-1]
        
        indicators = {
            # TREND (14)
            'EMA_9': latest['EMA_9'],
            'EMA_20': latest['EMA_20'],
            'EMA_50': latest['EMA_50'],
            'EMA_100': latest['EMA_100'],
            'EMA_200': latest['EMA_200'],
            'EMA_250': latest['EMA_250'],
            'SMA_20': latest['SMA_20'],
            'SMA_50': latest['SMA_50'],
            'SMA_200': latest['SMA_200'],
            'MACD': latest['MACD'],
            'MACD_Signal': latest['MACD_signal'],
            'MACD_Histogram': latest['MACD_diff'],
            'ADX': latest['ADX'],
            'DI_Positive': latest['DI_pos'],
            'DI_Negative': latest['DI_neg'],
            
            # MOMENTUM (12)
            'RSI': latest['RSI'],
            'Stochastic_K': latest['Stoch_K'],
            'Stochastic_D': latest['Stoch_D'],
            'Williams_R': latest['Williams_R'],
            'ROC': latest['ROC'],
            'TSI': latest['TSI'],
            'Ultimate_Oscillator': latest['UO'],
            'Momentum': latest['Momentum'],
            'CCI': latest['CCI'],
            
            # VOLATILITY (8)
            'ATR': latest['ATR'],
            'Bollinger_Upper': latest['BB_upper'],
            'Bollinger_Middle': latest['BB_middle'],
            'Bollinger_Lower': latest['BB_lower'],
            'Bollinger_Width': latest['BB_width'],
            'Bollinger_Percent': latest['BB_pct'],
            
            # VOLUME (10)
            'OBV': latest['OBV'],
            'CMF': latest['CMF'],
            'MFI': latest['MFI'],
            'Force_Index': latest['FI'],
            'EOM': latest['EOM'],
            'VPT': latest['VPT'],
            'NVI': latest['NVI'],
            'VWAP': latest['VWAP'],
            'Volume_SMA': latest['Volume_SMA'],
            'Volume_Ratio': latest['Volume_Ratio'],
            
            # PRICE ACTION (8)
            'Price_vs_SMA20_Pct': latest['Price_vs_SMA20'],
            'Price_vs_SMA50_Pct': latest['Price_vs_SMA50'],
            'Price_vs_SMA200_Pct': latest['Price_vs_SMA200'],
            'Close_vs_Open_Pct': latest['Close_vs_Open'],
            'Parabolic_SAR': latest['PSAR'],
            'Aroon_Up': latest['Aroon_up'],
            'Aroon_Down': latest['Aroon_down'],
            'Ichimoku_A': latest['Ichimoku_a'],
            'Ichimoku_B': latest['Ichimoku_b'],
        }
        
        return indicators

class TradingAnalyzer:
    """Analyzes stocks and generates BUY/SELL/HOLD signals"""
    
    def __init__(self, symbol, df):
        self.symbol = symbol
        self.df = df
        self.engine = IndicatorEngine(df)
        self.engine.calculate_all()
        self.latest = self.engine.df.iloc[-1]
        self.prev = self.engine.df.iloc[-2]
        
    def analyze(self):
        """Generate comprehensive analysis with IMPROVED scoring"""
        signal_score = 0
        buy_signals = 0
        sell_signals = 0
        reasons = []
        key_indicators = []
        
        # TREND ANALYSIS (40 points) - More weight
        ema_aligned_bull = self.latest['EMA_9'] > self.latest['EMA_20'] > self.latest['EMA_50']
        ema_aligned_bear = self.latest['EMA_9'] < self.latest['EMA_20'] < self.latest['EMA_50']
        
        if ema_aligned_bull:
            signal_score += 20
            buy_signals += 1
            reasons.append("✅ Strong uptrend: EMA alignment (9>20>50)")
        elif ema_aligned_bear:
            signal_score -= 20
            sell_signals += 1
            reasons.append("❌ Strong downtrend: EMA alignment (9<20<50)")
        
        price_above_200 = self.latest['close'] > self.latest['EMA_200']
        if price_above_200:
            signal_score += 15
            buy_signals += 1
            reasons.append("✅ Price above 200 EMA (bullish long-term)")
        else:
            signal_score -= 15
            sell_signals += 1
            reasons.append("❌ Price below 200 EMA (bearish long-term)")
            
        if self.latest['ADX'] > 25:
            if ema_aligned_bull:
                signal_score += 5
                reasons.append(f"✅ Strong uptrend (ADX: {self.latest['ADX']:.1f})")
            elif ema_aligned_bear:
                signal_score -= 5
                reasons.append(f"❌ Strong downtrend (ADX: {self.latest['ADX']:.1f})")
        
        key_indicators.append({"name": "EMA 9/20/50", "value": f"{self.latest['EMA_9']:.2f}/{self.latest['EMA_20']:.2f}/{self.latest['EMA_50']:.2f}"})
        key_indicators.append({"name": "ADX", "value": f"{self.latest['ADX']:.1f}"})
        
        # MOMENTUM ANALYSIS (35 points) - Enhanced
        rsi = self.latest['RSI']
        stoch_k = self.latest['Stoch_K']
        
        # RSI Analysis - Progressive scoring
        if rsi < 20:
            signal_score += 25
            buy_signals += 1
            reasons.append(f"✅ EXTREME Oversold RSI ({rsi:.1f}) - strong bounce")
        elif rsi < 30:
            signal_score += 20
            buy_signals += 1
            reasons.append(f"✅ Oversold RSI ({rsi:.1f}) - bounce likely")
        elif 40 <= rsi <= 60:
            signal_score += 10
            reasons.append(f"✅ RSI healthy ({rsi:.1f})")
        elif rsi > 80:
            signal_score -= 25
            sell_signals += 1
            reasons.append(f"❌ EXTREME Overbought RSI ({rsi:.1f}) - strong pullback")
        elif rsi > 70:
            signal_score -= 20
            sell_signals += 1
            reasons.append(f"❌ Overbought RSI ({rsi:.1f}) - pullback likely")
        
        # Stochastic Oscillator
        if stoch_k < 20:
            signal_score += 10
            buy_signals += 1
            reasons.append(f"✅ Stochastic oversold ({stoch_k:.1f})")
        elif stoch_k > 80:
            signal_score -= 10
            sell_signals += 1
            reasons.append(f"❌ Stochastic overbought ({stoch_k:.1f})")
        
        # MACD Crossovers
        if self.latest['MACD'] > self.latest['MACD_signal'] and self.prev['MACD'] <= self.prev['MACD_signal']:
            signal_score += 15
            buy_signals += 1
            reasons.append("✅ MACD bullish crossover")
        elif self.latest['MACD'] < self.latest['MACD_signal'] and self.prev['MACD'] >= self.prev['MACD_signal']:
            signal_score -= 15
            sell_signals += 1
            reasons.append("❌ MACD bearish crossover")
        elif self.latest['MACD'] > self.latest['MACD_signal']:
            signal_score += 5
        elif self.latest['MACD'] < self.latest['MACD_signal']:
            signal_score -= 5
        
        key_indicators.append({"name": "RSI", "value": f"{rsi:.1f}"})
        key_indicators.append({"name": "Stochastic", "value": f"{stoch_k:.1f}"})
        key_indicators.append({"name": "MACD", "value": f"{self.latest['MACD']:.3f}"})
        
        # VOLUME ANALYSIS (20 points)
        if self.latest['Volume_Ratio'] > 1.5:
            if signal_score > 0:
                signal_score += 10
                reasons.append(f"✅ High volume confirms bullish move ({self.latest['Volume_Ratio']:.1f}x)")
            else:
                signal_score -= 10
                reasons.append(f"❌ High volume confirms bearish move ({self.latest['Volume_Ratio']:.1f}x)")
        elif self.latest['Volume_Ratio'] < 0.7:
            signal_score = int(signal_score * 0.8)
            reasons.append("⚠️ Low volume - weak conviction")
        
        mfi = self.latest['MFI']
        if 40 <= mfi <= 60:
            signal_score += 10
        elif mfi > 80:
            signal_score -= 10
            sell_signals += 1
        elif mfi < 20:
            signal_score += 10
            buy_signals += 1
        
        key_indicators.append({"name": "Volume Ratio", "value": f"{self.latest['Volume_Ratio']:.2f}x"})
        key_indicators.append({"name": "MFI", "value": f"{mfi:.1f}"})
        
        # PIVOT POINTS & SUPPORT/RESISTANCE (15 points)
        current_price = self.latest['close']
        pivot = self.latest['Pivot']
        r1 = self.latest['R1']
        s1 = self.latest['S1']
        
        # Price near resistance - potential SELL
        if current_price >= r1 * 0.98:
            signal_score -= 10
            sell_signals += 1
            reasons.append(f"❌ Price near R1 resistance ({r1:.2f})")
        # Price near support - potential BUY
        elif current_price <= s1 * 1.02:
            signal_score += 10
            buy_signals += 1
            reasons.append(f"✅ Price near S1 support ({s1:.2f})")
        # Price above pivot - bullish
        elif current_price > pivot:
            signal_score += 5
            reasons.append(f"✅ Price above pivot ({pivot:.2f})")
        else:
            signal_score -= 5
            reasons.append(f"❌ Price below pivot ({pivot:.2f})")
        
        key_indicators.append({"name": "Pivot", "value": f"{pivot:.2f}"})
        key_indicators.append({"name": "R1/S1", "value": f"{r1:.2f}/{s1:.2f}"})
        
        # VOLATILITY ANALYSIS (10 points)
        bb_pct = self.latest['BB_pct']
        atr_pct = self.latest['ATR'] / current_price
        
        if bb_pct > 0.9:
            signal_score -= 15
            sell_signals += 1
            reasons.append("❌ Upper BB extreme - strong sell signal")
        elif bb_pct > 0.8:
            signal_score -= 8
            reasons.append("⚠️ Near upper BB - potential pullback")
        elif bb_pct < 0.1:
            signal_score += 15
            buy_signals += 1
            reasons.append("✅ Lower BB extreme - strong buy signal")
        elif bb_pct < 0.2:
            signal_score += 8
            reasons.append("✅ Near lower BB - potential bounce")
        
        if atr_pct < 0.02:
            signal_score += 5
            reasons.append("✅ Low volatility (stable)")
        
        key_indicators.append({"name": "ATR %", "value": f"{atr_pct*100:.1f}%"})
        key_indicators.append({"name": "BB Position", "value": f"{bb_pct*100:.0f}%"})
        
        # PRICE ACTION PATTERNS (10 points)
        if self.latest['Higher_High'] and ema_aligned_bull:
            signal_score += 10
            buy_signals += 1
            reasons.append("✅ Higher highs in uptrend")
        elif self.latest['Lower_Low'] and ema_aligned_bear:
            signal_score -= 10
            sell_signals += 1
            reasons.append("❌ Lower lows in downtrend")
        
        # MA CROSSOVER (3-10 day)
        if self.latest['SMA_3'] > self.latest['SMA_10'] and self.prev['SMA_3'] <= self.prev['SMA_10']:
            signal_score += 10
            buy_signals += 1
            reasons.append("✅ 3-10 MA bullish crossover")
        elif self.latest['SMA_3'] < self.latest['SMA_10'] and self.prev['SMA_3'] >= self.prev['SMA_10']:
            signal_score -= 10
            sell_signals += 1
            reasons.append("❌ 3-10 MA bearish crossover")
        
        # EXTREME CONDITIONS OVERRIDE (Critical Rule-Based Logic)
        extreme_overbought = (rsi > 80 or stoch_k > 90 or bb_pct > 0.95)
        extreme_oversold = (rsi < 20 or stoch_k < 10 or bb_pct < 0.05)
        
        # If EXTREME overbought AND price near resistance → Force SELL
        if extreme_overbought and (current_price >= r1 * 0.95 or bb_pct > 0.9):
            signal_score = min(signal_score, -40)  # Force negative
            sell_signals += 3  # Add weight to sell
            reasons.append("🔴 EXTREME OVERBOUGHT + Resistance → SELL signal")
        
        # If EXTREME oversold AND price near support → Force BUY
        elif extreme_oversold and (current_price <= s1 * 1.05 or bb_pct < 0.1):
            signal_score = max(signal_score, 40)  # Force positive
            buy_signals += 3  # Add weight to buy
            reasons.append("🟢 EXTREME OVERSOLD + Support → BUY signal")
        
        # ═══════════════════════════════════════════════════════════════════════
        # TECHNICAL ANALYSIS-BASED DECISION (Not Majority Voting)
        # Each condition is based on proven technical analysis principles
        # ═══════════════════════════════════════════════════════════════════════
        
        # STEP 1: Analyze Trend Strength (Most Important)
        trend_score = 0
        trend_confidence = 0
        
        # Strong uptrend conditions
        if ema_aligned_bull and price_above_200 and self.latest['ADX'] > 25:
            trend_score = 1  # Bullish
            trend_confidence = min(self.latest['ADX'], 100)
        # Strong downtrend conditions
        elif ema_aligned_bear and not price_above_200 and self.latest['ADX'] > 25:
            trend_score = -1  # Bearish
            trend_confidence = min(self.latest['ADX'], 100)
        else:
            trend_score = 0  # No clear trend
            trend_confidence = 0
        
        # STEP 2: Analyze Momentum (Confirm trend or reversal)
        momentum_score = 0
        momentum_confidence = 0
        
        # Bullish momentum
        if rsi > 50 and self.latest['MACD'] > self.latest['MACD_signal']:
            momentum_score = 1
            momentum_confidence = min((rsi - 50) * 2, 50) + 25  # 25-75%
        # Bearish momentum
        elif rsi < 50 and self.latest['MACD'] < self.latest['MACD_signal']:
            momentum_score = -1
            momentum_confidence = min((50 - rsi) * 2, 50) + 25  # 25-75%
        # Oversold reversal (bullish)
        elif rsi < 30 and stoch_k < 20:
            momentum_score = 1
            momentum_confidence = 70  # High confidence in reversal
        # Overbought reversal (bearish)
        elif rsi > 70 and stoch_k > 80:
            momentum_score = -1
            momentum_confidence = 70  # High confidence in reversal
        else:
            momentum_score = 0
            momentum_confidence = 0
        
        # STEP 3: Analyze Price Position (Support/Resistance)
        position_score = 0
        position_confidence = 0
        
        # At support (bullish)
        if current_price <= s1 * 1.02 or bb_pct < 0.2:
            position_score = 1
            position_confidence = 60
        # At resistance (bearish)
        elif current_price >= r1 * 0.98 or bb_pct > 0.8:
            position_score = -1
            position_confidence = 60
        # Breakout above resistance (bullish)
        elif current_price > r1 and self.latest['Volume_Ratio'] > 1.5:
            position_score = 1
            position_confidence = 75
        # Breakdown below support (bearish)
        elif current_price < s1 and self.latest['Volume_Ratio'] > 1.5:
            position_score = -1
            position_confidence = 75
        else:
            position_score = 0
            position_confidence = 0
        
        # STEP 4: Analyze Volume (Confirms moves)
        volume_score = 0
        volume_confidence = 0
        
        if self.latest['Volume_Ratio'] > 1.5 and mfi > 60:
            volume_score = 1  # Strong buying
            volume_confidence = min(self.latest['Volume_Ratio'] * 30, 70)
        elif self.latest['Volume_Ratio'] > 1.5 and mfi < 40:
            volume_score = -1  # Strong selling
            volume_confidence = min(self.latest['Volume_Ratio'] * 30, 70)
        elif self.latest['Volume_Ratio'] < 0.7:
            volume_score = 0  # Weak volume = unreliable
            volume_confidence = 0
        else:
            volume_score = 0
            volume_confidence = 40  # Average volume = neutral
        
        # STEP 5: Calculate Overall Decision (Weight-Based, Not Majority)
        # Weights: Trend=40%, Momentum=30%, Position=20%, Volume=10%
        
        bullish_evidence = 0
        bearish_evidence = 0
        confidence_components = []
        
        # Trend (40% weight) - Most important
        if trend_score == 1:
            bullish_evidence += 40
            confidence_components.append(('trend', trend_confidence, 0.4))
        elif trend_score == -1:
            bearish_evidence += 40
            confidence_components.append(('trend', trend_confidence, 0.4))
        
        # Momentum (30% weight)
        if momentum_score == 1:
            bullish_evidence += 30
            confidence_components.append(('momentum', momentum_confidence, 0.3))
        elif momentum_score == -1:
            bearish_evidence += 30
            confidence_components.append(('momentum', momentum_confidence, 0.3))
        
        # Position (20% weight)
        if position_score == 1:
            bullish_evidence += 20
            confidence_components.append(('position', position_confidence, 0.2))
        elif position_score == -1:
            bearish_evidence += 20
            confidence_components.append(('position', position_confidence, 0.2))
        
        # Volume (10% weight)
        if volume_score == 1:
            bullish_evidence += 10
            confidence_components.append(('volume', volume_confidence, 0.1))
        elif volume_score == -1:
            bearish_evidence += 10
            confidence_components.append(('volume', volume_confidence, 0.1))
        
        # Calculate weighted average confidence (only from components that contributed)
        if confidence_components:
            total_weight = sum(weight for _, _, weight in confidence_components)
            weighted_conf = sum(conf * (weight/total_weight) for _, conf, weight in confidence_components)
            total_confidence = weighted_conf
        else:
            total_confidence = 0
        
        # STEP 6: Make Decision Based on Evidence Strength
        net_evidence = bullish_evidence - bearish_evidence
        
        # BUY Conditions (Professional Trading Rules):
        # Require STRONG evidence - at least 2 of 4 components bullish
        # AND trend OR momentum must be bullish (can't buy without direction)
        # AND confidence >= 55% (professional threshold)
        if (net_evidence >= 60 and 
            (trend_score == 1 or momentum_score == 1) and
            bb_pct < 0.85 and
            total_confidence >= 55 and
            bullish_evidence >= 60):  # At least 60% bullish
            
            recommendation = "BUY"
            confidence = int(total_confidence)
            
            # Add clear explanation
            reasons_list = []
            if trend_score == 1:
                reasons_list.append(f"📈 Confirmed uptrend (ADX {self.latest['ADX']:.1f})")
            if momentum_score == 1:
                if rsi < 30:
                    reasons_list.append(f"💪 Oversold bounce setup (RSI {rsi:.1f})")
                else:
                    reasons_list.append(f"💪 Strong bullish momentum (RSI {rsi:.1f})")
            if position_score == 1:
                reasons_list.append(f"🎯 Good entry at support (${s1:.2f})")
            if volume_score == 1:
                reasons_list.append(f"📊 Volume confirms ({self.latest['Volume_Ratio']:.1f}x avg)")
            
            # Replace old reasons with new clear ones
            reasons = reasons_list
            reasons.append(f"✅ {len([c for c in confidence_components])}/4 factors align → BUY")
        
        # SELL Conditions (Professional Trading Rules):
        # Require STRONG evidence - at least 2 of 4 components bearish
        # AND trend OR momentum must be bearish
        # AND confidence >= 55%
        elif (net_evidence <= -60 and
              (trend_score == -1 or momentum_score == -1) and
              bb_pct > 0.15 and
              total_confidence >= 55 and
              bearish_evidence >= 60):  # At least 60% bearish
            
            recommendation = "SELL"
            confidence = int(total_confidence)
            
            # Add clear explanation
            reasons_list = []
            if trend_score == -1:
                reasons_list.append(f"📉 Confirmed downtrend (ADX {self.latest['ADX']:.1f})")
            if momentum_score == -1:
                if rsi > 70:
                    reasons_list.append(f"⚠️ Overbought reversal (RSI {rsi:.1f})")
                else:
                    reasons_list.append(f"⚠️ Weak bearish momentum (RSI {rsi:.1f})")
            if position_score == -1:
                reasons_list.append(f"🚫 At resistance level (${r1:.2f})")
            if volume_score == -1:
                reasons_list.append(f"📊 Volume confirms selling ({self.latest['Volume_Ratio']:.1f}x avg)")
            
            # Replace old reasons with new clear ones
            reasons = reasons_list
            reasons.append(f"❌ {len([c for c in confidence_components])}/4 factors align → SELL")
        
        # HOLD (Not enough evidence to trade) - MOST COMMON
        else:
            recommendation = "HOLD"
            
            # Confidence in HOLD = how certain we are NOT to trade
            # Higher when evidence is weak or mixed
            hold_certainty = 0
            
            if abs(net_evidence) < 60:
                hold_certainty += 40
            if trend_score == 0 or momentum_score == 0:
                hold_certainty += 30
            if total_confidence < 55:
                hold_certainty += 20
            if atr_pct > 0.08:
                hold_certainty += 10
            
            confidence = min(int(hold_certainty), 85)
            
            # Clear explanation why HOLD
            reasons_list = []
            if abs(net_evidence) < 60:
                reasons_list.append(f"⚠️ Insufficient evidence (Bull:{bullish_evidence}% Bear:{bearish_evidence}%)")
            if trend_score == 0:
                reasons_list.append(f"⚠️ No clear trend (ADX {self.latest['ADX']:.1f} < 25 or EMAs mixed)")
            if momentum_score == 0:
                reasons_list.append(f"⚠️ Momentum unclear (RSI {rsi:.1f} near neutral)")
            if total_confidence < 55:
                reasons_list.append(f"⚠️ Setup confidence too low ({total_confidence:.0f}% < 55% required)")
            if atr_pct > 0.08:
                reasons_list.append(f"⚠️ High volatility ({atr_pct*100:.1f}%) - wait for stability")
            
            reasons = reasons_list if reasons_list else ["⚠️ No clear trading setup"]
        
        # Calculate entry, stop, target
        current_price = self.latest['close']
        atr = self.latest['ATR']
        
        if recommendation == "BUY":
            entry_price = current_price
            stop_loss = entry_price - (atr * config['risk_management']['atr_stop_multiplier'])
            take_profit = entry_price + (atr * config['risk_management']['atr_target_multiplier'])
        elif recommendation == "SELL":
            entry_price = current_price
            stop_loss = entry_price + (atr * config['risk_management']['atr_stop_multiplier'])
            take_profit = entry_price - (atr * config['risk_management']['atr_target_multiplier'])
        else:
            entry_price = current_price
            stop_loss = None
            take_profit = None
        
        risk_pct = ((entry_price - stop_loss) / entry_price * 100) if stop_loss else 0
        reward_pct = ((take_profit - entry_price) / entry_price * 100) if take_profit else 0
        risk_reward = abs(reward_pct / risk_pct) if risk_pct != 0 else 0
        
        rationale = " | ".join(reasons[:4])
        
        return {
            "symbol": self.symbol,
            "analysis_time": datetime.now().isoformat(),
            "recommendation": recommendation,
            "entry_price": round(entry_price, 2),
            "stop_loss": round(stop_loss, 2) if stop_loss else None,
            "take_profit": round(take_profit, 2) if take_profit else None,
            "confidence_score": int(confidence),
            "risk_pct": round(risk_pct, 2),
            "reward_pct": round(reward_pct, 2),
            "risk_reward_ratio": round(risk_reward, 2),
            "rationale": rationale,
            "key_indicators": key_indicators,
            "raw_score": signal_score
        }

def download_and_save_data(symbol, timeframe="1d"):
    """Download data from yfinance and save to CSV"""
    try:
        eel.send_status(f"📥 Downloading {symbol}...")()
        
        # Download maximum available data with timeout
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="max", interval=timeframe)
        
        if df is None or df.empty:
            return {"error": f"No data available for {symbol} (delisted or invalid ticker)"}
        
        if len(df) < 10:
            return {"error": f"Too few data points ({len(df)}) for {symbol}"}
        
        # Save to CSV (overwrite existing)
        filepath = os.path.join(DATA_FOLDER, f"{symbol}.csv")
        df.to_csv(filepath)
        
        eel.send_status(f"✅ Saved {symbol} ({len(df)} candles)")()
        
        return {"success": True, "filepath": filepath, "rows": len(df)}
        
    except KeyboardInterrupt:
        # Allow user to cancel
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_details = str(e)
        
        # Provide more helpful error messages
        if "404" in error_details or "No data found" in error_details:
            return {"error": f"Symbol {symbol} not found (404)"}
        elif "ConnectionError" in error_type or "Timeout" in error_type:
            return {"error": f"Network error downloading {symbol}"}
        elif "HTTPError" in error_type:
            return {"error": f"HTTP error for {symbol}: {error_details}"}
        else:
            return {"error": f"{error_type}: {error_details}"}

def load_data_from_file(symbol):
    """Load data from saved CSV file"""
    try:
        filepath = os.path.join(DATA_FOLDER, f"{symbol}.csv")
        
        if not os.path.exists(filepath):
            return None
        
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        
        if df.empty:
            return None
            
        return df
        
    except Exception as e:
        print(f"Warning: Failed to load {symbol}: {str(e)}")
        return None

@eel.expose
def analyze_symbol(symbol, timeframe="1d"):
    """Analyze a single symbol from saved data"""
    try:
        # First, download and save/update data
        download_result = download_and_save_data(symbol, timeframe)
        
        if "error" in download_result:
            eel.send_status(f"❌ {symbol} - {download_result['error']}")()
            return {"symbol": symbol, "error": download_result['error']}
        
        # Load data from saved file
        df = load_data_from_file(symbol)
        
        if df is None or df.empty:
            error_msg = f"Failed to load data for {symbol}"
            eel.send_status(f"❌ {symbol} - {error_msg}")()
            return {"symbol": symbol, "error": error_msg}
        
        if len(df) < config['analysis']['min_data_points']:
            error_msg = f"Insufficient data ({len(df)} candles, need {config['analysis']['min_data_points']})"
            eel.send_status(f"❌ {symbol} - {error_msg}")()
            return {"symbol": symbol, "error": error_msg}
        
        # Standardize column names
        df.columns = [col.lower() for col in df.columns]
        
        eel.send_status(f"🔍 Analyzing {symbol}...")()
        
        # Analyze
        analyzer = TradingAnalyzer(symbol, df)
        result = analyzer.analyze()
        
        # Save all 52+ indicators to CSV for this symbol
        all_indicators = analyzer.engine.get_all_indicators_for_export()
        indicators_df = pd.DataFrame([all_indicators])
        indicators_df.insert(0, 'Symbol', symbol)
        indicators_df.insert(1, 'Timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        indicator_file = os.path.join(INDICATORS_FOLDER, f"{symbol}_indicators.csv")
        indicators_df.to_csv(indicator_file, index=False)
        
        # Add all indicators to result for UI display
        result['all_indicators'] = all_indicators
        
        eel.send_status(f"✅ {symbol} complete")()
        
        return result
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        eel.send_status(f"❌ {symbol} - Error: {error_msg}")()
        return {"symbol": symbol, "error": error_msg}

@eel.expose
def analyze_batch(symbols, timeframe="1d"):
    """Analyze multiple symbols - continues even if some fail"""
    results = []
    failed_count = 0
    success_count = 0
    
    for i, symbol in enumerate(symbols, 1):
        try:
            eel.send_status(f"Processing {symbol} ({i}/{len(symbols)})...")()
            
            result = analyze_symbol(symbol, timeframe)
            results.append(result)
            
            # Track stats
            if "error" in result:
                failed_count += 1
            else:
                success_count += 1
            
            eel.update_progress(symbol, result)()
            
        except Exception as e:
            # Catch any unexpected errors and continue
            error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
            eel.send_status(f"❌ {symbol} - {error_msg}")()
            results.append({"symbol": symbol, "error": error_msg})
            failed_count += 1
            eel.update_progress(symbol, {"symbol": symbol, "error": error_msg})()
    
    # Final summary
    eel.send_status(f"✅ Batch complete: {success_count} succeeded, {failed_count} failed")()
    
    return results

@eel.expose
def read_symbols_from_csv(file_content=None):
    """Read symbols from uploaded CSV or default template"""
    try:
        if file_content:
            # Parse uploaded CSV content
            from io import StringIO
            df = pd.read_csv(StringIO(file_content))
        else:
            # Use template file
            df = pd.read_csv('symbols/1.csv')
        
        # Extract Symbol column
        if 'Symbol' in df.columns:
            symbols = df['Symbol'].dropna().tolist()
            # Remove any non-symbol rows (like footer text)
            symbols = [s for s in symbols if isinstance(s, str) and len(s) <= 10 and s.isupper()]
            return {"success": True, "symbols": symbols}
        else:
            return {"error": "CSV must have a 'Symbol' column"}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def export_results(results):
    """Export results to CSV in results folder"""
    try:
        # Remove 'all_indicators' from each result for main CSV (too many columns)
        simplified_results = []
        for r in results:
            r_copy = r.copy()
            if 'all_indicators' in r_copy:
                del r_copy['all_indicators']
            simplified_results.append(r_copy)
        
        # Save main results
        df = pd.DataFrame(simplified_results)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"trading_signals_{timestamp}.csv"
        filepath = os.path.join(RESULTS_FOLDER, filename)
        df.to_csv(filepath, index=False)
        
        return {"success": True, "filename": filename, "path": filepath}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def clear_old_data():
    """Clear old data files and indicator analysis before starting new analysis"""
    try:
        import shutil
        
        deleted_counts = {
            "data_files": 0,
            "indicator_files": 0,
            "ai_files": 0
        }
        
        # Clear data folder (OHLCV CSV files)
        if os.path.exists(DATA_FOLDER):
            data_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.csv')]
            for file in data_files:
                os.remove(os.path.join(DATA_FOLDER, file))
                deleted_counts["data_files"] += 1
        
        # Clear indicators folder
        if os.path.exists(INDICATORS_FOLDER):
            indicator_files = [f for f in os.listdir(INDICATORS_FOLDER) if f.endswith('.csv')]
            for file in indicator_files:
                os.remove(os.path.join(INDICATORS_FOLDER, file))
                deleted_counts["indicator_files"] += 1
        
        # Clear AI analysis folder
        if os.path.exists(AI_RESULTS_FOLDER):
            ai_files = [f for f in os.listdir(AI_RESULTS_FOLDER) if f.endswith('.json')]
            for file in ai_files:
                os.remove(os.path.join(AI_RESULTS_FOLDER, file))
                deleted_counts["ai_files"] += 1
        
        return {
            "success": True,
            "deleted": deleted_counts,
            "message": f"Cleared {deleted_counts['data_files']} data files, {deleted_counts['indicator_files']} indicator files, {deleted_counts['ai_files']} AI analysis files"
        }
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def get_data_folder_info():
    """Get info about saved data files"""
    try:
        files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.csv')]
        total_size = sum(os.path.getsize(os.path.join(DATA_FOLDER, f)) for f in files)
        return {
            "total_files": len(files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "symbols": [f.replace('.csv', '') for f in files]
        }
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def get_ai_status():
    """Check if AI analysis is available"""
    return {
        "enabled": AI_ENABLED,
        "provider": ai_analyzer.provider if ai_analyzer else None,
        "model": ai_analyzer.model if ai_analyzer else None
    }

@eel.expose
def analyze_with_ai(symbol, traditional_result):
    """
    Perform AI analysis on a symbol
    Called when user clicks "AI Analyze" button
    """
    if not AI_ENABLED or not ai_analyzer:
        return {
            "error": "AI analysis not initialized. Check console for error details.",
            "enabled": False
        }
    
    try:
        # Prepare data for AI
        indicators = traditional_result.get('all_indicators', {})
        price_data = {
            'close': traditional_result.get('entry_price', 0),
            'daily_change': traditional_result.get('raw_score', 0),
            'volume': indicators.get('Volume_SMA', 0),
            'avg_volume': indicators.get('Volume_SMA', 0)
        }
        
        # Get AI analysis
        ai_result = ai_analyzer.analyze(symbol, indicators, price_data)
        
        # Check if AI returned an error
        if "error" in ai_result:
            return {
                "error": f"AI analysis failed: {ai_result.get('error')}",
                "enabled": True
            }
        
        # Save AI analysis to file
        ai_file = os.path.join(AI_RESULTS_FOLDER, f"{symbol}_ai_analysis.json")
        with open(ai_file, 'w') as f:
            json.dump(ai_result, f, indent=2)
        
        # Safely extract AI values with defaults
        ai_entry = ai_result.get('entry_strategy', {}).get('price', traditional_result.get('entry_price', 0))
        ai_stop = ai_result.get('stop_loss', {}).get('price', traditional_result.get('stop_loss', 0))
        ai_target = ai_result.get('take_profit', {}).get('target_1', {}).get('price', traditional_result.get('take_profit', 0))
        
        # Calculate consensus score
        trad_signal = traditional_result['recommendation']
        ai_signal = ai_result.get('recommendation', 'HOLD')
        trad_conf = traditional_result.get('confidence_score', 0)
        ai_conf = ai_result.get('confidence', 0)
        
        # Consensus logic
        signals_agree = trad_signal == ai_signal
        both_confident = trad_conf >= 60 and ai_conf >= 60
        
        if signals_agree and both_confident:
            consensus_score = "STRONG_AGREEMENT"
            consensus_rating = 95
            consensus_message = "🟢 HIGH CONFIDENCE: Both systems strongly agree - Best opportunity!"
        elif signals_agree and (trad_conf >= 50 or ai_conf >= 50):
            consensus_score = "MODERATE_AGREEMENT"
            consensus_rating = 75
            consensus_message = "🟡 MODERATE: Both agree but lower confidence - Proceed with caution"
        elif not signals_agree:
            consensus_score = "DISAGREEMENT"
            consensus_rating = 40
            consensus_message = "🔴 CONFLICTING SIGNALS: Systems disagree - High risk, consider HOLD"
        else:
            consensus_score = "WEAK_AGREEMENT"
            consensus_rating = 55
            consensus_message = "🟠 WEAK: Signals agree but low confidence - Not ideal"
        
        # Determine final recommendation
        if consensus_score == "STRONG_AGREEMENT":
            final_recommendation = trad_signal
            final_action = f"✅ RECOMMENDED: {trad_signal}"
        elif consensus_score == "MODERATE_AGREEMENT":
            final_recommendation = trad_signal
            final_action = f"⚠️ PROCEED CAUTIOUSLY: {trad_signal}"
        elif consensus_score == "DISAGREEMENT":
            final_recommendation = "HOLD"
            final_action = "❌ AVOID: Wait for clearer signal"
        else:
            final_recommendation = "HOLD"
            final_action = "⏸️ WAIT: Signal not strong enough"
        
        # Compare with traditional
        comparison = {
            "agreement": signals_agree,
            "consensus_score": consensus_score,
            "consensus_rating": consensus_rating,
            "consensus_message": consensus_message,
            "final_recommendation": final_recommendation,
            "final_action": final_action,
            "traditional": {
                "signal": trad_signal,
                "confidence": trad_conf,
                "entry": traditional_result.get('entry_price'),
                "stop": traditional_result.get('stop_loss'),
                "target": traditional_result.get('take_profit')
            },
            "ai_enhanced": {
                "signal": ai_signal,
                "confidence": ai_conf,
                "entry": ai_entry,
                "stop": ai_stop,
                "target": ai_target
            }
        }
        
        return {
            "success": True,
            "ai_analysis": ai_result,
            "comparison": comparison,
            "saved_to": ai_file
        }
        
    except KeyError as e:
        return {
            "error": f"AI response missing field: {str(e)}. AI may have returned incomplete data.",
            "enabled": True
        }
    except Exception as e:
        return {
            "error": f"Error: {str(e)}",
            "enabled": True
        }

if __name__ == '__main__':
    eel.start('dashboard.html', size=(1400, 900), port=8080)
