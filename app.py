from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Piyasa & Deniz Ticareti Paneli",
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
)  # Varsayılan: 10 Yıl
selected_period = period_map[selected_period_label]

interval_choice = st.sidebar.radio(
    "Veri Periyodu", ["Günlük", "Haftalık", "Aylık"], index=0
)
interval_map = {"Günlük": "1d", "Haftalık": "1wk", "Aylık": "1mo"}


# --- VERİ ÇEKME (ÖNBELLEKLİ) ---
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


@st.cache_data(ttl=3600)
def fetch_portwatch_data():
  """IMF PortWatch açık servisinden Süveyş ve Babülmendep verilerini çeker."""
  url = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
  headers = {"User-Agent": "Mozilla/5.0"}
  points = [("Suez", "Süveyş Kanalı"), ("Bab el-Mandeb", "Babülmendep")]
  records = []

  for keyword, label in points:
    params = {
        "where": f"name LIKE '%{keyword}%'",
        "outFields": (
            "date,transit_calls,n_container,n_tanker,n_dry_bulk,n_general_cargo"
        ),
        "orderByFields": "date DESC",
        "resultRecordCount": 3650,  # 10 yıla kadar
        "f": "json",
    }
    try:
      r = requests.get(url, params=params, headers=headers, timeout=15).json()
      for f in r.get("features", []):
        attr = f["attributes"]
        dt = pd.to_datetime(attr.get("date"), unit="ms")
        mapping = {
            "Toplam Gemi": attr.get("transit_calls", 0),
            "Konteyner (Container)": attr.get("n_container", 0),
            "Tanker (Petrol/Kimyasal)": attr.get("n_tanker", 0),
            "Kuru Yük (Dry Bulk)": attr.get("n_dry_bulk", 0),
            "Genel Kargo": attr.get("n_general_cargo", 0),
        }
        for tur, adet in mapping.items():
          if adet is not None:
            records.append({
                "Boğaz": label,
                "Tarih": dt,
                "Yük/Gemi Türü": tur,
                "Geçiş Sayısı": adet,
            })
    except Exception:
      pass
  return pd.DataFrame(records)


# --- ANA EKRAN: PİYASA PANELİ ---
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

  # Değişim Oranı
  if len(df_market) > 1:
    prev_price = df_market["Close"].iloc[-2]
    diff = last_price - prev_price
    pct_change = (diff / prev_price) * 100
  else:
    diff, pct_change = 0, 0

  # Metrik Kartları
  c1, c2, c3, c4 = st.columns(4)
  c1.metric(
      "Son Kapanış Fiyatı",
      f"{last_price:,.2f}",
      f"%{pct_change:.2f}",
      delta_color="normal",
  )
  c2.metric("Periyot En Yüksek", f"{period_high:,.2f}")
  c3.metric("Periyot En Düşük", f"{period_low:,.2f}")
  c4.metric("Veri Sayısı", f"{data_count} Gün")

  # Sekmeler: Çizgi, Mum ve Tablo
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

# --- BÖLÜM 2: IMF PORTWATCH DENİZ TRAFİĞİ & YÜK TÜRLERİ ---
st.divider()
st.header("🚢 IMF PortWatch: Deniz Ticareti ve Boğaz Geçişleri")
st.caption(
    "Süveyş Kanalı ve Babülmendep Boğazı yük ve tanker trafiği analizi (10 Yıla"
    " kadar geçmiş veriler)"
)

df_ships = fetch_portwatch_data()

if not df_ships.empty:
  col_b, col_z, col_t = st.columns(3)
  with col_b:
    sec_bogaz = st.selectbox(
        "📍 Boğaz / Kanal Seçin:", df_ships["Boğaz"].unique(), index=0
    )
  with col_z:
    sec_zaman = st.selectbox(
        "📅 Zaman Dilimi:",
        ["Son 1 Yıl", "Son 3 Yıl", "Son 5 Yıl", "Son 10 Yıl (Tümü)"],
        index=1,
    )
  with col_t:
    sec_turler = st.multiselect(
        "📦 Gemi / Yük Türleri:",
        options=df_ships["Yük/Gemi Türü"].unique(),
        default=[
            "Konteyner (Container)",
            "Tanker (Petrol/Kimyasal)",
            "Kuru Yük (Dry Bulk)",
        ],
    )

  # Zaman Aralığı Filtreleme
  max_date = df_ships["Tarih"].max()
  days_dict = {
      "Son 1 Yıl": 365,
      "Son 3 Yıl": 365 * 3,
      "Son 5 Yıl": 365 * 5,
      "Son 10 Yıl (Tümü)": 365 * 10,
  }
  cutoff = max_date - timedelta(days=days_dict[sec_zaman])

  filtered_ships = df_ships[
      (df_ships["Boğaz"] == sec_bogaz)
      & (df_ships["Tarih"] >= cutoff)
      & (df_ships["Yük/Gemi Türü"].isin(sec_turler))
  ]

  if not filtered_ships.empty:
    fig_ship = px.line(
        filtered_ships,
        x="Tarih",
        y="Geçiş Sayısı",
        color="Yük/Gemi Türü",
        title=f"{sec_bogaz} - {sec_zaman} Gemi ve Yük Geçiş Dağılımı",
    )
    fig_ship.update_layout(
        hovermode="x unified",
        xaxis_title="Tarih",
        yaxis_title="Günlük Gemi Sayısı",
    )
    st.plotly_chart(fig_ship, use_container_width=True)
  else:
    st.info("Seçili filtrelere uygun gemi verisi bulunamadı.")
else:
  st.warning("PortWatch verileri şu anda yüklenemiyor.")
