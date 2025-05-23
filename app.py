import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# NIFTY50 symbols
NIFTY50_SYMBOLS = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BEL.NS", "BPCL.NS",
    "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS",
    "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS",
    "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS",
    "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SHRIRAMFIN.NS", "SBIN.NS",
    "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "TECHM.NS", "TITAN.NS", "TRENT.NS", "ULTRACEMCO.NS", "WIPRO.NS"
]

def get_stock_data(symbol, days=30):
    try:
        end_date = datetime.today()
        start_date = end_date - timedelta(days=days)
        df = yf.download(symbol, start=start_date, end=end_date)
        return df if not df.empty else None
    except Exception as e:
        st.error(f"Error fetching {symbol}: {str(e)}")
        return None

def analyze_stock(symbol):
    data = get_stock_data(symbol)
    if data is None or data.empty:
        return None
    
    try:
        # Get the last trading day's data
        last_row = data.iloc[-1]
        current_price = round(float(last_row['Close']), 2)
        open_price = float(last_row['Open'])
        high_price = float(last_row['High'])
        low_price = float(last_row['Low'])
        
        # Compare the specific values
        if abs(open_price - high_price) < 0.01:  # Bearish (Open ≈ High)
            recommendation = "Sell"
            stop_loss = round(current_price * 1.02, 2)
            target = round(current_price * 0.96, 2)
        elif abs(open_price - low_price) < 0.01:  # Bullish (Open ≈ Low)
            recommendation = "Buy"
            stop_loss = round(current_price * 0.98, 2)
            target = round(current_price * 1.04, 2)
        else:
            recommendation = "Neutral"
            stop_loss = target = None
        
        return {
            'Symbol': symbol.replace(".NS", ""),
            'Current Price': current_price,
            'Recommendation': recommendation,
            'Stop Loss': stop_loss,
            'Target': target,
            'Condition': "Bearish" if recommendation == "Sell" else "Bullish" if recommendation == "Buy" else "Neutral",
            'Chart Data': data
        }
    except Exception as e:
        st.error(f"Error analyzing {symbol}: {str(e)}")
        return None

def plot_stock_chart(data, current_price, stop_loss, target, symbol):
    fig = go.Figure()
    
    # Add candlestick
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price'
    ))
    
    # Add current price line
    fig.add_hline(y=current_price, line_dash="solid", 
                 line_color="blue", annotation_text=f"Current: {current_price}")
    
    # Add stop loss line if available
    if stop_loss is not None:
        fig.add_hline(y=stop_loss, line_dash="dash", 
                     line_color="red", annotation_text=f"SL: {stop_loss}")
    
    # Add target line if available
    if target is not None:
        fig.add_hline(y=target, line_dash="dash", 
                     line_color="green", annotation_text=f"Target: {target}")
    
    # Update layout
    fig.update_layout(
        title=f"{symbol} - Last 30 Days",
        xaxis_title="Date",
        yaxis_title="Price (₹)",
        showlegend=False,
        height=600,
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("NIFTY50 Stock Analyzer")
    st.markdown("""
    **Analyzes NIFTY50 stocks based on Open-High/Low conditions**  
    Shows stop loss and target levels on interactive charts
    """)
    
    if st.button("Analyze NIFTY50 Stocks"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, symbol in enumerate(NIFTY50_SYMBOLS):
            status_text.text(f"Processing {symbol} ({i+1}/{len(NIFTY50_SYMBOLS)})")
            result = analyze_stock(symbol)
            if result:
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
                        """)
                    
                    # Show the interactive chart
                    plot_stock_chart(
                        row['Chart Data'],
                        row['Current Price'],
                        row['Stop Loss'],
                        row['Target'],
                        row['Symbol']
                    )
            
            st.download_button(
                "Download Recommendations",
                actionable_df.drop(columns=['Chart Data']).to_csv(index=False),
                "nifty50_recommendations.csv",
                "text/csv"
            )
        else:
            st.info("No strong Buy/Sell signals found today.")
        
        st.subheader("All Stocks Analysis")
        st.dataframe(results_df.drop(columns=['Chart Data']))

if __name__ == "__main__":
    main()
