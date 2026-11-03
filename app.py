import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Dashboard | Gösterge Paneli",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# DİL SÖZLÜĞÜ (TR / EN)
# ==========================================
LANG = {
    "TR": {
        "menu_title": "🧭 Menü",
        "market_mode": "📈 Finansal Piyasalar",
        "market_settings": "⚙️ Piyasa Ayarları",
        "instrument": "Enstrüman Seçin",
        "timeframe": "Zaman Dilimi",
        "data_period": "Veri Periyodu",
        "intervals": ["Günlük", "Haftalık", "Aylık"],
        "periods": ["1 Ay", "6 Ay", "1 Yıl", "3 Yıl", "5 Yıl", "10 Yıl", "Tümü (Maks)"],
        "market_title": "📈 Finansal Gösterge Paneli",
        "market_sub": "Veriler Yahoo Finance üzerinden canlı ve geçmişe dönük olarak çekilmektedir.",
        "last_close": "Son Kapanış Fiyatı",
        "period_high": "Periyot En Yüksek",
        "period_low": "Periyot En Düşük",
        "data_count": "Veri Sayısı",
        "tab_line": "📈 Fiyat Grafiği (Çizgi)",
        "tab_candle": "🕯️ Mum Grafik (Detaylı)",
        "tab_table": "📋 Veri Tablosu",
        "price_trend": "Fiyat Trendi",
        "candle_title": "Mum Grafiği",
        "no_data": "için veri alınamadı.",
        "date": "Tarih",
    },
    "EN": {
        "menu_title": "🧭 Navigation",
        "market_mode": "📈 Financial Markets",
        "market_settings": "⚙️ Market Settings",
        "instrument": "Select Instrument",
        "timeframe": "Timeframe",
        "data_period": "Data Frequency",
        "intervals": ["Daily", "Weekly", "Monthly"],
        "periods": ["1 Month", "6 Months", "1 Year", "3 Years", "5 Years", "10 Years", "All (Max)"],
        "market_title": "📈 Financial Dashboard",
        "market_sub": "Live and historical market data powered by Yahoo Finance.",
        "last_close": "Last Close Price",
        "period_high": "Period High",
        "period_low": "Period Low",
        "data_count": "Data Points",
        "tab_line": "📈 Line Chart",
        "tab_candle": "🕯️ Candlestick Chart",
        "tab_table": "📋 Data Table",
        "price_trend": "Price Trend",
        "candle_title": "Candlestick Chart",
        "no_data": "No data found for",
        "date": "Date",
    },
}

# --- DİL SEÇİMİ ---
lang_col1, lang_col2 = st.columns([8, 2])
with lang_col2:
    selected_lang = st.selectbox("🌐 Dil / Language", ["Türkçe 🇹🇷", "English 🇬🇧"], index=0)

lang_code = "TR" if "Türkçe" in selected_lang else "EN"
t = LANG[lang_code]

TICKERS = {
    "Bitcoin (BTC)": "BTC-USD",
    "Altın / Gold (Ons)": "GC=F",
    "Gümüş / Silver (Ons)": "SI=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Cotton / Pamuk (#2)": "CT=F",
    "USD/TRY": "USDTRY=X",
    "US 10Y Yield": "^TNX",
    "USD/CNY": "CNY=X",
}

st.sidebar.title(t["menu_title"])
st.sidebar.markdown("---")
st.sidebar.header(t["market_settings"])
selected_label = st.sidebar.selectbox(t["instrument"], list(TICKERS.keys()))
selected_ticker = TICKERS[selected_label]

raw_period_values = ["1mo", "6mo", "1y", "3y", "5y", "10y", "max"]
period_display_map = dict(zip(t["periods"], raw_period_values))

selected_period_label = st.sidebar.selectbox(t["timeframe"], t["periods"], index=5)
selected_period = period_display_map[selected_period_label]

interval_display_map = dict(zip(t["intervals"], ["1d", "1wk", "1mo"]))
interval_choice = st.sidebar.radio(t["data_period"], t["intervals"], index=0)

@st.cache_data(ttl=1800)
def load_market_data(ticker_symbol, period, interval):
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period=period, interval=interval)
        if not df.empty:
            df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return pd.DataFrame()

st.title(t["market_title"])
st.caption(t["market_sub"])

df_market = load_market_data(selected_ticker, selected_period, interval_display_map[interval_choice])

if not df_market.empty:
    last_price = df_market["Close"].iloc[-1]
    period_high = df_market["High"].max()
    period_low = df_market["Low"].min()
    data_count = len(df_market)

    if len(df_market) > 1:
        prev_price = df_market["Close"].iloc[-2]
        pct_change = ((last_price - prev_price) / prev_price) * 100
    else:
        pct_change = 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t["last_close"], f"{last_price:,.2f}", f"%{pct_change:.2f}", delta_color="normal")
    c2.metric(t["period_high"], f"{period_high:,.2f}")
    c3.metric(t["period_low"], f"{period_low:,.2f}")
    c4.metric(t["data_count"], f"{data_count}")

    tab_line, tab_candle, tab_table = st.tabs([t["tab_line"], t["tab_candle"], t["tab_table"]])

    with tab_line:
        fig_line = px.line(df_market, x=df_market.index, y="Close", title=f"{selected_label} - {t['price_trend']}")
        fig_line.update_layout(hovermode="x unified", xaxis_title=t["date"], yaxis_title="Price")
        st.plotly_chart(fig_line, use_container_width=True)

    with tab_candle:
        fig_candle = go.Figure(data=[go.Candlestick(x=df_market.index, open=df_market["Open"], high=df_market["High"], low=df_market["Low"], close=df_market["Close"], name="OHLC")])
        fig_candle.update_layout(title=f"{selected_label} - {t['candle_title']}", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig_candle, use_container_width=True)

    with tab_table:
        st.dataframe(df_market[["Open", "High", "Low", "Close", "Volume"]].sort_index(ascending=False), use_container_width=True)
else:
    st.warning(f"{selected_label} {t['no_data']}")
