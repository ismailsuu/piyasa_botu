import os
import io
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
        "Accept": "text/csv,application/json,*/*",
    }

    # REST query yerine doğrudan statik OpenData CSV bağlantıları
    csv_sources = [
        "https://opendata.arcgis.com/datasets/3da2b9ca97684916b75c4013f95d18ab_0.csv",
        "https://hub.arcgis.com/datasets/3da2b9ca97684916b75c4013f95d18ab_0.csv",
        "https://portwatch.imf.org/datasets/3da2b9ca97684916b75c4013f95d18ab_0.csv"
    ]

    for url in csv_sources:
        try:
            print(f"PortWatch CSV indiriliyor: {url}...")
            r = requests.get(url, headers=headers, timeout=40, allow_redirects=True)
            
            if r.status_code == 200 and not r.text.strip().lower().startswith("<!doctype html"):
                # Gelen metin geçerli bir tablo mu kontrol et
                df = pd.read_csv(io.StringIO(r.text))
                if not df.empty and len(df) > 10:
                    print(f"Başarılı! {len(df)} satır veri indirildi.")
                    return df
            else:
                print(f"Kaynak yanıt vermedi veya HTML döndü: HTTP {r.status_code}")
        except Exception as e:
            print(f"İndirme hatası ({url}): {e}")

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
        
        # Tarih sütununu belirle ve sırala
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
                        # En güncel geçerli satırı al
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
                    tanker = safe_int(kayit.get("n_tanker") or kayit.get("tanker_calls") or kayit.get("tankers") or 0)
                    konteyner = safe_int(kayit.get("n_container") or kayit.get("container_calls") or kayit.get("containers") or 0)
                    kuru = safe_int(kayit.get("n_dry_bulk") or kayit.get("dry_bulk_calls") or kayit.get("cargo_calls") or 0)

                    tarih_str = ""
                    if pd.notna(kayit.get("parsed_date")):
                        tarih_str = f" <i>({str(kayit['parsed_date'])[:10]})</i>"

                    mesajlar.append(f"⚓ <b>{etiket}</b>{tarih_str} (Toplam: <b>{toplam}</b>)")
                    mesajlar.append(f"   ▫️ Tanker: {tanker} | Konteyner: {konteyner} | Kuru Yük: {kuru}\n")
                    bulunan += 1

    # Hiçbir veri çekilemediyse fallback mesajı gönder
    if bulunan == 0:
        print("Veri eşleştirilemedi, fallback mesajı gönderiliyor.")
        mesajlar.append("⚠️ <i>IMF PortWatch veri akışında geçici gecikme yaşanıyor.</i>\n")
        mesajlar.append("Detaylı analiz için paneli ziyaret edebilirsiniz.")

    mesajlar.append("📊 <b>Canlı Panel:</b> https://ismail-piyasa.streamlit.app/")
    send_telegram("\n".join(mesajlar))
    print(f"Tamamlandı: {bulunan} boğaz bildirildi.")

if __name__ == "__main__":
    main()
