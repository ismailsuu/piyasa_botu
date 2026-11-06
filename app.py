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
        "periods": ["10 Yıl", "5 Yıl", "3 Yıl"],
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
        "marine_sub": "Veriler IMF PortWatch veri tabanından zaman serisi olarak derlenmektedir.",
        "marine_settings": "⚓ Deniz Trafiği Ayarları",
        "strait": "Boğaz / Geçit",
        "chokepoints": {
            "Süveyş Kanalı": ["chokepoint1", "suez"],
            "Hürmüz Boğazı": ["chokepoint6", "hormuz"],
            "Ümit Burnu": ["chokepoint7", "good hope", "cape"],
        },
        "spinner_text": "Veriler yükleniyor...",
        "last_transit": "Son Geçiş Sayısı",
        "tab_marine_trend": "📈 Geçiş Trendi (Çizgi)",
        "tab_marine_breakdown": "📊 Gemi Türleri Trendi",
        "tab_compare_line": "🌐 3 Boğaz Karşılaştırma",
        "tab_raw": "📋 Veri Tablosu",
        "transit_trend": "Geçiş Trendi",
        "date": "Tarih",
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
        "periods": ["10 Years", "5 Years", "3 Years"],
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
        "marine_sub": "Sourced from IMF PortWatch official time-series database.",
        "marine_settings": "⚓ Maritime Settings",
        "strait": "Chokepoint / Strait",
        "chokepoints": {
            "Suez Canal": ["chokepoint1", "suez"],
            "Strait of Hormuz": ["chokepoint6", "hormuz"],
            "Cape of Good Hope": ["chokepoint7", "good hope", "cape"],
        },
        "spinner_text": "Loading data...",
        "last_transit": "Last Transit Count",
        "tab_marine_trend": "📈 Transit Trend (Line)",
        "tab_marine_breakdown": "📊 Vessel Breakdown Trend",
        "tab_compare_line": "🌐 3 Chokepoints Comparison",
        "tab_raw": "📋 Data Table",
        "transit_trend": "Transit Trend",
        "date": "Date",
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

# Sadece 10, 5 ve 3 yıl seçenekleri
raw_period_values = ["10y", "5y", "3y"]
period_display_map = dict(zip(t["periods"], raw_period_values))

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

    selected_period_label = st.sidebar.selectbox(t["timeframe"], t["periods"], index=0)
    selected_period_key = period_display_map[selected_period_label]

    interval_display_map = dict(zip(t["intervals"], ["1d", "1wk", "1mo"]))
    interval_choice = st.sidebar.radio(t["data_period"], t["intervals"], index=0)

    @st.cache_data(ttl=1800)
    def load_market_data(ticker_symbol, interval):
        try:
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period="max", interval=interval)
            if not df.empty:
                df.index = pd.to_datetime(df.index)
            return df
        except Exception:
            return pd.DataFrame()

    st.title(t["market_title"])
    st.caption(t["market_sub"])

    df_full = load_market_data(selected_ticker, interval_display_map[interval_choice])

    if not df_full.empty:
        df_market = df_full.copy()
        year_offsets = {"3y": 3, "5y": 5, "10y": 10}

        if selected_period_key in year_offsets:
            years = year_offsets[selected_period_key]
            latest_date = df_market.index[-1]
            earliest_date = df_market.index[0]
            target_start = latest_date - pd.DateOffset(years=years)
            effective_start = max(earliest_date, target_start)
            df_market = df_market.loc[df_market.index >= effective_start]

        last_price = df_market["Close"].iloc[-1]
        period_high = df_market["High"].max()
        period_low = df_market["Low"].min()
        data_count = len(df_market)

        prev_price = df_market["Close"].iloc[-2] if len(df_market) > 1 else last_price
        pct_change = ((last_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t["last_close"], f"{last_price:,.2f}", f"%{pct_change:.2f}")
        c2.metric(t["period_high"], f"{period_high:,.2f}")
        c3.metric(t["period_low"], f"{period_low:,.2f}")
        c4.metric(t["data_count"], f"{data_count}")

        tab_line, tab_candle, tab_table = st.tabs([t["tab_line"], t["tab_candle"], t["tab_table"]])

        with tab_line:
            fig_line = go.Figure()
            fig_line.add_trace(
                go.Scatter(
                    x=df_market.index,
                    y=df_market["Close"],
                    mode="lines",
                    line=dict(color="#0052cc", width=2),
                    name="Price",
                    hovertemplate="%{x|%Y-%m-%d}<br>Price: %{y:,.2f}<extra></extra>"
                )
            )
            fig_line.update_layout(
                title=dict(text=f"<b>{selected_label} - {t['price_trend']}</b>", font=dict(size=16, color="#1e293b")),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                hovermode="x unified",
                xaxis=dict(
                    title=dict(text=t["date"], font=dict(color="#64748b", size=12)),
                    showgrid=False,
                    showline=False,
                    type="date",
                    dtick="M12",          # Yıllık işaretler
                    tickformat="%Y",      # Sadece yıl (2018, 2019...)
                    tickfont=dict(color="#64748b", size=11),
                ),
                yaxis=dict(
                    title=dict(text="Price", font=dict(color="#64748b", size=12)),
                    showgrid=True,
                    gridcolor="#e2e8f0",
                    gridwidth=1,
                    showline=False,
                    tickformat="~s",      # Finans tarafında 20k, 40k
                    tickfont=dict(color="#64748b", size=11),
                ),
                margin=dict(l=40, r=20, t=50, b=40),
            )
            st.plotly_chart(fig_line, use_container_width=True)

        with tab_candle:
            fig_candle = go.Figure(
                data=[go.Candlestick(x=df_market.index, open=df_market["Open"], high=df_market["High"], low=df_market["Low"], close=df_market["Close"])]
            )
            fig_candle.update_layout(title=f"{selected_label} - {t['candle_title']}", xaxis_rangeslider_visible=False, plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
            st.plotly_chart(fig_candle, use_container_width=True)

        with tab_table:
            st.dataframe(df_market[["Open", "High", "Low", "Close", "Volume"]].sort_index(ascending=False), use_container_width=True)
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

    # Yalnızca 10, 5 ve 3 yıl
    selected_period_label = st.sidebar.selectbox(t["timeframe"], t["periods"], index=0)
    selected_period_key = period_display_map[selected_period_label]

    interval_choice = st.sidebar.radio(t["data_period"], t["intervals"], index=0)

    @st.cache_data(ttl=3600)
    def load_portwatch_data():
        csv_file = "PortWatch_chokepoints_database.csv"
        if os.path.exists(csv_file):
            return pd.read_csv(csv_file)
        return pd.DataFrame()

    with st.spinner(t["spinner_text"]):
        df_pw = load_portwatch_data()

    if not df_pw.empty:
        df_pw.columns = [str(c).strip().lower() for c in df_pw.columns]

        id_col = "portid" if "portid" in df_pw.columns else "portname"
        name_col = "portname" if "portname" in df_pw.columns else id_col

        mask = df_pw[id_col].astype(str).str.lower().apply(lambda x: any(pid in x for pid in selected_pid_list)) | \
               df_pw[name_col].astype(str).str.lower().apply(lambda x: any(pid in x for pid in selected_pid_list))
        
        df_strait = df_pw[mask].copy()

        if df_strait.empty:
            st.warning(f"{secilen_bogaz} {t['no_data']}")
        else:
            date_col = next((c for c in df_strait.columns if c in ["date", "tarih", "datetime", "time"]), None)
            
            if date_col:
                df_strait[date_col] = pd.to_datetime(df_strait[date_col])
                df_strait = df_strait.sort_values(by=date_col).set_index(date_col)
            else:
                df_strait.index = pd.date_range(end=pd.Timestamp.now(), periods=len(df_strait), freq="D")

            # 10, 5, 3 yıl filtreleme
            year_offsets = {"3y": 3, "5y": 5, "10y": 10}
            if selected_period_key in year_offsets:
                years = year_offsets[selected_period_key]
                latest_date = df_strait.index[-1]
                earliest_date = df_strait.index[0]
                target_start = latest_date - pd.DateOffset(years=years)
                effective_start = max(earliest_date, target_start)
                df_strait = df_strait.loc[df_strait.index >= effective_start]

            target_metric_col = "vessel_count_total" if "vessel_count_total" in df_strait.columns else df_strait.select_dtypes(include="number").columns[0]
            df_strait[target_metric_col] = pd.to_numeric(df_strait[target_metric_col], errors="coerce").fillna(0)

            # Periyoda göre toplama
            if interval_choice == t["intervals"][1]:
                df_plot = df_strait[[target_metric_col]].resample("W").sum()
            elif interval_choice == t["intervals"][2]:
                df_plot = df_strait[[target_metric_col]].resample("ME").sum()
            else:
                df_plot = df_strait[[target_metric_col]].resample("D").sum()

            df_plot = df_plot.dropna()

            last_val = df_plot[target_metric_col].iloc[-1]
            prev_val = df_plot[target_metric_col].iloc[-2] if len(df_plot) > 1 else last_val
            pct_change = ((last_val - prev_val) / prev_val) * 100 if prev_val != 0 else 0
            p_high = df_plot[target_metric_col].max()
            p_low = df_plot[target_metric_col].min()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t["last_transit"], f"{int(last_val):,}", f"%{pct_change:.2f}")
            m2.metric(t["period_high"], f"{int(p_high):,}")
            m3.metric(t["period_low"], f"{int(p_low):,}")
            m4.metric(t["data_count"], f"{len(df_plot)}")

            tab_marine_trend, tab_marine_breakdown, tab_compare_line, tab_raw = st.tabs([
                t["tab_marine_trend"], t["tab_marine_breakdown"], t["tab_compare_line"], t["tab_raw"]
            ])

            # ÇİZGİ GRAFİK: Y ekseni düz tam sayı (20, 80...), X ekseni sadece Yıl (2018, 2019...)
            with tab_marine_trend:
                fig_marine = go.Figure()
                fig_marine.add_trace(
                    go.Scatter(
                        x=df_plot.index,
                        y=df_plot[target_metric_col],
                        mode="lines",
                        line=dict(color="#0052cc", width=2),
                        name=t["count"],
                        hovertemplate="%{x|%Y-%m-%d}<br>Geçiş Sayısı: %{y:,.0f}<extra></extra>"
                    )
                )

                fig_marine.update_layout(
                    title=dict(
                        text=f"<b>{secilen_bogaz} - {t['transit_trend']}</b>",
                        font=dict(size=16, color="#1e293b", family="sans-serif")
                    ),
                    plot_bgcolor="#FFFFFF",
                    paper_bgcolor="#FFFFFF",
                    hovermode="x unified",
                    xaxis=dict(
                        title=dict(text=t["date"], font=dict(color="#64748b", size=12)),
                        showgrid=False,
                        showline=False,
                        type="date",
                        dtick="M12",          # Yıllık aralıklar
                        tickformat="%Y",      # Sadece yıl gösterimi (2018, 2019...)
                        tickfont=dict(color="#64748b", size=11),
                    ),
                    yaxis=dict(
                        title=dict(text=t["count"], font=dict(color="#64748b", size=12)),
                        showgrid=True,
                        gridcolor="#e2e8f0",
                        gridwidth=1,
                        showline=False,
                        tickformat="d",       # 'k' yok, düz tam sayı (20, 80 vb.)
                        tickfont=dict(color="#64748b", size=11),
                    ),
                    margin=dict(l=40, r=20, t=50, b=40),
                )
                st.plotly_chart(fig_marine, use_container_width=True)

            with tab_marine_breakdown:
                sub_cols = [c for c in ["vessel_count_tanker", "vessel_count_container", "vessel_count_dry_bulk", "vessel_count_general_cargo", "vessel_count_roro"] if c in df_strait.columns]
                if sub_cols:
                    df_sub = df_strait[sub_cols].apply(pd.to_numeric, errors="coerce").resample("ME" if interval_choice == t["intervals"][2] else "W").sum()
                    fig_sub = px.line(df_sub, x=df_sub.index, y=sub_cols, title=f"{secilen_bogaz} - Gemi Türleri Dağılım Trendi")
                    fig_sub.update_layout(
                        plot_bgcolor="#FFFFFF", 
                        paper_bgcolor="#FFFFFF", 
                        hovermode="x unified",
                        xaxis=dict(type="date", dtick="M12", tickformat="%Y"),
                        yaxis=dict(tickformat="d")
                    )
                    st.plotly_chart(fig_sub, use_container_width=True)
                else:
                    st.info("Alt gemi türü kırılım verisi bulunamadı.")

            with tab_compare_line:
                st.subheader(t["tab_compare_line"])
                target_3_pids = ["chokepoint1", "chokepoint6", "chokepoint7"]
                df_3 = df_pw[df_pw[id_col].isin(target_3_pids)].copy()
                if not df_3.empty and date_col:
                    df_3[date_col] = pd.to_datetime(df_3[date_col])
                    df_3_pivot = df_3.pivot_table(index=date_col, columns=name_col, values=target_metric_col, aggfunc="sum").resample("W").sum()
                    fig_3 = px.line(df_3_pivot, x=df_3_pivot.index, y=df_3_pivot.columns, title="Süveyş, Hürmüz ve Ümit Burnu Geçiş Karşılaştırması")
                    fig_3.update_layout(
                        plot_bgcolor="#FFFFFF", 
                        paper_bgcolor="#FFFFFF", 
                        hovermode="x unified",
                        xaxis=dict(type="date", dtick="M12", tickformat="%Y"),
                        yaxis=dict(tickformat="d")
                    )
                    st.plotly_chart(fig_3, use_container_width=True)

            with tab_raw:
                st.dataframe(df_strait.sort_index(ascending=False), use_container_width=True)
    else:
        st.warning("PortWatch veri tabanı bulunamadı. Lütfen CSV dosyasının repo dizininde olduğundan emin olun.")
