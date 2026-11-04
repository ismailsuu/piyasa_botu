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
        print("Telegram Yanıtı:", res.status_code)
    except Exception as e:
        print("Telegram gönderim hatası:", e)

def fetch_single_point(query_url, headers, where_clause):
    """Belirtilen filtre için en güncel tekil kaydı POST ile çeker."""
    data_payload = {
        "where": where_clause,
        "outFields": "*",
        "orderByFields": "date DESC",
        "resultRecordCount": "1",
        "returnGeometry": "false",
        "f": "json"
    }
    try:
        r = requests.post(query_url, headers=headers, data=data_payload, timeout=20)
        if r.status_code == 200:
            res_json = r.json()
            features = res_json.get("features", [])
            if features:
                return features[0].get("attributes")
    except Exception as e:
        print(f"Sorgu hatası ({where_clause}): {e}")
    return None

def fetch_portwatch_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://portwatch.imf.org/",
    }

    query_url = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

    # Her boğaz için olası tüm portid ve isim kombinasyonları
    hedef_noktalar = [
        ("Süveyş Kanalı", "(portid = 'chokepoint1' OR LOWER(name) LIKE '%suez%')"),
        ("Babülmendep Boğazı", "(portid = 'chokepoint2' OR LOWER(name) LIKE '%mandeb%')"),
        ("Hürmüz Boğazı", "(portid IN ('chokepoint3', 'chokepoint6') OR LOWER(name) LIKE '%hormuz%')"),
        ("Ümit Burnu", "(portid IN ('chokepoint5', 'chokepoint8') OR LOWER(name) LIKE '%good hope%' OR LOWER(name) LIKE '%cape%')"),
    ]

    records = []
    print("Boğaz verileri tek tek hedeflenerek çekiliyor...")
    
    for etiket, where_filter in hedef_noktalar:
        attr = fetch_single_point(query_url, headers, where_filter)
        if attr:
            attr["_label"] = etiket
            records.append(attr)
            print(f"Alındı: {etiket}")
        else:
            print(f"Kayıt bulunamadı: {etiket}")

    if records:
        return pd.DataFrame(records)

    return pd.DataFrame()

def main():
    df = fetch_portwatch_data()

    if df.empty:
        print("Kritik Hata: Hiçbir boğaz için veri alınamadı.")
        return

    # Sütun isimlerini küçük harfe normalize et
    df.columns = [str(col).lower().strip() for col in df.columns]

    # Tarih formatını ayarla
    date_col = next((c for c in ["date", "datetime", "record_date"] if c in df.columns), None)
    if date_col:
        try:
            df["parsed_date"] = pd.to_datetime(df[date_col], unit="ms")
        except Exception:
            df["parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        df["parsed_date"] = None

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    def safe_int(val):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    for _, satir in df.iterrows():
        etiket = satir.get("_label", "Boğaz")
        toplam = safe_int(satir.get("n_total") or satir.get("total_calls") or satir.get("transit_calls") or 0)
        tanker = safe_int(satir.get("n_tanker") or satir.get("tanker_calls") or satir.get("tankers") or 0)
        konteyner = safe_int(satir.get("n_container") or satir.get("container_calls") or satir.get("containers") or 0)
        kuru = safe_int(satir.get("n_dry_bulk") or satir.get("dry_bulk_calls") or satir.get("cargo_calls") or 0)

        tarih_str = ""
        if pd.notna(satir.get("parsed_date")):
            tarih_str = f" <i>({str(satir['parsed_date'])[:10]})</i>"

        mesajlar.append(f"⚓ <b>{etiket}</b>{tarih_str} (Toplam: <b>{toplam}</b>)")
        mesajlar.append(f"   ▫️ Tanker: {tanker} | Konteyner: {konteyner} | Kuru Yük: {kuru}\n")
        bulunan += 1

    if bulunan > 0:
        mesajlar.append("📊 <b>Canlı Panel:</b> https://ismail-piyasa.streamlit.app/")
        send_telegram("\n".join(mesajlar))
        print(f"İşlem Tamamlandı: {bulunan} boğaz Telegram'a iletildi.")
    else:
        print("Uyarı: Boğaz verisi listelenemedi.")

if __name__ == "__main__":
    main()
