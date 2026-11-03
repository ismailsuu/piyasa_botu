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

def main():
    # Gerçek tarayıcı başlıkları (WAF engellerini azaltmak için)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
        "Referer": "https://portwatch.imf.org/",
    }

    # PortWatch ve ArcGIS Hub açık veri indirme bağlantıları
    csv_urls = [
        "https://hub.arcgis.com/api/v3/datasets/3da2b9ca97684916b75c4013f95d18ab_0/downloads/data?format=csv&spatialRefId=4326&where=1%3D1",
        "https://portwatch.imf.org/api/v3/datasets/3da2b9ca97684916b75c4013f95d18ab_0/downloads/data?format=csv",
        "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/PortWatch_Chokepoints_Daily/FeatureServer/0/query?where=1%3D1&outFields=*&f=csv"
    ]

    df = pd.DataFrame()
    for url in csv_urls:
        try:
            print(f"Veri çekiliyor: {url[:60]}...")
            r = requests.get(url, headers=headers, timeout=35)
            
            # Sunucu HTML hata sayfası dönerse atla
            if r.status_code == 200 and not r.text.strip().lower().startswith("<!doctype html"):
                df_temp = pd.read_csv(io.StringIO(r.text))
                if not df_temp.empty and len(df_temp) > 5:
                    df = df_temp
                    print("Veri başarıyla indirildi.")
                    break
        except Exception as e:
            print(f"Bağlantı denemesi başarısız ({e})")
            continue

    if df.empty:
        print("Kritik Hata: PortWatch veri kaynaklarından CSV dosyası temin edilemedi.")
        return

    # Sütun isimlerini normalize et
    df.columns = [str(col).lower().strip() for col in df.columns]

    # Tarih formatını ayarla ve güncelden eskiye sırala
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"], unit="ms")
        except Exception:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values(by="date", ascending=False)

    noktalar = [
        ("Süveyş Kanalı", ["suez", "chokepoint1"]),
        ("Babülmendep Boğazı", ["bab_el_mandeb", "bab el-mandeb", "chokepoint2"]),
        ("Hürmüz Boğazı", ["hormuz", "chokepoint6", "chokepoint3"]),
        ("Ümit Burnu", ["cape_of_good_hope", "cape of good hope", "chokepoint8", "chokepoint5"]),
    ]

    id_col = next((col for col in ["portid", "chokepoint", "chokepoint_name", "name"] if col in df.columns), None)

    if not id_col:
        print("CSV dosyasında boğaz kimlik/isim (portid/name) sütunu bulunamadı.")
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
            if "date" in kayit and pd.notna(kayit["date"]):
                tarih_str = f" <i>({str(kayit['date'])[:10]})</i>"

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
