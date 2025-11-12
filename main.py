import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import os
import datetime
from groq import Groq  # Add this import for Groq API

# ---------------------- CUSTOM CSS FOR ULTIMATE BEAUTY ----------------------
st.markdown("""
    <style>
    /* Global styles - Elegant, modern theme with gradients and shadows */
    .stApp {
        background: linear-gradient(to bottom right, #e6f0ff, #f0f4f8);
        color: #1e1e1e;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Button styling - Vibrant, hover effects */
    .stButton > button {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #45a049, #4CAF50);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    /* Selectbox and multiselect - Clean, with subtle borders */
    .stSelectbox > div, .stMultiselect > div {
        background-color: #ffffff;
        border: 1px solid #d1d1d1;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* Header - Bold, centered with shadow */
    h1 {
        color: #007BFF;
        text-align: center;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    /* Caption - Elegant footer */
    .stCaption {
        text-align: center;
        color: #666666;
        font-style: italic;
    }
    /* Treemap - Enhanced hover and borders */
    .modebar {
        background-color: rgba(255,255,255,0.9) !important;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Pie chart - Smooth animations */
    .js-plotly-plot .plotly .modebar {
        left: 50%;
        transform: translateX(-50%);
    }
    /* Expander - Card-like with subtle gradient */
    .stExpander {
        background: linear-gradient(to bottom, #ffffff, #f9f9f9);
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .stExpander:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    /* Spinner - Custom color */
    .stSpinner {
        color: #007BFF;
    }
    /* Divider - Stylish */
    hr {
        border: 0;
        height: 1px;
        background: linear-gradient(to right, transparent, #d1d1d1, transparent);
    }
    /* Add subtle animations for inputs */
    input, select {
        transition: border-color 0.3s ease;
    }
    input:focus, select:focus {
        border-color: #007BFF !important;
    }
    /* Market details styling */
    .market-details {
        background: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)


# ---------------------- CACHING ----------------------
@st.cache_data(ttl=86400)
def get_sector_map_from_nse_total_market():
    url = "https://nsearchives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv"
    try:
        df_map = pd.read_csv(url)
        # Create dict: { Symbol : Industry }
        return df_map.set_index("Symbol")["Industry"].to_dict()
    except Exception as e:
        st.error(f"Failed to load sector data: {e}")
        return {}


import yfinance as yf
import streamlit as st
import pandas as pd


@st.cache_data(ttl=86400)  # Cache data for 24 hours
def get_sector_data_yfinance(symbols):

    sector_map = {}
    total = len(symbols)
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, symbol in enumerate(symbols):
        try:
            # Fetch ticker information
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Extract sector if available
            if 'sector' in info and info['sector']:
                sector_map[symbol] = info['sector']
            else:
                # If sector is not found, you can assign a default value
                sector_map[symbol] = "Unknown"

            # Update progress
            status_text.info(f"Fetching sector for {symbol}... ({i + 1}/{total})")
            progress_bar.progress((i + 1) / total)

        except Exception as e:
            # Handle cases where a symbol might be delisted or invalid
            status_text.warning(f"Could not retrieve data for {symbol}. Skipping. Error: {e}")
            continue

    progress_bar.empty()
    return sector_map


@st.cache_data(ttl=300)
def get_index_details(category):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        "Accept": "application/json,text/html",
        'Accept-Language': 'en-US,en;q=0.9'
    }
    category = category.upper().replace('&', '%26').replace(' ', '%20')
    try:
        session = requests.Session()
        session.headers.update(headers)
        ref_url = f"https://www.nseindia.com/market-data/live-equity-market?symbol={category}"
        session.get(ref_url, timeout=5)  # warm-up
        url = f"https://www.nseindia.com/api/equity-stockIndices?index={category}"
        data = session.get(url, timeout=5).json()
        df = pd.DataFrame(data['data'])
        if not df.empty:
            if "meta" in df.columns:
                df = df.drop(["meta"], axis=1)
            df = df.set_index("symbol", drop=True)
            df['ffmc'] = round(df['ffmc'] / 10000000, 0)
            df = df.iloc[1:].reset_index(drop=False)
            df['yf_symbol'] = df['symbol'] + '.NS'
        return df
    except Exception:
        return pd.DataFrame()


# ---------------------- NEW: GROQ API INTEGRATION ----------------------
@st.cache_data(ttl=300)
def get_market_details_groq(index_name, df_summary):

    groq_api_key = st.secrets.get("GROQ_API_KEY")

    # Check if the key was found. If not, show an error and stop.
    if not groq_api_key:
        st.error("Groq API key not configured. Please add it to your .streamlit/secrets.toml file.")
        st.stop()

    client = Groq(api_key=groq_api_key)

    prompt = f"""
            Summarize today’s performance of the {index_name} index on NSE using this data. The summary should be below 70 words:
            {df_summary}

            In 4 simple lines, highlight:
            1) Overall index trend (average % change & volatility).
            2) Market cap distribution impact.
            3) Sector performance if discernible.
            4) Notable sentiment or market observations.
            Keep it concise, neutral, and data-driven. Do not say "Here's your summary" or include any pre-text.
        """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error generating AI insights: {str(e)}"


# ---------------------- NEW: TOTAL MARKET INSIGHTS ----------------------
@st.cache_data(ttl=300)
def get_total_market_insights(df):
    insights = {}

    insights['Total Market Cap (Cr)'] = df['ffmc'].sum()
    insights['Number of Stocks'] = len(df)
    insights['Volatility (Std Dev of pChange)'] = round(df['pChange'].std(), 2)
    advances = len(df[df['pChange'] > 0])
    declines = len(df[df['pChange'] < 0])

    if 'yf_symbol' in df.columns:
        symbols = df['yf_symbol']
    else:
        symbols = df['symbol'].apply(lambda x: str(x) + '.NS')

    pe_ratios = []
    pb_ratios = []
    div_yields = []
    betas = []
    for symbol in symbols:
        try:
            info = yf.Ticker(symbol).info
            pe = info.get('trailingPE')
            pb = info.get('priceToBook')
            div_yld = info.get('dividendYield')
            beta = info.get('beta')
            if pe: pe_ratios.append(pe)
            if pb: pb_ratios.append(pb)
            if div_yld: div_yields.append(div_yld * 100)  # Convert to %
            if beta: betas.append(beta)
        except Exception:
            continue

    insights['Average P/E'] = round(sum(pe_ratios) / len(pe_ratios), 2) if pe_ratios else 'N/A'
    insights['Average Dividend Yield (%)'] = round(sum(div_yields) / len(div_yields), 2) if div_yields else 'N/A'

    top_gainers = df.nlargest(5, 'pChange')[['symbol', 'pChange']]
    top_losers = df.nsmallest(5, 'pChange')[['symbol', 'pChange']]

    return insights, top_gainers, top_losers


# ---------------------- CONFIG ----------------------
index_list = ['NIFTY TOTAL MARKET', 'NIFTY 50', 'NIFTY NEXT 50', 'NIFTY MIDCAP 50', 'NIFTY MIDCAP 100',
              'NIFTY MIDCAP 150',
              'NIFTY SMALLCAP 50', 'NIFTY SMALLCAP 100', 'NIFTY SMALLCAP 250', 'NIFTY MIDSMALLCAP 400',
              'NIFTY 100', 'NIFTY 200', 'NIFTY AUTO', 'NIFTY BANK', 'NIFTY ENERGY',
              'NIFTY FINANCIAL SERVICES', 'NIFTY FINANCIAL SERVICES 25/50', 'NIFTY FMCG', 'NIFTY IT',
              'NIFTY MEDIA', 'NIFTY METAL', 'NIFTY PHARMA', 'NIFTY PSU BANK', 'NIFTY REALTY',
              'NIFTY PRIVATE BANK', 'NIFTY DIVIDEND OPPORTUNITIES 50', 'NIFTY50 VALUE 20',
              'NIFTY100 QUALITY 30', 'NIFTY50 EQUAL WEIGHT', 'NIFTY100 EQUAL WEIGHT',
              'NIFTY100 LOW VOLATILITY 30', 'NIFTY ALPHA 50', 'NIFTY200 QUALITY 30',
              'NIFTY ALPHA LOW-VOLATILITY 30', 'NIFTY200 MOMENTUM 30', 'NIFTY COMMODITIES',
              'NIFTY INDIA CONSUMPTION', 'NIFTY CPSE', 'NIFTY INFRASTRUCTURE', 'NIFTY MNC',
              'NIFTY GROWTH SECTORS 15', 'NIFTY PSE', 'NIFTY SERVICES SECTOR', 'NIFTY100 LIQUID 15',
              'NIFTY MIDCAP LIQUID 15']

st.set_page_config(page_title='NSE Indices Heatmap Dashboard', layout="wide")
st_autorefresh(interval=300000, key="auto_refresh")


# ---------------------- TREEMAP FUNCTION ----------------------
def build_treemap(df, slice_factor, color_scale, height=900):
    """Reusable treemap for both single and multi index modes"""
    fig = px.treemap(
        df,
        path=['sector', 'symbol'],  # Nested hierarchy
        values=slice_factor,  # Box size
        color='pChange',  # Box color
        color_continuous_scale=color_scale,
        custom_data=['pChange', 'ffmc', 'sector']
    )

    fig.update_layout(
        margin=dict(t=30, l=0, r=0, b=0),
        height=height,
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
    )

    fig.update_traces(
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Sector: %{customdata[2]}<br>'
            'Size: %{value}<br>'
            'Market Cap: %{customdata[1]:,.0f} Cr<br>'
            'pChange: %{customdata[0]:.2f}%'
        ),
        texttemplate='%{label}<br>%{customdata[0]:.2f}%',
        textposition='middle center',
        textinfo="label+text",
        marker=dict(cornerradius=8, line=dict(width=2, color='#ffffff'))  # Enhanced borders and rounding
    )

    fig.update_coloraxes(showscale=False)
    return fig


# ---------------------- PIE CHART FUNCTION ----------------------
def build_pie_chart(df):
    advances = df[df['pChange'] > 0].shape[0]
    declines = df[df['pChange'] < 0].shape[0]
    no_change = df[df['pChange'] == 0].shape[0]

    fig = px.pie(
        names=['Advances', 'Declines', 'No Change'],
        values=[advances, declines, no_change],
        color=['Advances', 'Declines', 'No Change'],
        color_discrete_sequence=['#3AA864', '#F38039', '#F2F2F2']
    )
    fig.update_traces(hole=0.7, textinfo='none', marker=dict(line=dict(color='#ffffff', width=2)))
    fig.update_layout(
        width=150, height=150, showlegend=False,
        annotations=[dict(
            text=f'Positive: {advances}<br>Negative: {declines}<br>',
            x=0.5, y=0.5, font_size=12, showarrow=False, font_color='#333333'
        )],
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig


# ---------------------- UI ----------------------
st.title("📊 NSE Indices Heatmap Dashboard")

# Display current date and time with style
st.markdown(
    f"<div style='text-align: center; color: #007BFF; font-weight: bold; margin-bottom: 20px;'>Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST</div>",
    unsafe_allow_html=True)

# Global filters in an expander at the top
with st.expander("⚙ Settings", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        mode = st.radio("View Mode", ["Single Index", "Multi Index Comparison"], horizontal=True,
                        help="Choose between detailed single index view or side-by-side comparisons.")
    with col2:
        slice_by = st.selectbox("Slice By", ["Market Cap", "Gainers", "Losers"], index=0,
                                help="Determine how treemap boxes are sized and filtered.")

    st.caption("Auto-refreshes every 5 minutes for live data. 💹")

# ---------------------- SINGLE INDEX MODE ----------------------
if mode == "Single Index":
    with st.expander("Single Index Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            index_filter = st.selectbox("Choose Index", index_list, index=0, help="Select an NSE index to visualize.")
        with col2:
            search_query = st.text_input("🔍 Search Stock Symbol", "",
                                         help="Filter stocks by symbol (case-insensitive).")
        with col3:
            sort_by = st.selectbox("Sort By", [
                "pChange (High to Low)", "pChange (Low to High)",
                "ffmc (High to Low)", "ffmc (Low to High)"
            ], help="Sort the data before rendering the treemap.")

    # Fetch and process data with spinner
    with st.spinner("Fetching latest index data... 🌟"):
        df = get_index_details(index_filter)

    if not df.empty:
        # Load or fetch sector data
        if os.path.exists("sector_map.csv"):
            sector_map = pd.read_csv("sector_map.csv", index_col=0).to_dict()["sector"]
        else:
            with st.spinner("Gathering sector insights... 📈"):
                sector_map = get_sector_data_yfinance(df['yf_symbol'].tolist())
            pd.DataFrame.from_dict(sector_map, orient="index", columns=["sector"]).to_csv("sector_map.csv")

        df['sector'] = df['yf_symbol'].map(sector_map)
        df.dropna(subset=['sector'], inplace=True)
        df.drop('yf_symbol', axis=1, inplace=True)

        # Filter by search query if provided
        if search_query:
            df = df[df['symbol'].str.contains(search_query.upper())]

        # Slice logic
        if slice_by == 'Market Cap':
            slice_factor = 'ffmc'
            color_scale = px.colors.diverging.RdYlGn
        elif slice_by == 'Gainers':
            df = df[df["pChange"] > 0].copy()
            slice_factor = 'pChange'
            color_scale = ['white', '#a5eb79']
        elif slice_by == 'Losers':
            df = df[df["pChange"] < 0].copy()
            df['Abs'] = df['pChange'].abs()
            slice_factor = 'Abs'
            color_scale = ['#ff7a3a', 'white']

        # Sorting
        if sort_by == "pChange (High to Low)":
            df = df.sort_values(by="pChange", ascending=False)
        elif sort_by == "pChange (Low to High)":
            df = df.sort_values(by="pChange", ascending=True)
        elif sort_by == "ffmc (High to Low)":
            df = df.sort_values(by="ffmc", ascending=False)
        elif sort_by == "ffmc (Low to High)":
            df = df.sort_values(by="ffmc", ascending=True)

        # Layout with pie chart on the right
        header1, header2 = st.columns([3, 1])
        with header1:
            fig = build_treemap(df, slice_factor, color_scale, height=625)
            st.plotly_chart(fig, use_container_width=True)
        with header2:
            st.subheader("Advance/Decline Ratio :")
            pie_fig = build_pie_chart(df)
            st.plotly_chart(pie_fig, use_container_width=True)

            df_summary = df.describe().to_string()  # Simple summary of DataFrame stats
            market_details = get_market_details_groq(index_filter, df_summary)
            st.markdown(
                f'<div class="market-details"><b>Market Insights (Powered by Groq AI):</b><br>{market_details}</div>',
                unsafe_allow_html=True)

        # New: Total Market Insights (if selected) - Moved below both columns
        if index_filter == 'NIFTY TOTAL MARKET':
            st.subheader("Total Market Overview ")
            with st.spinner("Computing total market insights... 📊"):
                insights, top_gainers, top_losers = get_total_market_insights(df)

            # Display key aggregates in a table
            st.markdown("*Key Aggregates*")
            aggregate_df = pd.DataFrame(list(insights.items()), columns=['Metric', 'Value'])
            st.table(aggregate_df)

            # Top Gainers/Losers Tables
            col_g, col_l = st.columns(2)
            with col_g:
                st.markdown("*Top 5 Gainers*")
                st.dataframe(top_gainers)
            with col_l:
                st.markdown("*Top 5 Losers*")
                st.dataframe(top_losers)

        # Expander for data table and download
        with st.expander("📋 View Raw Data", expanded=False):
            st.dataframe(df.style.background_gradient(cmap='viridis', subset=['pChange']), use_container_width=True)
            st.download_button("📥 Download as CSV", df.to_csv(index=False), "index_data.csv", "text/csv",
                               help="Download the filtered data as a CSV file.")
    else:
        st.error("⚠ Failed to fetch data for the selected index. Please try another or check your connection.")

# ---------------------- MULTI INDEX MODE ----------------------
else:
    with st.expander("Multi Index Filters", expanded=True):
        selected_indices = st.multiselect("Select up to 3 Indices", index_list, default=["NIFTY 50", "NIFTY BANK"],
                                          max_selections=3, help="Choose 1-3 indices for side-by-side comparison.")

    if selected_indices:
        cols = st.columns(len(selected_indices))
        for i, idx in enumerate(selected_indices):
            with cols[i]:
                st.subheader(idx)
                with st.spinner(f"Fetching {idx} data... 🌟"):
                    df = get_index_details(idx)

                if not df.empty:
                    # --- CORRECTED: Using the more reliable yfinance function ---
                    with st.spinner(f"Gathering sector insights for {idx}... 📈"):
                        # This ensures consistency with the single-index mode's fallback
                        sector_map = get_sector_data_yfinance(df['yf_symbol'].tolist())

                    df['sector'] = df['yf_symbol'].map(sector_map).fillna("Unknown")
                    # --- END OF CORRECTION ---

                    # Determine slice factor and color scale
                    if slice_by == 'Market Cap':
                        slice_factor = 'ffmc'
                        color_scale = px.colors.diverging.RdYlGn
                    elif slice_by == 'Gainers':
                        df = df[df["pChange"] > 0].copy()
                        slice_factor = 'pChange'
                        color_scale = ['white', '#a5eb79']
                    elif slice_by == 'Losers':
                        df = df[df["pChange"] < 0].copy()
                        df['Abs'] = df['pChange'].abs()
                        slice_factor = 'Abs'
                        color_scale = ['#ff7a3a', 'white']

                    # Ensure dataframe is not empty after filtering
                    if not df.empty:
                        fig = build_treemap(df, slice_factor, color_scale, height=625)
                        st.plotly_chart(fig, use_container_width=True)

                        # Add pie chart below each treemap
                        pie_fig = build_pie_chart(df)
                        st.plotly_chart(pie_fig, use_container_width=True)

                        # Get market details from Groq AI
                        df_summary = df.describe().to_string()
                        market_details = get_market_details_groq(idx, df_summary)
                        st.markdown(
                            f'<div class="market-details"><b>Market Insights (Powered by Groq AI):</b><br>{market_details}</div>',
                            unsafe_allow_html=True)
                    else:
                        st.warning(f"No data to display for '{slice_by}' in {idx}.")
                else:
                    st.error(f"⚠ No data for {idx}. Try another index.")
    else:
        st.info("Please select at least one index to compare. ✨")

st.markdown("---")
st.caption("Made with ❤ by M.Chandra Sekhara Sri Sai | Data sourced from NSE India and Yahoo Finance")
