import os
import requests
import pandas as pd

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(mesaj):
    if not BOT_TOKEN or not CHAT_ID:
        print("Hata: TELEGRAM_TOKEN veya TELEGRAM_CHAT_ID bulunamadı!")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        res = requests.post(url, json=payload, timeout=20)
        print("Telegram Yanıtı:", res.status_code, res.text)
    except Exception as e:
        print("Telegram gönderim hatası:", e)

def fetch_portwatch_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
    }

    # Alternatif 1: IMF PortWatch doğrudan katman sorgu URL'leri
    endpoints = [
        "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/PortWatch_Daily_Chokepoints_Data/FeatureServer/0/query",
        "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/PortWatch_Chokepoints_Daily/FeatureServer/0/query",
        "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoint_Data/FeatureServer/0/query",
    ]

    for ep in endpoints:
        print(f"Denetleniyor: {ep}...")
        params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "false",
            "resultRecordCount": "100",
            "f": "pjson"
        }
        try:
            r = requests.get(ep, headers=headers, params=params, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if "features" in data and len(data["features"]) > 0:
                    rows = [item["attributes"] for item in data["features"]]
                    print(f"Başarılı! {len(rows)} kayıt alındı.")
                    return pd.DataFrame(rows)
        except Exception:
            continue

    # Alternatif 2: ArcGIS Hub API v3 (Download URL doğrudan alma)
    try:
        print("ArcGIS Hub API v3 üzerinden dosya URL'si aranıyor...")
        hub_api = "https://hub.arcgis.com/api/v3/datasets/3da2b9ca97684916b75c4013f95d18ab_0"
        r_hub = requests.get(hub_api, headers=headers, timeout=15)
        if r_hub.status_code == 200:
            hub_json = r_hub.json()
            download_url = hub_json.get("data", {}).get("attributes", {}).get("sourceUrl") or \
                           hub_json.get("data", {}).get("links", {}).get("downloadLink")
            if download_url:
                print(f"İndirme bağlantısı bulundu: {download_url}")
                df_hub = pd.read_csv(download_url)
                if not df_hub.empty:
                    return df_hub
    except Exception as e:
        print(f"Hub indirme hatası: {e}")

    return pd.DataFrame()

def main():
    df = fetch_portwatch_data()

    noktalar = [
        ("Süveyş Kanalı", ["suez", "chokepoint1"]),
        ("Babülmendep Boğazı", ["bab_el_mandeb", "bab el-mandeb", "chokepoint2"]),
        ("Hürmüz Boğazı", ["hormuz", "chokepoint6", "chokepoint3"]),
        ("Ümit Burnu", ["cape_of_good_hope", "cape of good hope", "chokepoint8", "chokepoint5"]),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    if not df.empty:
        df.columns = [str(col).lower().strip() for col in df.columns]
        date_col = next((c for c in ["date", "datetime", "record_date"] if c in df.columns), None)
        if date_col:
            try:
                df["parsed_date"] = pd.to_datetime(df[date_col], unit="ms")
            except Exception:
                df["parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=["parsed_date"]).sort_values(by="parsed_date", ascending=False)
        else:
            df["parsed_date"] = None

        id_col = next((col for col in ["portid", "chokepoint", "chokepoint_name", "name"] if col in df.columns), None)

        if id_col:
            for etiket, kelimeler in noktalar:
                kayit = None
                for kelime in kelimeler:
                    filtre = df[df[id_col].astype(str).str.lower().str.contains(kelime, na=False)]
                    if not filtre.empty:
                        kayit = filtre.iloc[0]
                        break

                if kayit is not None:
                    def safe_int(val):
                        try:
                            return int(float(val))
                        except Exception:
                            return 0

                    toplam = safe_int(kayit.get("n_total") or kayit.get("total_calls") or kayit.get("transit_calls") or 0)
                    tanker = safe_int(kayit.get("n_tanker") or kayit.get("tanker_calls") or 0)
                    konteyner = safe_int(kayit.get("n_container") or kayit.get("container_calls") or 0)
                    kuru = safe_int(kayit.get("n_dry_bulk") or kayit.get("dry_bulk_calls") or 0)

                    tarih_str = ""
                    if pd.notna(kayit.get("parsed_date")):
                        tarih_str = f" <i>({str(kayit['parsed_date'])[:10]})</i>"

                    mesajlar.append(f"⚓ <b>{etiket}</b>{tarih_str} (Toplam: <b>{toplam}</b>)")
                    mesajlar.append(f"   ▫️ Tanker: {tanker} | Konteyner: {konteyner} | Kuru Yük: {kuru}\n")
                    bulunan += 1

    # PortWatch tamamen erişilmez durumdaysa fallback (bilgilendirme) mesajı gönder
    if bulunan == 0:
        print("Uyarı: IMF PortWatch API verisi alınamadı, özet bilgilendirme gönderiliyor.")
        mesajlar.append("⚠️ <i>IMF PortWatch açık veri servisinde anlık güncelleme/erişim kesintisi mevcut.</i>\n")
        mesajlar.append("📊 Güncel grafikleri ve geçmiş analizleri Streamlit paneli üzerinden inceleyebilirsiniz.")

    mesajlar.append("\n🔗 <b>Canlı Panel:</b> https://ismail-piyasa.streamlit.app/")
    send_telegram("\n".join(mesajlar))
    print("Telegram bildirimi gönderildi.")

if __name__ == "__main__":
    main()
