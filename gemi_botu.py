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

def fetch_chokepoint(query_url, headers, pid):
    """Her boğaz için en güncel kaydı POST ile hızlıca çeker."""
    data_payload = {
        "where": f"portid = '{pid}'",
        "outFields": "*",
        "orderByFields": "date DESC",
        "resultRecordCount": "1",
        "returnGeometry": "false",
        "f": "json"
    }
    try:
        r = requests.post(query_url, headers=headers, data=data_payload, timeout=30)
        if r.status_code == 200:
            res_json = r.json()
            features = res_json.get("features", [])
            if features:
                return features[0].get("attributes")
    except Exception as e:
        print(f"{pid} çekilirken hata: {e}")
    return None

def fetch_portwatch_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://portwatch.imf.org/",
    }

    query_url = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

    # 1. Strateji: Hedef boğazları tek tek çek (En hızlı ve garanti yöntem)
    target_ids = ["chokepoint1", "chokepoint2", "chokepoint3", "chokepoint6", "chokepoint8", "chokepoint5"]
    records = []
    
    print("Boğaz verileri POST ile doğrudan sorgulanıyor...")
    for pid in target_ids:
        attr = fetch_chokepoint(query_url, headers, pid)
        if attr:
            records.append(attr)

    if records:
        print(f"Başarılı: {len(records)} boğaz kaydı anında alındı.")
        return pd.DataFrame(records)

    # 2. Strateji (Yedek): Tek seferde toplu POST sorgusu (45 sn timeout)
    print("Tekil sorgular tamamlanamadı, toplu POST deneniyor...")
    batch_payload = {
        "where": "1=1",
        "outFields": "*",
        "orderByFields": "date DESC",
        "resultRecordCount": "100",
        "returnGeometry": "false",
        "f": "json"
    }
    try:
        r = requests.post(query_url, headers=headers, data=batch_payload, timeout=45)
        if r.status_code == 200:
            res_json = r.json()
            features = res_json.get("features", [])
            if features:
                rows = [item["attributes"] for item in features]
                print(f"Toplu sorgu başarılı: {len(rows)} kayıt alındı.")
                return pd.DataFrame(rows)
    except Exception as e:
        print(f"Toplu sorgu hatası: {e}")

    return pd.DataFrame()

def main():
    df = fetch_portwatch_data()

    if df.empty:
        print("Kritik Hata: Veri çekilemedi.")
        return

    # Sütun isimlerini normalize et
    df.columns = [str(col).lower().strip() for col in df.columns]

    # Milisaniye (Unix Epoch) tarihini datetime formatına dönüştür
    date_col = next((c for c in ["date", "datetime", "record_date"] if c in df.columns), None)
    if date_col:
        try:
            df["parsed_date"] = pd.to_datetime(df[date_col], unit="ms")
        except Exception:
            df["parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=["parsed_date"]).sort_values(by="parsed_date", ascending=False)
    else:
        df["parsed_date"] = None

    noktalar = [
        ("Süveyş Kanalı", ["suez", "chokepoint1"]),
        ("Babülmendep Boğazı", ["bab_el_mandeb", "bab el-mandeb", "chokepoint2"]),
        ("Hürmüz Boğazı", ["hormuz", "chokepoint6", "chokepoint3"]),
        ("Ümit Burnu", ["cape_of_good_hope", "cape of good hope", "chokepoint8", "chokepoint5"]),
    ]

    id_col = next((col for col in ["portid", "chokepoint", "chokepoint_name", "name"] if col in df.columns), None)

    if not id_col:
        print(f"Hata: Boğaz kimlik/isim sütunu bulunamadı. Mevcut sütunlar: {list(df.columns)}")
        return

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for etiket, kelimeler in noktalar:
        kayit = None
        for kelime in kelimeler:
            filtre = df[df[id_col].astype(str).str.lower().str.contains(kelime, na=False)]
            if not filtre.empty:
                for _, satir in filtre.iterrows():
                    toplam_test = satir.get("n_total") or satir.get("total_calls") or satir.get("transit_calls") or 0
                    try:
                        toplam_sayi = float(toplam_test)
                    except (ValueError, TypeError):
                        toplam_sayi = 0

                    if toplam_sayi > 0:
                        kayit = satir
                        break
                if kayit is not None:
                    break

        if kayit is not None:
            def safe_int(val):
                try:
                    return int(float(val))
                except (ValueError, TypeError):
                    return 0

            toplam = safe_int(kayit.get("n_total") or kayit.get("total_calls") or kayit.get("transit_calls") or 0)
            tanker = safe_int(kayit.get("n_tanker") or kayit.get("tanker_calls") or kayit.get("tankers") or 0)
            konteyner = safe_int(kayit.get("n_container") or kayit.get("container_calls") or kayit.get("containers") or 0)
            kuru = safe_int(kayit.get("n_dry_bulk") or kayit.get("dry_bulk_calls") or kayit.get("cargo_calls") or 0)

            tarih_str = ""
            if pd.notna(kayit.get("parsed_date")):
                tarih_str = f" <i>({str(kayit['parsed_date'])[:10]})</i>"

            mesajlar.append(f"⚓ <b>{etiket}</b>{tarih_str} (Toplam: <b>{toplam}</b>)")
            mesajlar.append(
                f"   ▫️ Tanker: {tanker} | Konteyner: {konteyner} | Kuru Yük: {kuru}\n"
            )
            bulunan += 1
        else:
            print(f"{etiket} için geçerli transit kaydı bulunamadı.")

    if bulunan > 0:
        mesajlar.append("📊 <b>Canlı Panel:</b> https://ismail-piyasa.streamlit.app/")
        send_telegram("\n".join(mesajlar))
        print(f"İşlem Tamamlandı: {bulunan} boğaz Telegram'a iletildi.")
    else:
        print("Uyarı: Hiçbir boğaz için geçerli veri satırı eşleştirilemedi.")

if __name__ == "__main__":
    main()
