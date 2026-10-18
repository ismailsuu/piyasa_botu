import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
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
        "marine_mode": "🚢 Deniz Trafiği (IMF PortWatch)",
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
        "marine_title": "🚢 Kritik Boğazlar Deniz Trafiği Analizi",
        "marine_sub": "Veriler IMF PortWatch açık servisinden canlı çekilmektedir.",
        "marine_settings": "⚓ Deniz Trafiği Ayarları",
        "strait": "Boğaz / Geçit",
        "chokepoints": {
            "Süveyş Kanalı": "chokepoint1",
            "Babülmendep Boğazı": "chokepoint2",
            "Hürmüz Boğazı": "chokepoint6",
            "Ümit Burnu": "chokepoint8",
        },
        "time_ranges": ["Son 1 Yıl", "Son 3 Yıl", "Son 5 Yıl", "Tüm Geçmiş (2019 - Günümüz)"],
        "spinner_text": "Tüm veri arşivi yükleniyor...",
        "daily_total": "Son Günlük Toplam",
        "tanker": "Tanker",
        "container": "Konteyner",
        "dry_bulk": "Kuru Yük",
        "tab_total": "📈 Toplam Geçiş Trendi",
        "tab_types": "📊 Gemi Türleri Dağılımı",
        "tab_raw": "📋 Ham Veri",
        "chart_total_title": "Günlük Toplam Gemi Geçişi",
        "chart_types_title": "Gemi Türlerine Göre Trend",
        "daily_calls": "Günlük Geçiş Sayısı",
        "date": "Tarih",
        "type": "Tür",
    },
    "EN": {
        "menu_title": "🧭 Navigation",
        "market_mode": "📈 Financial Markets",
        "marine_mode": "🚢 Maritime Traffic (IMF PortWatch)",
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
        "marine_title": "🚢 Chokepoints Maritime Traffic Analysis",
        "marine_sub": "Live and historical transit data sourced from IMF PortWatch.",
        "marine_settings": "⚓ Maritime Settings",
        "strait": "Chokepoint / Strait",
        "chokepoints": {
            "Suez Canal": "chokepoint1",
            "Bab el-Mandeb Strait": "chokepoint2",
            "Strait of Hormuz": "chokepoint6",
            "Cape of Good Hope": "chokepoint8",
        },
        "time_ranges": ["Last 1 Year", "Last 3 Years", "Last 5 Years", "All History (2019 - Present)"],
        "spinner_text": "Loading historical archive...",
        "daily_total": "Latest Daily Total",
        "tanker": "Tankers",
        "container": "Containers",
        "dry_bulk": "Dry Bulk",
        "tab_total": "📈 Total Transit Trend",
        "tab_types": "📊 Transit Breakdown by Type",
        "tab_raw": "📋 Raw Data",
        "chart_total_title": "Daily Total Vessel Transits",
        "chart_types_title": "Transit Trends by Vessel Type",
        "daily_calls": "Daily Transit Count",
        "date": "Date",
        "type": "Vessel Type",
    },
}

# --- HEM YAN MENÜYE HEM ANA EKRANA DİL SEÇİMİ ---
lang_col1, lang_col2 = st.columns([8, 2])
with lang_col2:
  selected_lang = st.selectbox("🌐 Dil / Language", ["Türkçe 🇹🇷", "English 🇬🇧"], index=0)

lang_code = "TR" if "Türkçe" in selected_lang else "EN"
t = LANG[lang_code]

# --- YAN MENÜ ---
st.sidebar.title(t["menu_title"])
app_mode = st.sidebar.radio(
    "Görünüm / View",
    [t["market_mode"], t["marine_mode"]],
    index=0,
)

# ==========================================
# 1. BÖLÜM: FİNANSAL PİYASALAR
# ==========================================
if app_mode == t["market_mode"]:
  TICKERS = {
      "Bitcoin (BTC)": "BTC-USD",
      "Gold / Altın (Ons)": "GC=F",
      "Silver / Gümüş (Ons)": "SI=F",
      "Brent Crude": "BZ=F",
      "Natural Gas": "NG=F",
      "Cotton / Pamuk (#2)": "CT=F",
      "USD/TRY": "USDTRY=X",
      "US 10Y Yield": "^TNX",
      "USD/CNY": "CNY=X",
  }

  st.sidebar.markdown("---")
  st.sidebar.header(t["market_settings"])
  selected_label = st.sidebar.selectbox(t["instrument"], list(TICKERS.keys()))
  selected_ticker = TICKERS[selected_label]

  raw_period_values = ["1mo", "6mo", "1y", "3y", "5y", "10y", "max"]
  period_display_map = dict(zip(t["periods"], raw_period_values))

  selected_period_label = st.sidebar.selectbox(
      t["timeframe"], t["periods"], index=5
  )
  selected_period = period_display_map[selected_period_label]

  interval_display_map = dict(zip(t["intervals"], ["1d", "1wk", "1mo"]))
  interval_choice = st.sidebar.radio(
      t["data_period"], t["intervals"], index=0
  )

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

  df_market = load_market_data(
      selected_ticker, selected_period, interval_display_map[interval_choice]
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
        t["last_close"],
        f"{last_price:,.2f}",
        f"%{pct_change:.2f}",
        delta_color="normal",
    )
    c2.metric(t["period_high"], f"{period_high:,.2f}")
    c3.metric(t["period_low"], f"{period_low:,.2f}")
    c4.metric(t["data_count"], f"{data_count}")

    tab_line, tab_candle, tab_table = st.tabs(
        [t["tab_line"], t["tab_candle"], t["tab_table"]]
    )

    with tab_line:
      fig_line = px.line(
          df_market,
          x=df_market.index,
          y="Close",
          title=f"{selected_label} - {t['price_trend']}",
      )
      fig_line.update_layout(
          hovermode="x unified", xaxis_title=t["date"], yaxis_title="Price"
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
          title=f"{selected_label} - {t['candle_title']}",
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
    st.warning(f"{selected_label} {t['no_data']}")

# ==========================================
# 2. BÖLÜM: IMF PORTWATCH DENİZ TRAFİĞİ
# ==========================================
else:
  st.title(t["marine_title"])
  st.caption(t["marine_sub"])

  chokepoints_dict = t["chokepoints"]

  st.sidebar.markdown("---")
  st.sidebar.header(t["marine_settings"])
  secilen_bogaz = st.sidebar.selectbox(t["strait"], list(chokepoints_dict.keys()))
  selected_pid = chokepoints_dict[secilen_bogaz]

  secilen_aralik = st.sidebar.radio(
      t["timeframe"],
      t["time_ranges"],
      index=3,
  )

  @st.cache_data(ttl=86400)
  def load_portwatch_history(pid):
    endpoint = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
    headers = {"User-Agent": "Mozilla/5.0"}

    tum_kayitlar = []
    offset = 0

    while True:
      params = {
          "where": f"portid='{pid}'",
          "outFields": "date,n_total,n_tanker,n_container,n_dry_bulk",
          "orderByFields": "date desc",
          "resultOffset": offset,
          "resultRecordCount": 1000,
          "f": "json",
      }
      try:
        r = requests.get(endpoint, params=params, headers=headers, timeout=25)
        if r.status_code == 200:
          data = r.json()
          features = data.get("features", [])
          if not features:
            break
          tum_kayitlar.extend([f["attributes"] for f in features])
          if len(features) < 1000:
            break
          offset += len(features)
        else:
          break
      except Exception:
        break

    if tum_kayitlar:
      df = pd.DataFrame(tum_kayitlar)
      if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        df = df.sort_values("date").reset_index(drop=True)
        return df

    return pd.DataFrame()

  with st.spinner(t["spinner_text"]):
    df_pw = load_portwatch_history(selected_pid)

  if not df_pw.empty:
    bugun = df_pw["date"].max()
    if secilen_aralik == t["time_ranges"][0]:
      df_filtre = df_pw[df_pw["date"] >= bugun - pd.DateOffset(years=1)]
    elif secilen_aralik == t["time_ranges"][1]:
      df_filtre = df_pw[df_pw["date"] >= bugun - pd.DateOffset(years=3)]
    elif secilen_aralik == t["time_ranges"][2]:
      df_filtre = df_pw[df_pw["date"] >= bugun - pd.DateOffset(years=5)]
    else:
      df_filtre = df_pw

    son_gun = df_filtre.iloc[-1]
    g1, g2, g3, g4 = st.columns(4)
    g1.metric(t["daily_total"], f"{int(son_gun.get('n_total', 0))}")
    g2.metric(t["tanker"], f"{int(son_gun.get('n_tanker', 0))}")
    g3.metric(t["container"], f"{int(son_gun.get('n_container', 0))}")
    g4.metric(t["dry_bulk"], f"{int(son_gun.get('n_dry_bulk', 0))}")

    t1, t2, t3 = st.tabs([t["tab_total"], t["tab_types"], t["tab_raw"]])

    with t1:
      fig_trend = px.line(
          df_filtre,
          x="date",
          y="n_total",
          title=f"{secilen_bogaz} - {t['chart_total_title']} ({secilen_aralik})",
          labels={"date": t["date"], "n_total": t["daily_calls"]},
      )
      fig_trend.update_layout(hovermode="x unified")
      st.plotly_chart(fig_trend, use_container_width=True)

    with t2:
      df_filtre_renamed = df_filtre.rename(
          columns={
              "n_tanker": t["tanker"],
              "n_container": t["container"],
              "n_dry_bulk": t["dry_bulk"],
          }
      )
      color_map = {
          t["tanker"]: "#e74c3c",
          t["container"]: "#3498db",
          t["dry_bulk"]: "#f1c40f",
      }

      fig_types = px.line(
          df_filtre_renamed,
          x="date",
          y=[t["tanker"], t["container"], t["dry_bulk"]],
          title=f"{secilen_bogaz} - {t['chart_types_title']} ({secilen_aralik})",
          labels={"date": t["date"], "value": t["daily_calls"], "variable": t["type"]},
          color_discrete_map=color_map,
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
    st.warning(f"{secilen_bogaz} {t['no_data']}")
