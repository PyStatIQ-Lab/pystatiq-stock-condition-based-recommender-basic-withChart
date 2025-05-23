import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# NIFTY50 symbols with NSE: prefix
NIFTY50_SYMBOLS = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BEL", "BPCL",
    "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DRREDDY",
    "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE",
    "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", "ITC",
    "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LT",
    "M&M", "MARUTI", "NTPC", "NESTLEIND", "ONGC",
    "POWERGRID", "RELIANCE", "SBILIFE", "SHRIRAMFIN", "SBIN",
    "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS", "TATASTEEL",
    "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO"
]

def get_stock_data(symbol, period='1d'):
    try:
        stock = yf.Ticker(symbol + ".NS")
        hist = stock.history(period=period)
        return hist.iloc[-1] if not hist.empty else None
    except Exception as e:
        st.error(f"Error fetching {symbol}: {str(e)}")
        return None

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
        
        return {
            'Symbol': f"NSE:{symbol}",
            'Current Price': current_price,
            'Recommendation': recommendation,
            'Stop Loss': stop_loss,
            'Target': target,
            'Condition': "Bearish" if recommendation == "Sell" else "Bullish" if recommendation == "Buy" else "Neutral"
        }
    except Exception as e:
        st.error(f"Error analyzing {symbol}: {str(e)}")
        return None

def show_tradingview_chart(symbol, current_price, stop_loss, target):
    chart_html = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_{symbol}"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget(
          {{
            "autosize": true,
            "symbol": "NSE:{symbol.replace('NSE:', '')}",
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": "light",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "hide_side_toolbar": false,
            "allow_symbol_change": true,
            "studies": [],
            "container_id": "tradingview_{symbol}"
          }}
        );
        
        // Wait for chart to load
        setTimeout(function() {{
          var widget = document.getElementById('tradingview_{symbol}').querySelector('iframe').contentWindow;
          
          // Add horizontal lines
          widget.postMessage({{
            'name': 'drawing',
            'action': 'create',
            'tool': 'HorizontalLine',
            'points': [{{'time': 0, 'price': {current_price}}}],
            'options': {{
              'color': '#2962FF',
              'linestyle': 0,
              'linewidth': 1,
              'axisLabelVisible': true,
              'title': 'Current: {current_price}'
            }}
          }}, '*');
          {f"""
          widget.postMessage({{
            'name': 'drawing',
            'action': 'create',
            'tool': 'HorizontalLine',
            'points': [{{'time': 0, 'price': {stop_loss}}}],
            'options': {{
              'color': '#F44336',
              'linestyle': 1,
              'linewidth': 2,
              'axisLabelVisible': true,
              'title': 'SL: {stop_loss}'
            }}
          }}, '*');
          """ if stop_loss else ""}
          {f"""
          widget.postMessage({{
            'name': 'drawing',
            'action': 'create',
            'tool': 'HorizontalLine',
            'points': [{{'time': 0, 'price': {target}}}],
            'options': {{
              'color': '#4CAF50',
              'linestyle': 1,
              'linewidth': 2,
              'axisLabelVisible': true,
              'title': 'Target: {target}'
            }}
          }}, '*');
          """ if target else ""}
        }}, 2000);
      </script>
    </div>
    """
    st.components.v1.html(chart_html, height=500)

def main():
    st.title("NIFTY50 Stock Analyzer with TradingView Charts")
    st.markdown("""
    **Analyzes NIFTY50 stocks based on Open-High/Low conditions**  
    Shows stop loss and target levels directly on interactive charts
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
                    show_tradingview_chart(
                        row['Symbol'].replace("NSE:", ""),
                        row['Current Price'],
                        row['Stop Loss'],
                        row['Target']
                    )
            
            st.download_button(
                "Download Recommendations",
                actionable_df.to_csv(index=False),
                "nifty50_recommendations.csv",
                "text/csv"
            )
        else:
            st.info("No strong Buy/Sell signals found today.")
        
        st.subheader("All Stocks Analysis")
        st.dataframe(results_df)

if __name__ == "__main__":
    main()
