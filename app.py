import io
import os
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
        "no_data": "için veri bulunamadı.",
        "marine_title": "🚢 Kritik Boğazlar Deniz Trafiği Analizi",
        "marine_sub": "Veriler IMF PortWatch veri tabanından derlenmektedir.",
        "marine_settings": "⚓ Deniz Trafiği Ayarları",
        "strait": "Boğaz / Geçit",
        "chokepoints": {
            "Süveyş Kanalı": ["chokepoint1", "suez"],
            "Hürmüz Boğazı": ["chokepoint6", "hormuz"],
            "Ümit Burnu": ["chokepoint7", "good hope", "cape"],
        },
        "spinner_text": "Veriler yükleniyor...",
        "total_transit": "Toplam Gemi Geçişi",
        "tanker": "Tanker",
        "container": "Konteyner",
        "dry_bulk": "Kuru Yük",
        "general_cargo": "Genel Kargo",
        "roro": "Ro-Ro",
        "tab_line_breakdown": "📈 Gemi Türleri Dağılımı (Çizgi Grafik)",
        "tab_compare_line": "📊 3 Boğaz Karşılaştırma Grafiği",
        "tab_industries": "📦 Taşınan Kritik Sektörler",
        "tab_raw": "📋 Veri Tablosu",
        "chart_line_title": "Gemi Türlerine Göre Geçiş Sayıları",
        "chart_compare_title": "Süveyş, Hürmüz ve Ümit Burnu Karşılaştırmalı Geçiş Trendi",
        "date": "Tarih",
        "type": "Gemi Türü",
        "count": "Geçiş Sayısı",
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
        "marine_sub": "Sourced from IMF PortWatch official database.",
        "marine_settings": "⚓ Maritime Settings",
        "strait": "Chokepoint / Strait",
        "chokepoints": {
            "Suez Canal": ["chokepoint1", "suez"],
            "Strait of Hormuz": ["chokepoint6", "hormuz"],
            "Cape of Good Hope": ["chokepoint7", "good hope", "cape"],
        },
        "spinner_text": "Loading data...",
        "total_transit": "Total Vessel Transits",
        "tanker": "Tankers",
        "container": "Containers",
        "dry_bulk": "Dry Bulk",
        "general_cargo": "General Cargo",
        "roro": "Ro-Ro",
        "tab_line_breakdown": "📈 Vessel Types Breakdown (Line Chart)",
        "tab_compare_line": "📊 3 Chokepoints Comparison (Line Chart)",
        "tab_industries": "📦 Top Traded Commodities",
        "tab_raw": "📋 Raw Data",
        "chart_line_title": "Transit Calls by Vessel Category",
        "chart_compare_title": "Suez, Hormuz & Cape of Good Hope Comparison",
        "date": "Date",
        "type": "Vessel Type",
        "count": "Transit Count",
    },
}

# --- DİL SEÇİMİ ---
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
        "Altın / Gold (Ons)": "GC=F",
        "Gümüş / Silver (Ons)": "SI=F",
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
    selected_pid_list = chokepoints_dict[secilen_bogaz]

    @st.cache_data(ttl=3600)
    def load_portwatch_data():
        csv_file = "PortWatch_chokepoints_database.csv"
        if os.path.exists(csv_file):
            return pd.read_csv(csv_file)
        return pd.DataFrame()

    with st.spinner(t["spinner_text"]):
        df_pw = load_portwatch_data()

    if not df_pw.empty:
        df_pw.columns = [str(c).strip() for c in df_pw.columns]

        id_col = "portid" if "portid" in df_pw.columns else "portname"
        name_col = "portname" if "portname" in df_pw.columns else id_col

        # Seçilen boğazı bul
        mask = df_pw[id_col].astype(str).str.lower().apply(lambda x: any(pid in x for pid in selected_pid_list)) | \
               df_pw[name_col].astype(str).str.lower().apply(lambda x: any(pid in x for pid in selected_pid_list))
        
        selected_row = df_pw[mask]

        if selected_row.empty:
            st.warning(f"{secilen_bogaz} {t['no_data']}")
        else:
            row = selected_row.iloc[0]

            def to_int(val):
                try:
                    return int(float(val))
                except Exception:
                    return 0

            toplam = to_int(row.get("vessel_count_total", 0))
            tanker = to_int(row.get("vessel_count_tanker", 0))
            konteyner = to_int(row.get("vessel_count_container", 0))
            kuru_yuk = to_int(row.get("vessel_count_dry_bulk", 0))
            genel_kargo = to_int(row.get("vessel_count_general_cargo", 0))
            roro = to_int(row.get("vessel_count_RoRo", 0))

            # Üst Metrik Kartları
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t["total_transit"], f"{toplam:,}")
            m2.metric(t["tanker"], f"{tanker:,}")
            m3.metric(t["container"], f"{konteyner:,}")
            m4.metric(t["dry_bulk"], f"{kuru_yuk:,}")

            tab_line_breakdown, tab_compare_line, tab_industries, tab_raw = st.tabs([
                t["tab_line_breakdown"], t["tab_compare_line"], t["tab_industries"], t["tab_raw"]
            ])

            # TAB 1: Seçilen Boğazın Gemi Türleri Dağılımı (Klasik Çizgi Grafik)
            with tab_line_breakdown:
                category_data = pd.DataFrame({
                    t["type"]: [t["tanker"], t["container"], t["dry_bulk"], t["general_cargo"], t["roro"]],
                    t["count"]: [tanker, konteyner, kuru_yuk, genel_kargo, roro]
                })

                fig_line = px.line(
                    category_data,
                    x=t["type"],
                    y=t["count"],
                    markers=True,
                    text=t["count"],
                    title=f"{secilen_bogaz} - {t['chart_line_title']}",
                )
                fig_line.update_traces(
                    line=dict(color="#1f77b4", width=3),
                    marker=dict(size=10, color="#d62728"),
                    textposition="top center"
                )
                fig_line.update_layout(
                    hovermode="x unified",
                    xaxis_title=t["type"],
                    yaxis_title=t["count"]
                )
                st.plotly_chart(fig_line, use_container_width=True)

            # TAB 2: Süveyş, Hürmüz ve Ümit Burnu Karşılaştırmalı Çizgi Grafiği
            with tab_compare_line:
                target_3_pids = ["chokepoint1", "chokepoint6", "chokepoint7"]
                df_3 = df_pw[df_pw[id_col].isin(target_3_pids)].copy()

                name_mapping = {
                    "chokepoint1": "Süveyş Kanalı (Suez)",
                    "chokepoint6": "Hürmüz Boğazı (Hormuz)",
                    "chokepoint7": "Ümit Burnu (Good Hope)"
                }
                df_3["Bogaz"] = df_3[id_col].map(name_mapping)

                compare_rows = []
                for _, r_3 in df_3.iterrows():
                    b_name = r_3["Bogaz"]
                    compare_rows.append({"Boğaz": b_name, t["type"]: t["tanker"], t["count"]: to_int(r_3.get("vessel_count_tanker", 0))})
                    compare_rows.append({"Boğaz": b_name, t["type"]: t["container"], t["count"]: to_int(r_3.get("vessel_count_container", 0))})
                    compare_rows.append({"Boğaz": b_name, t["type"]: t["dry_bulk"], t["count"]: to_int(r_3.get("vessel_count_dry_bulk", 0))})
                    compare_rows.append({"Boğaz": b_name, t["type"]: t["general_cargo"], t["count"]: to_int(r_3.get("vessel_count_general_cargo", 0))})
                    compare_rows.append({"Boğaz": b_name, t["type"]: t["roro"], t["count"]: to_int(r_3.get("vessel_count_RoRo", 0))})

                df_compare_plot = pd.DataFrame(compare_rows)

                fig_multi_line = px.line(
                    df_compare_plot,
                    x=t["type"],
                    y=t["count"],
                    color="Boğaz",
                    markers=True,
                    title=t["chart_compare_title"],
                    color_discrete_map={
                        "Süveyş Kanalı (Suez)": "#2ca02c",
                        "Hürmüz Boğazı (Hormuz)": "#d62728",
                        "Ümit Burnu (Good Hope)": "#1f77b4"
                    }
                )
                fig_multi_line.update_traces(line=dict(width=3), marker=dict(size=9))
                fig_multi_line.update_layout(
                    hovermode="x unified",
                    xaxis_title=t["type"],
                    yaxis_title=t["count"]
                )
                st.plotly_chart(fig_multi_line, use_container_width=True)

            # TAB 3: Taşınan Sektörler & Kritik Emtialar
            with tab_industries:
                st.subheader(f"⚓ {secilen_bogaz} - {t['tab_industries']}")
                ind1 = row.get("industry_top1", "-")
                ind2 = row.get("industry_top2", "-")
                ind3 = row.get("industry_top3", "-")

                col_i1, col_i2, col_i3 = st.columns(3)
                col_i1.info(f"🥇 **1. Sektör / Commodity:**\n\n### {ind1}")
                col_i2.info(f"🥈 **2. Sektör / Commodity:**\n\n### {ind2}")
                col_i3.info(f"🥉 **3. Sektör / Commodity:**\n\n### {ind3}")

            # TAB 4: Ham Veri (Yalnızca 3 Boğaz)
            with tab_raw:
                df_filtered_3 = df_pw[df_pw[id_col].isin(["chokepoint1", "chokepoint6", "chokepoint7"])]
                st.dataframe(df_filtered_3, use_container_width=True)
    else:
        st.warning("PortWatch veri tabanı bulunamadı. Lütfen CSV dosyasının repo dizininde olduğundan emin olun.")
