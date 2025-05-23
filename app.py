import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
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

# Function to fetch stock data
def get_stock_data(symbol, period='1d'):
    try:
        # Remove NSE: prefix for yfinance
        yfinance_symbol = symbol.replace("NSE:", "") + ".NS"
        stock = yf.Ticker(yfinance_symbol)
        hist = stock.history(period=period)
        if hist.empty:
            return None
        return hist.iloc[-1]
    except:
        return None

# Function to generate TradingView chart URL with drawings
def get_tradingview_url(symbol, current_price, stop_loss, target, recommendation):
    base_url = "https://www.tradingview.com/chart/"
    
    # Create drawings for stop loss and target
    drawings = []
    
    if stop_loss is not None:
        sl_color = "#FF0000"  # Red for stop loss
        sl_drawing = {
            "points": [{"time": "0", "price": stop_loss}],
            "styles": {"color": sl_color, "linestyle": 2, "linewidth": 2},
            "text": f"SL: {stop_loss}",
            "type": "horizontal_line"
        }
        drawings.append(sl_drawing)
    
    if target is not None:
        target_color = "#00FF00"  # Green for target
        target_drawing = {
            "points": [{"time": "0", "price": target}],
            "styles": {"color": target_color, "linestyle": 2, "linewidth": 2},
            "text": f"Target: {target}",
            "type": "horizontal_line"
        }
        drawings.append(target_drawing)
    
    # Create current price line
    current_color = "#0000FF"  # Blue for current price
    current_drawing = {
        "points": [{"time": "0", "price": current_price}],
        "styles": {"color": current_color, "linestyle": 0, "linewidth": 1},
        "text": f"Current: {current_price}",
        "type": "horizontal_line"
    }
    drawings.append(current_drawing)
    
    # URL encode the drawings
    drawings_json = urllib.parse.quote(str(drawings).replace("'", '"'))
    
    return f"{base_url}?symbol={symbol}&drawings={drawings_json}"

# Function to analyze stock condition
def analyze_stock(symbol):
    data = get_stock_data(symbol)
    if data is None:
        return None
    
    current_price = round(data['Close'], 2)
    
    # Calculate stop loss and target (simple percentage-based)
    if data['Open'] == data['High']:  # Bearish condition
        recommendation = "Sell"
        stop_loss = round(current_price * 1.02, 2)  # 2% above current price
        target = round(current_price * 0.96, 2)     # 4% below current price
    elif data['Open'] == data['Low']:  # Bullish condition
        recommendation = "Buy"
        stop_loss = round(current_price * 0.98, 2)  # 2% below current price
        target = round(current_price * 1.04, 2)     # 4% above current price
    else:
        recommendation = "Neutral"
        stop_loss = None
        target = None
    
    # Generate TradingView URL with drawings
    tv_url = get_tradingview_url(symbol, current_price, stop_loss, target, recommendation)
    
    return {
        'Symbol': symbol,
        'Current Price': current_price,
        'Open': round(data['Open'], 2),
        'High': round(data['High'], 2),
        'Low': round(data['Low'], 2),
        'Close': current_price,
        'Recommendation': recommendation,
        'Stop Loss': stop_loss,
        'Target': target,
        'Condition': "Open=High (Bearish)" if data['Open'] == data['High'] else 
                    "Open=Low (Bullish)" if data['Open'] == data['Low'] else "No clear pattern",
        'TradingView Chart': tv_url
    }

# Main Streamlit app
def main():
    st.title("NIFTY50 Stock Condition-Based Recommender")
    st.write("Analyzes NIFTY50 stocks based on Open-High/Low conditions and provides recommendations with TradingView charts")
    
    # User inputs
    analyze_button = st.button("Analyze NIFTY50 Stocks")
    
    if analyze_button:
        try:
            symbols = NIFTY50_SYMBOLS
            
            # Analyze each stock
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, symbol in enumerate(symbols):
                status_text.text(f"Analyzing {symbol} ({i+1}/{len(symbols)})...")
                result = analyze_stock(symbol)
                if result is not None:
                    results.append(result)
                progress_bar.progress((i + 1) / len(symbols))
            
            if not results:
                st.warning("No valid stock data could be fetched. Please try again later.")
                return
            
            # Create results dataframe
            results_df = pd.DataFrame(results)
            
            # Filter only Buy/Sell recommendations
            actionable_df = results_df[results_df['Recommendation'].isin(['Buy', 'Sell'])]
            
            # Display results
            st.subheader("All Analyzed NIFTY50 Stocks")
            st.dataframe(results_df.drop(columns=['TradingView Chart']))
            
            st.subheader("Actionable Recommendations (Buy/Sell)")
            if not actionable_df.empty:
                # Display actionable recommendations with chart links
                for _, row in actionable_df.iterrows():
                    st.markdown(f"### {row['Symbol']} - {row['Recommendation']}")
                    st.markdown(f"""
                    - **Current Price**: {row['Current Price']}
                    - **Stop Loss**: {row['Stop Loss']}
                    - **Target**: {row['Target']}
                    - **Condition**: {row['Condition']}
                    - [Open TradingView Chart with Levels]({row['TradingView Chart']})
                    """)
                    st.write("---")
                
                # Download buttons
                st.download_button(
                    label="Download All Results as CSV",
                    data=results_df.to_csv(index=False).encode('utf-8'),
                    file_name=f'nifty50_recommendations_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime='text/csv'
                )
                
                st.download_button(
                    label="Download Actionable Recommendations as CSV",
                    data=actionable_df.to_csv(index=False).encode('utf-8'),
                    file_name=f'nifty50_actionable_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime='text/csv'
                )
            else:
                st.info("No strong Buy/Sell recommendations today based on the criteria.")
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
