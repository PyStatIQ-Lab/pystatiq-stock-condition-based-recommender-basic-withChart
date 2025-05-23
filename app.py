import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import json
import urllib.parse

# NIFTY50 symbols with NSE: prefix for TradingView
NIFTY50_SYMBOLS = [
    "NSE:ADANIENT", "NSE:ADANIPORTS", "NSE:APOLLOHOSP", "NSE:ASIANPAINT", "NSE:AXISBANK",
    "NSE:BAJAJ-AUTO", "NSE:BAJFINANCE", "NSE:BAJAJFINSV", "NSE:BEL", "NSE:BPCL",
    "NSE:BHARTIARTL", "NSE:BRITANNIA", "NSE:CIPLA", "NSE:COALINDIA", "NSE:DRREDDY",
    "NSE:EICHERMOT", "NSE:GRASIM", "NSE:HCLTECH", "NSE:HDFCBANK", "NSE:HDFCLIFE",
    "NSE:HEROMOTOCO", "NSE:HINDALCO", "NSE:HINDUNILVR", "NSE:ICICIBANK", "NSE:ITC",
    "NSE:INDUSINDBK", "NSE:INFY", "NSE:JSWSTEEL", "NSE:KOTAKBANK", "NSE:LT",
    "NSE:M&M", "NSE:MARUTI", "NSE:NTPC", "NSE:NESTLEIND", "NSE:ONGC",
    "NSE:POWERGRID", "NSE:RELIANCE", "NSE:SBILIFE", "NSE:SHRIRAMFIN", "NSE:SBIN",
    "NSE:SUNPHARMA", "NSE:TCS", "NSE:TATACONSUM", "NSE:TATAMOTORS", "NSE:TATASTEEL",
    "NSE:TECHM", "NSE:TITAN", "NSE:TRENT", "NSE:ULTRACEMCO", "NSE:WIPRO"
]

def get_stock_data(symbol, period='1d'):
    try:
        yfinance_symbol = symbol.replace("NSE:", "") + ".NS"
        stock = yf.Ticker(yfinance_symbol)
        hist = stock.history(period=period)
        return hist.iloc[-1] if not hist.empty else None
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

def create_tradingview_url(symbol, current_price, stop_loss, target):
    base_url = "https://www.tradingview.com/chart/"
    
    # Create drawing configuration
    drawings = []
    
    # Current price line (blue)
    if current_price is not None:
        drawings.append({
            "tool": "HorizontalLine",
            "points": [{"time": 0, "price": current_price}],
            "options": {
                "color": "#2962FF",
                "linestyle": 0,
                "linewidth": 1,
                "axisLabelVisible": True,
                "title": f"Current: {current_price}"
            }
        })
    
    # Stop loss line (red)
    if stop_loss is not None:
        drawings.append({
            "tool": "HorizontalLine",
            "points": [{"time": 0, "price": stop_loss}],
            "options": {
                "color": "#F44336",
                "linestyle": 1,
                "linewidth": 2,
                "axisLabelVisible": True,
                "title": f"SL: {stop_loss}"
            }
        })
    
    # Target line (green)
    if target is not None:
        drawings.append({
            "tool": "HorizontalLine",
            "points": [{"time": 0, "price": target}],
            "options": {
                "color": "#4CAF50",
                "linestyle": 1,
                "linewidth": 2,
                "axisLabelVisible": True,
                "title": f"Target: {target}"
            }
        })
    
    if drawings:
        # Convert drawings to JSON and URL encode
        drawings_json = json.dumps(drawings)
        encoded_drawings = urllib.parse.quote(drawings_json)
        return f"{base_url}?symbol={symbol}&interval=1D&drawing={encoded_drawings}"
    return f"{base_url}?symbol={symbol}&interval=1D"

def analyze_stock(symbol):
    data = get_stock_data(symbol)
    if data is None or pd.isna(data['Close']):
        return None
    
    try:
        current_price = round(float(data['Close']), 2)
        
        if data['Open'] == data['High']:  # Bearish
            recommendation = "Sell"
            stop_loss = round(current_price * 1.02, 2)
            target = round(current_price * 0.96, 2)
        elif data['Open'] == data['Low']:  # Bullish
            recommendation = "Buy"
            stop_loss = round(current_price * 0.98, 2)
            target = round(current_price * 1.04, 2)
        else:
            recommendation = "Neutral"
            stop_loss = target = None
        
        tv_url = create_tradingview_url(symbol, current_price, stop_loss, target)
        
        return {
            'Symbol': symbol,
            'Current Price': current_price,
            'Recommendation': recommendation,
            'Stop Loss': stop_loss,
            'Target': target,
            'Condition': "Bearish" if recommendation == "Sell" else "Bullish" if recommendation == "Buy" else "Neutral",
            'Chart Link': tv_url
        }
    except Exception as e:
        st.error(f"Error analyzing {symbol}: {str(e)}")
        return None

def main():
    st.title("NIFTY50 Stock Analyzer with TradingView Charts")
    st.markdown("""
    **Analyzes NIFTY50 stocks based on Open-High/Low conditions**  
    Shows stop loss and target levels directly on TradingView charts
    """)
    
    if st.button("Analyze NIFTY50 Stocks"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, symbol in enumerate(NIFTY50_SYMBOLS):
            status_text.text(f"Processing {symbol} ({i+1}/{len(NIFTY50_SYMBOLS)})")
            result = analyze_stock(symbol)
            if result is not None:
                results.append(result)
            progress_bar.progress((i + 1) / len(NIFTY50_SYMBOLS))
        
        if not results:
            st.warning("Failed to fetch data for all stocks. Please try again later.")
            return
        
        results_df = pd.DataFrame(results)
        actionable_df = results_df[results_df['Recommendation'].isin(['Buy', 'Sell'])]
        
        st.subheader("Actionable Recommendations")
        if not actionable_df.empty:
            for _, row in actionable_df.iterrows():
                with st.expander(f"{row['Symbol']} - {row['Recommendation']}"):
                    if pd.notna(row['Stop Loss']) and pd.notna(row['Target']):
                        sl_pct = abs(row['Stop Loss']-row['Current Price'])/row['Current Price']*100
                        target_pct = abs(row['Target']-row['Current Price'])/row['Current Price']*100
                        
                        st.markdown(f"""
                        - **Current Price**: ₹{row['Current Price']}
                        - **Stop Loss**: ₹{row['Stop Loss']} ({sl_pct:.2f}%)
                        - **Target**: ₹{row['Target']} ({target_pct:.2f}%)
                        - **Condition**: {row['Condition']}
                        - [Open TradingView Chart with Levels]({row['Chart Link']})
                        """)
                    else:
                        st.markdown(f"""
                        - **Current Price**: ₹{row['Current Price']}
                        - **Condition**: {row['Condition']}
                        - [Open TradingView Chart]({row['Chart Link']})
                        """)
            
            st.download_button(
                "Download Recommendations",
                actionable_df.to_csv(index=False),
                "nifty50_recommendations.csv",
                "text/csv"
            )
        else:
            st.info("No strong Buy/Sell signals found today.")
        
        st.subheader("All Stocks Analysis")
        st.dataframe(results_df.drop(columns=['Chart Link']))

if __name__ == "__main__":
    main()
