from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import requests
import streamlit as st


@st.cache_data(ttl=3600)  # Her saat başı güncellenir, siteyi yormaz
def fetch_portwatch_vessel_data():
  """PortWatch'tan Babülmendep ve Süveyş için detaylı gemi/yük türü verilerini çeker."""
  url = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
  headers = {"User-Agent": "Mozilla/5.0"}

  hedef_noktalar = [
      ("Suez", "Süveyş Kanalı"),
      ("Bab el-Mandeb", "Babülmendep"),
  ]

  toplu_kayitlar = []

  for anahtar, boğaz_adi in hedef_noktalar:
    # 10 yıllık geniş veri seti çekimi (ArcGIS üst sınırı dahilinde)
    params = {
        "where": f"name LIKE '%{anahtar}%'",
        "outFields": (
            "date,transit_calls,n_container,n_tanker,n_dry_bulk,n_general_cargo"
        ),
        "orderByFields": "date DESC",
        "resultRecordCount": 3650,  # Yaklaşık 10 yıl
        "f": "json",
    }
    try:
      res = requests.get(url, params=params, headers=headers, timeout=20)
      features = res.json().get("features", [])
      for f in features:
        attr = f["attributes"]
        # Milisaniye timestamp'i tarihe çevir
        tarih = pd.to_datetime(attr.get("date"), unit="ms")

        # Farklı yük türlerini satır satır ekle (Plotly kolay çizsin diye)
        turler = {
            "Toplam Gemi": attr.get("transit_calls", 0),
            "Konteyner (Container)": attr.get("n_container", 0),
            "Tanker (Petrol/Kimyasal)": attr.get("n_tanker", 0),
            "Kuru Yük (Dry Bulk)": attr.get("n_dry_bulk", 0),
            "Genel Kargo": attr.get("n_general_cargo", 0),
        }

        for tur_adi, sayi in turler.items():
          if sayi is not None:
            toplu_kayitlar.append({
                "Boğaz": boğaz_adi,
                "Tarih": tarih,
                "Yük/Gemi Türü": tur_adi,
                "Günlük Geçiş Sayısı": sayi,
            })
    except Exception as e:
      print(f"{boğaz_adi} verisi çekilemedi: {e}")

  return pd.DataFrame(toplu_kayitlar)


# ==========================================
# STREAMLIT ARAYÜZÜ BÖLÜMÜ
# ==========================================
st.divider()
st.header("🚢 IMF PortWatch: Deniz Ticareti ve Boğaz Geçişleri")
st.caption(
    "Süveyş Kanalı ve Babülmendep Boğazı'ndan geçen yük ve tanker trafiği"
)

# Veriyi yükle
df_gemiler = fetch_portwatch_vessel_data()

if not df_gemiler.empty:
  # Filtreleme Alanı (Kolonlar halinde yan yana)
  col1, col2, col3 = st.columns(3)

  with col1:
    secilen_bogaz = st.selectbox(
        "📍 Boğaz / Kanal Seçin:",
        options=df_gemiler["Boğaz"].unique(),
        index=0,
    )

  with col2:
    zaman_araligi = st.selectbox(
        "📅 Zaman Dilimi:",
        options=["Son 1 Yıl", "Son 3 Yıl", "Son 5 Yıl", "Son 10 Yıl (Tümü)"],
        index=1,  # Varsayılan: Son 3 Yıl
    )

  with col3:
    secilen_turler = st.multiselect(
        "📦 Gemi / Yük Türleri:",
        options=df_gemiler["Yük/Gemi Türü"].unique(),
        default=[
            "Konteyner (Container)",
            "Tanker (Petrol/Kimyasal)",
            "Kuru Yük (Dry Bulk)",
        ],
    )

  # Zaman Filtresini Uygula
  bugun = df_gemiler["Tarih"].max()
  gun_map = {
      "Son 1 Yıl": 365,
      "Son 3 Yıl": 365 * 3,
      "Son 5 Yıl": 365 * 5,
      "Son 10 Yıl (Tümü)": 365 * 10,
  }
  baslangic_tarihi = bugun - timedelta(days=gun_map[zaman_araligi])

  # DataFrame Filtreleme
  filtrelenmis_df = df_gemiler[
      (df_gemiler["Boğaz"] == secilen_bogaz)
      & (df_gemiler["Tarih"] >= baslangic_tarihi)
      & (df_gemiler["Yük/Gemi Türü"].isin(secilen_turler))
  ]

  # İnteraktif Plotly Grafiği
  if not filtrelenmis_df.empty:
    fig = px.line(
        filtrelenmis_df,
        x="Tarih",
        y="Günlük Geçiş Sayısı",
        color="Yük/Gemi Türü",
        title=f"{secilen_bogaz} - {zaman_araligi} Geçiş Dağılımı",
    )
    fig.update_layout(
        hovermode="x unified",
        xaxis_title="Tarih",
        yaxis_title="Günlük Gemi Sayısı",
        legend_title="Gemi Türü",
        template="plotly_dark",  # Sitenizin koyu/açık temasına uyum sağlar
    )
    st.plotly_chart(fig, use_container_width=True)
  else:
    st.warning("Seçilen filtrelere uygun veri bulunamadı.")
else:
  st.info("PortWatch verileri yükleniyor veya şu an erişilemiyor...")
