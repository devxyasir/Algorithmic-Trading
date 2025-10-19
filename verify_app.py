"""
Final verification test - simulates app.py indicator calculation
"""
import pandas as pd
import yfinance as yf
import ta
import yaml

print("=" * 80)
print("FINAL VERIFICATION TEST")
print("Testing exact code from app.py")
print("=" * 80)

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Test with multiple symbols
test_symbols = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']

for symbol in test_symbols:
    print(f"\n📊 Testing {symbol}...")
    
    try:
        # Download data (same as app.py)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y", interval="1d")
        
        if df.empty or len(df) < 250:
            print(f"   ⚠️ Insufficient data ({len(df)} candles)")
            continue
        
        # Standardize columns (same as app.py)
        df.columns = [col.lower() for col in df.columns]
        
        # Calculate ALL indicators (EXACT copy from app.py)
        
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
        
        # PRICE ACTION PATTERNS (8)
        df['Higher_High'] = ((df['high'] > df['high'].shift(1)) & (df['high'].shift(1) > df['high'].shift(2))).fillna(False)
        df['Lower_Low'] = ((df['low'] < df['low'].shift(1)) & (df['low'].shift(1) < df['low'].shift(2))).fillna(False)
        df['Inside_Bar'] = ((df['high'] < df['high'].shift(1)) & (df['low'] > df['low'].shift(1))).fillna(False)
        df['Outside_Bar'] = ((df['high'] > df['high'].shift(1)) & (df['low'] < df['low'].shift(1))).fillna(False)
        
        df['Price_vs_SMA20'] = ((df['close'] / df['SMA_20'] - 1) * 100).fillna(0)
        df['Price_vs_SMA50'] = ((df['close'] / df['SMA_50'] - 1) * 100).fillna(0)
        df['Price_vs_SMA200'] = ((df['close'] / df['SMA_200'] - 1) * 100).fillna(0)
        df['Close_vs_Open'] = ((df['close'] / df['open'] - 1) * 100).fillna(0)
        
        # Check latest values
        latest = df.iloc[-1]
        
        print(f"   ✅ {symbol} SUCCESS!")
        print(f"      Total indicators: {len(df.columns) - 7}")
        print(f"      Latest RSI: {latest['RSI']:.2f}")
        print(f"      Latest MACD: {latest['MACD']:.2f}")
        print(f"      Latest Aroon Up: {latest['Aroon_up']:.2f}")
        
    except Exception as e:
        print(f"   ❌ {symbol} FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print("\n✅ If all symbols passed, app.py is ready to use!")
