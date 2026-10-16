import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# Sayfa Yapılandırması
st.set_page_config(page_title="Piyasa Gösterge Paneli", page_icon="📈", layout="wide")

st.title("📈 10 Yıllık Finansal Gösterge Paneli")
st.caption("Veriler Yahoo Finance üzerinden canlı ve geçmişe dönük olarak çekilmektedir.")

# Enstrüman Listesi
TICKERS = {
    "Bitcoin (BTC)": "BTC-USD",
    "Altın (Ons - USD)": "GC=F",
    "Gümüş (Ons - USD)": "SI=F",
    "Brent Petrol (Varil)": "BZ=F",
    "Doğalgaz (USD/MMBtu)": "NG=F",
    "Pamuk (#2)": "CT=F",
    "USD / TRY": "USDTRY=X",
    "ABD 10 Yıllık Tahvil": "^TNX",
    "USD / CNY": "CNY=X"
}

# Yan Panel (Filtreler)
st.sidebar.header("⚙️ Ayarlar ve Filtreler")
secilen_ad = st.sidebar.selectbox("Enstrüman Seçin", list(TICKERS.keys()))
secilen_sembol = TICKERS[secilen_ad]

aralik = st.sidebar.selectbox(
    "Zaman Dilimi",
    options=["1 Yıl", "3 Yıl", "5 Yıl", "10 Yıl", "Tüm Geçmiş"],
    index=3  # Varsayılan 10 Yıl
)

aralik_map = {
    "1 Yıl": "1y",
    "3 Yıl": "3y",
    "5 Yıl": "5y",
    "10 Yıl": "10y",
    "Tüm Geçmiş": "max"
}

periyot = st.sidebar.radio("Veri Periyodu", ["Günlük", "Haftalık", "Aylık"])
periyot_map = {"Günlük": "1d", "Haftalık": "1wk", "Aylık": "1mo"}

@st.cache_data(ttl=3600)  # Veriyi 1 saat önbelleğe alıp hızı artırır
def verileri_getir(sembol, period, interval):
    df = yf.download(sembol, period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

with st.spinner("Piyasa verileri yükleniyor..."):
    df = verileri_getir(secilen_sembol, aralik_map[aralik], periyot_map[periyot])

if df.empty:
    st.error("Bu enstrüman için geçmiş veri bulunamadı.")
else:
    # Metrik Kartları
    son_fiyat = float(df['Close'].iloc[-1])
    onceki_fiyat = float(df['Close'].iloc[-2]) if len(df) > 1 else son_fiyat
    fark = son_fiyat - onceki_fiyat
    yuzde_degisim = (fark / onceki_fiyat) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Son Kapanış Fiyatı", f"{son_fiyat:,.2f}", f"%{yuzde_degisim:+.2f}")
    col2.metric("Periyot En Yüksek", f"{float(df['High'].max()):,.2f}")
    col3.metric("Periyot En Düşük", f"{float(df['Low'].min()):,.2f}")
    col4.metric("Veri Sayısı", f"{len(df)} Kayıt")

    st.markdown("---")

    # İnteraktif Grafik Sekmeleri
    tab1, tab2, tab3 = st.tabs(["📉 Fiyat Grafiği (Çizgi)", "🕯️ Mum Grafik (Detaylı)", "📋 Veri Tablosu"])

    with tab1:
        fig_cizgi = go.Figure()
        fig_cizgi.add_trace(go.Scatter(
            x=df.index, y=df['Close'],
            mode='lines',
            name='Kapanış',
            line=dict(color='#00ADB5', width=2)
        ))
        fig_cizgi.update_layout(
            title=f"{secilen_ad} - {aralik} Çizgi Grafiği",
            xaxis_title="Tarih",
            yaxis_title="Fiyat",
            hovermode="x unified",
            template="plotly_dark"
        )
        st.plotly_chart(fig_cizgi, use_container_width=True)

    with tab2:
        fig_mum = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Mum Verisi'
        )])
        fig_mum.update_layout(
            title=f"{secilen_ad} - Mum Grafiği",
            xaxis_title="Tarih",
            yaxis_title="Fiyat",
            template="plotly_dark",
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig_mum, use_container_width=True)

    with tab3:
        st.subheader("Geçmiş Veri Tablosu")
        tablo_df = df[['Open', 'High', 'Low', 'Close', 'Volume']].sort_index(ascending=False)
        st.dataframe(tablo_df, use_container_width=True)
