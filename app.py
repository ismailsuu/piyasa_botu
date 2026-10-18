import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Finans ve Deniz Trafiği Gösterge Paneli",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- YAN MENÜ: ANA MOD SEÇİMİ ---
st.sidebar.title("🧭 Menü")
app_mode = st.sidebar.radio(
    "Görünüm Seçin",
    ["📈 Finansal Piyasalar", "🚢 Deniz Trafiği (IMF PortWatch)"],
    index=0,
)

# ==========================================
# 1. BÖLÜM: FİNANSAL PİYASALAR
# ==========================================
if app_mode == "📈 Finansal Piyasalar":
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

  st.sidebar.markdown("---")
  st.sidebar.header("⚙️ Piyasa Ayarları")
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

# ==========================================
# 2. BÖLÜM: IMF PORTWATCH DENİZ TRAFİĞİ
# ==========================================
else:
  st.title("🚢 Kritik Boğazlar Deniz Trafiği Analizi")
  st.caption("Veriler IMF PortWatch açık servisinden canlı çekilmektedir.")

  CHOKEPOINTS = {
      "Süveyş Kanalı": "chokepoint1",
      "Babülmendep Boğazı": "chokepoint2",
      "Hürmüz Boğazı": "chokepoint6",
      "Ümit Burnu": "chokepoint8",
  }

  st.sidebar.markdown("---")
  st.sidebar.header("⚓ Deniz Trafiği Ayarları")
  secilen_bogaz = st.sidebar.selectbox("Boğaz / Geçit", list(CHOKEPOINTS.keys()))
  selected_pid = CHOKEPOINTS[secilen_bogaz]

  secilen_aralik = st.sidebar.radio(
      "Zaman Aralığı",
      ["Son 1 Yıl", "Son 3 Yıl", "Son 5 Yıl", "Tümü (Tüm Geçmiş)"],
      index=1,
  )

  @st.cache_data(ttl=86400)
  def load_portwatch_history(pid):
    endpoint = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
    headers = {"User-Agent": "Mozilla/5.0"}

    tum_kayitlar = []
    offset = 0
    limit = 2000

    while True:
      params = {
          "where": f"portid='{pid}'",
          "outFields": "date,n_total,n_tanker,n_container,n_dry_bulk",
          "orderByFields": "date asc",
          "resultOffset": offset,
          "resultRecordCount": limit,
          "f": "json",
      }
      try:
        r = requests.get(endpoint, params=params, headers=headers, timeout=20)
        if r.status_code == 200:
          features = r.json().get("features", [])
          if not features:
            break
          tum_kayitlar.extend([f["attributes"] for f in features])
          if len(features) < limit:
            break
          offset += limit
        else:
          break
      except Exception as e:
        print("PortWatch API Hatası:", e)
        break

    if tum_kayitlar:
      df = pd.DataFrame(tum_kayitlar)
      if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        df = df.sort_values("date").reset_index(drop=True)
        return df

    return pd.DataFrame()

  with st.spinner("Tarihsel gemi verileri yükleniyor..."):
    df_pw = load_portwatch_history(selected_pid)

  if not df_pw.empty:
    bugun = df_pw["date"].max()
    if secilen_aralik == "Son 1 Yıl":
      df_filtre = df_pw[df_pw["date"] >= bugun - pd.DateOffset(years=1)]
    elif secilen_aralik == "Son 3 Yıl":
      df_filtre = df_pw[df_pw["date"] >= bugun - pd.DateOffset(years=3)]
    elif secilen_aralik == "Son 5 Yıl":
      df_filtre = df_pw[df_pw["date"] >= bugun - pd.DateOffset(years=5)]
    else:
      df_filtre = df_pw

    son_gun = df_filtre.iloc[-1]
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Son Günlük Toplam", f"{int(son_gun.get('n_total', 0))} Gemi")
    g2.metric("Tanker", f"{int(son_gun.get('n_tanker', 0))}")
    g3.metric("Konteyner", f"{int(son_gun.get('n_container', 0))}")
    g4.metric("Kuru Yük", f"{int(son_gun.get('n_dry_bulk', 0))}")

    t1, t2, t3 = st.tabs(
        ["📈 Toplam Geçiş Trendi", "📊 Gemi Türleri Dağılımı", "📋 Ham Veri"]
    )

    with t1:
      fig_trend = px.line(
          df_filtre,
          x="date",
          y="n_total",
          title=f"{secilen_bogaz} - Günlük Toplam Gemi Geçişi ({secilen_aralik})",
          labels={"date": "Tarih", "n_total": "Günlük Geçiş Sayısı"},
      )
      fig_trend.update_layout(hovermode="x unified")
      st.plotly_chart(fig_trend, use_container_width=True)

    with t2:
      fig_types = px.line(
          df_filtre,
          x="date",
          y=["n_tanker", "n_container", "n_dry_bulk"],
          title=f"{secilen_bogaz} - Gemi Türlerine Göre Trend",
          labels={"date": "Tarih", "value": "Geçiş Sayısı", "variable": "Tür"},
          color_discrete_map={
              "n_tanker": "#e74c3c",
              "n_container": "#3498db",
              "n_dry_bulk": "#f1c40f",
          },
      )
      fig_types.update_layout(hovermode="x unified")
      st.plotly_chart(fig_types, use_container_width=True)

    with t3:
      st.dataframe(
          df_filtre[[
              "date",
              "n_total",
              "n_tanker",
              "n_container",
              "n_dry_bulk",
          ]].sort_values("date", ascending=False),
          use_container_width=True,
      )
  else:
    st.warning(f"{secilen_bogaz} için geçmiş veri alınamadı.")
