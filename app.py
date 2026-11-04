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
        "marine_sub": "Veriler IMF PortWatch resmi veri tabanından derlenmektedir.",
        "marine_settings": "⚓ Deniz Trafiği Ayarları",
        "strait": "Boğaz / Geçit",
        "chokepoints": {
            "İstanbul Boğazı": ["chokepoint3", "bosporus"],
            "Süveyş Kanalı": ["chokepoint1", "suez"],
            "Babülmendep Boğazı": ["chokepoint4", "mandeb"],
            "Hürmüz Boğazı": ["chokepoint6", "hormuz"],
            "Ümit Burnu": ["chokepoint7", "good hope", "cape"],
            "Malakka Boğazı": ["chokepoint5", "malacca"],
            "Panama Kanalı": ["chokepoint2", "panama"],
            "Cebelitarık Boğazı": ["chokepoint8", "gibraltar"],
        },
        "spinner_text": "Veriler yükleniyor...",
        "total_transit": "Toplam Gemi Geçişi",
        "tanker": "Tanker",
        "container": "Konteyner",
        "dry_bulk": "Kuru Yük",
        "general_cargo": "Genel Kargo",
        "roro": "Ro-Ro",
        "tab_types": "📊 Gemi Türleri Dağılımı",
        "tab_compare": "🌍 Küresel Boğazlar Sıralaması",
        "tab_industries": "📦 Taşınan Kritik Sektörler",
        "tab_raw": "📋 Veri Tablosu",
        "chart_types_title": "Gemi Türü Dağılımı (Oransal)",
        "chart_compare_title": "Dünya Çapında 28 Kritik Boğazın Trafik Karşılaştırması",
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
            "Bosporus Strait": ["chokepoint3", "bosporus"],
            "Suez Canal": ["chokepoint1", "suez"],
            "Bab el-Mandeb Strait": ["chokepoint4", "mandeb"],
            "Strait of Hormuz": ["chokepoint6", "hormuz"],
            "Cape of Good Hope": ["chokepoint7", "good hope", "cape"],
            "Malacca Strait": ["chokepoint5", "malacca"],
            "Panama Canal": ["chokepoint2", "panama"],
            "Gibraltar Strait": ["chokepoint8", "gibraltar"],
        },
        "spinner_text": "Loading data...",
        "total_transit": "Total Vessel Transits",
        "tanker": "Tankers",
        "container": "Containers",
        "dry_bulk": "Dry Bulk",
        "general_cargo": "General Cargo",
        "roro": "Ro-Ro",
        "tab_types": "📊 Transit Breakdown by Type",
        "tab_compare": "🌍 Global Chokepoints Ranking",
        "tab_industries": "📦 Top Traded Commodities",
        "tab_raw": "📋 Raw Data",
        "chart_types_title": "Transit Share by Vessel Type",
        "chart_compare_title": "Global Comparison of 28 Maritime Chokepoints",
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
        
        # Yerel dosya bulunamazsa internet kaynaklarını dene
        fallback_urls = [
            "https://hub.arcgis.com/api/v3/datasets/3da2b9ca97684916b75c4013f95d18ab_0/downloads/data?format=csv",
            "https://portwatch.imf.org/api/v3/datasets/3da2b9ca97684916b75c4013f95d18ab_0/downloads/data?format=csv"
        ]
        headers = {"User-Agent": "Mozilla/5.0"}
        for url in fallback_urls:
            try:
                r = requests.get(url, headers=headers, timeout=20)
                if r.status_code == 200:
                    df = pd.read_csv(io.StringIO(r.text))
                    if not df.empty:
                        return df
            except Exception:
                continue
        return pd.DataFrame()

    with st.spinner(t["spinner_text"]):
        df_pw = load_portwatch_data()

    if not df_pw.empty:
        # Sütun isimlerini normalize et
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

            # Gemi sayılarını al
            toplam = to_int(row.get("vessel_count_total", row.get("n_total", 0)))
            tanker = to_int(row.get("vessel_count_tanker", row.get("n_tanker", 0)))
            konteyner = to_int(row.get("vessel_count_container", row.get("n_container", 0)))
            kuru_yuk = to_int(row.get("vessel_count_dry_bulk", row.get("n_dry_bulk", 0)))
            genel_kargo = to_int(row.get("vessel_count_general_cargo", row.get("n_general_cargo", 0)))
            roro = to_int(row.get("vessel_count_RoRo", row.get("n_roro", 0)))

            # Üst Metrik Kartları
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t["total_transit"], f"{toplam:,}")
            m2.metric(t["tanker"], f"{tanker:,}")
            m3.metric(t["container"], f"{konteyner:,}")
            m4.metric(t["dry_bulk"], f"{kuru_yuk:,}")

            tab_types, tab_compare, tab_industries, tab_raw = st.tabs([
                t["tab_types"], t["tab_compare"], t["tab_industries"], t["tab_raw"]
            ])

            # TAB 1: Gemi Türleri Dağılımı (Donut Grafiği)
            with tab_types:
                breakdown_data = pd.DataFrame({
                    t["type"]: [t["tanker"], t["container"], t["dry_bulk"], t["general_cargo"], t["roro"]],
                    t["count"]: [tanker, konteyner, kuru_yuk, genel_kargo, roro]
                })
                breakdown_data = breakdown_data[breakdown_data[t["count"]] > 0]

                fig_donut = px.pie(
                    breakdown_data,
                    names=t["type"],
                    values=t["count"],
                    hole=0.45,
                    title=f"{secilen_bogaz} - {t['chart_types_title']}",
                    color=t["type"],
                    color_discrete_map={
                        t["tanker"]: "#e74c3c",
                        t["container"]: "#3498db",
                        t["dry_bulk"]: "#f1c40f",
                        t["general_cargo"]: "#9b59b6",
                        t["roro"]: "#1abc9c",
                    }
                )
                fig_donut.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_donut, use_container_width=True)

            # TAB 2: Dünyadaki Tüm Boğazların Karşılaştırması
            with tab_compare:
                if "vessel_count_total" in df_pw.columns and name_col in df_pw.columns:
                    df_sorted = df_pw[[name_col, "vessel_count_total"]].copy().dropna()
                    df_sorted["vessel_count_total"] = pd.to_numeric(df_sorted["vessel_count_total"], errors="coerce")
                    df_sorted = df_sorted.sort_values(by="vessel_count_total", ascending=True)

                    fig_bar = px.bar(
                        df_sorted,
                        x="vessel_count_total",
                        y=name_col,
                        orientation="h",
                        title=t["chart_compare_title"],
                        labels={"vessel_count_total": t["total_transit"], name_col: t["strait"]},
                        color="vessel_count_total",
                        color_continuous_scale="Blues"
                    )
                    fig_bar.update_layout(height=700)
                    st.plotly_chart(fig_bar, use_container_width=True)

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

            # TAB 4: Ham Veri
            with tab_raw:
                st.dataframe(df_pw, use_container_width=True)
    else:
        st.warning("PortWatch veri tabanı bulunamadı. Lütfen CSV dosyasının repo dizininde olduğundan emin olun.")
