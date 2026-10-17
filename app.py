@st.cache_data(ttl=3600)
def fetch_portwatch_data():
  """PortWatch açık CSV verisini doğrudan yükler."""
  csv_url = "https://raw.githubusercontent.com/IMF-PortWatch/PortWatch-data/main/data/daily_chokepoints_data.csv"
  try:
    df = pd.read_csv(csv_url)
    df.columns = [c.lower() for c in df.columns]
    df["tarih"] = pd.to_datetime(df["date"])

    noktalar = {
        "suez": "Süveyş Kanalı",
        "bab el-mandeb": "Babülmendep",
        "hormuz": "Hürmüz Boğazı",
        "cape of good hope": "Ümit Burnu",
    }

    records = []
    for anahtar, etiket in noktalar.items():
      alt_df = df[df["name"].str.lower().str.contains(anahtar, na=False)]
      for _, row in alt_df.iterrows():
        dt = row["tarih"]
        tur_haritasi = {
            "Toplam Gemi": row.get("n_total") or row.get("transit_calls", 0),
            "Konteyner (Container)": row.get("n_container", 0),
            "Tanker (Petrol/Kimyasal)": row.get("n_tanker", 0),
            "Kuru Yük (Dry Bulk)": row.get("n_dry_bulk", 0),
        }
        for tur, adet in tur_haritasi.items():
          records.append({
              "Boğaz": etiket,
              "Tarih": dt,
              "Yük/Gemi Türü": tur,
              "Geçiş Sayısı": int(adet or 0),
          })
    return pd.DataFrame(records)
  except Exception as e:
    print(f"PortWatch yükleme hatası: {e}")
    return pd.DataFrame()
