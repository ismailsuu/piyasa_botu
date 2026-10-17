import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# Sayfa Yapılandırması
st.set_page_config(
    page_title="10 Yıllık Finansal Gösterge Paneli",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Takip Edilen Enstrümanlar
TICKERS = {
    "Bitcoin (BTC)": "BTC-USD",
    "Altın (Ons)": "GC=F",
    "Gümüş (Ons)": "SI=F",
    "Brent Petrol": "BZ=F",
    "Doğalgaz": "NG=F",
    "Pamuk (#2)": "CT=F",
    "USD/TRY": "USDTRY=X",
    "ABD 10Y Tahvil": "^TNX",
    "USD/CNY": "CNY=X",
}

# --- YAN MENÜ (SIDEBAR) ---
st.sidebar.header("⚙️ Ayarlar ve Filtreler")
selected_label = st.sidebar.selectbox("Enstrüman Seçin", list(TICKERS.keys()))
selected_ticker = TICKERS[selected_label]

period_map = {
    "1 Ay": "1mo",
    "6 Ay": "6mo",
    "1 Yıl": "1y",
    "3 Yıl": "3y",
    "5 Yıl": "5y",
    "10 Yıl": "10y",
    "Tümü (Maks)": "max",
}
selected_period_label = st.sidebar.selectbox(
    "Zaman Dilimi", list(period_map.keys()), index=5
)
selected_period = period_map[selected_period_label]

interval_choice = st.sidebar.radio(
    "Veri Periyodu", ["Günlük", "Haftalık", "Aylık"], index=0
)
interval_map = {"Günlük": "1d", "Haftalık": "1wk", "Aylık": "1mo"}


# --- VERİ ÇEKME ---
@st.cache_data(ttl=1800)
def load_market_data(ticker_symbol, period, interval):
  try:
    t = yf.Ticker(ticker_symbol)
    df = t.history(period=period, interval=interval)
    if not df.empty:
      df.index = pd.to_datetime(df.index)
    return df
  except Exception:
    return pd.DataFrame()


# --- ANA EKRAN ---
st.title("📈 10 Yıllık Finansal Gösterge Paneli")
st.caption(
    "Veriler Yahoo Finance üzerinden canlı ve geçmişe dönük olarak"
    " çekilmektedir."
)

df_market = load_market_data(
    selected_ticker, selected_period, interval_map[interval_choice]
)

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

  # Metrikler
  c1, c2, c3, c4 = st.columns(4)
  c1.metric(
      "Son Kapanış Fiyatı",
      f"{last_price:,.2f}",
      f"%{pct_change:.2f}",
      delta_color="normal",
  )
  c2.metric("Periyot En Yüksek", f"{period_high:,.2f}")
  c3.metric("Periyot En Düşük", f"{period_low:,.2f}")
  c4.metric("Veri Sayısı", f"{data_count} Veri")

  # Sekmeler
  tab_line, tab_candle, tab_table = st.tabs(
      ["📈 Fiyat Grafiği (Çizgi)", "🕯️ Mum Grafik (Detaylı)", "📋 Veri Tablosu"]
  )

  with tab_line:
    fig_line = px.line(
        df_market,
        x=df_market.index,
        y="Close",
        title=f"{selected_label} - Fiyat Trendi",
    )
    fig_line.update_layout(
        hovermode="x unified", xaxis_title="Tarih", yaxis_title="Fiyat"
    )
    st.plotly_chart(fig_line, use_container_width=True)

  with tab_candle:
    fig_candle = go.Figure(
        data=[
            go.Candlestick(
                x=df_market.index,
                open=df_market["Open"],
                high=df_market["High"],
                low=df_market["Low"],
                close=df_market["Close"],
                name="OHLC",
            )
        ]
    )
    fig_candle.update_layout(
        title=f"{selected_label} - Mum Grafiği",
        xaxis_rangeslider_visible=False,
    )
    st.plotly_chart(fig_candle, use_container_width=True)

  with tab_table:
    st.dataframe(
        df_market[["Open", "High", "Low", "Close", "Volume"]].sort_index(
            ascending=False
        ),
        use_container_width=True,
    )
else:
  st.warning(f"{selected_label} için veri alınamadı.")
