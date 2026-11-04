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

def fetch_portwatch_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://portwatch.imf.org/",
    }

    # Doğrulanmış tam servis ve katman adresi
    url = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
    
    # Sunucu tarafında timeout yaratmayan en hafif sorgu parametreleri
    params_list = [
        # 1. En güncel verileri en hızlı çeken OBJECTID azalan sıralı sorgu
        {
            "where": "1=1",
            "outFields": "*",
            "orderByFields": "OBJECTID DESC",
            "resultRecordCount": "100",
            "returnGeometry": "false",
            "f": "json"
        },
        # 2. Alternatif: Tarih sıralamalı
        {
            "where": "1=1",
            "outFields": "*",
            "orderByFields": "date DESC",
            "resultRecordCount": "100",
            "returnGeometry": "false",
            "f": "json"
        },
        # 3. Alternatif: Sıralamasız düz küçük paket
        {
            "where": "1=1",
            "outFields": "*",
            "resultRecordCount": "100",
            "returnGeometry": "false",
            "f": "json"
        }
    ]

    for idx, params in enumerate(params_list, 1):
        try:
            print(f"Hafif sorgu gönderiliyor (Deneme {idx})...")
            r = requests.get(url, headers=headers, params=params, timeout=20)
            if r.status_code == 200:
                data = r.json()
                if "features" in data and len(data["features"]) > 0:
                    rows = [item["attributes"] for item in data["features"]]
                    print(f"Başarılı! {len(rows)} satır veri alındı.")
                    return pd.DataFrame(rows)
                else:
                    print(f"Kayıt gelmedi (Deneme {idx}):", data.get("error", "Boş liste"))
            else:
                print(f"HTTP {r.status_code} alındı.")
        except Exception as e:
            print(f"Deneme {idx} hatası: {e}")

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
        
        # Tarih sütunu çözümleme
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
                        for _, satir in filtre.iterrows():
                            toplam_val = satir.get("n_total") or satir.get("total_calls") or satir.get("transit_calls") or 0
                            try:
                                if float(toplam_val) > 0:
                                    kayit = satir
                                    break
                            except (ValueError, TypeError):
                                continue
                        if kayit is not None:
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

    if bulunan == 0:
        print("Uyarı: Boğaz verisi eşleştirilemedi.")
        mesajlar.append("⚠️ <i>IMF PortWatch veri akışında geçici gecikme yaşanıyor.</i>\n")

    mesajlar.append("📊 <b>Canlı Panel:</b> https://ismail-piyasa.streamlit.app/")
    send_telegram("\n".join(mesajlar))
    print(f"İşlem Tamamlandı. {bulunan} boğaz bildirildi.")

if __name__ == "__main__":
    main()
