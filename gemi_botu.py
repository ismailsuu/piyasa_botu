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
        res = requests.post(url, json=payload, timeout=15)
        print("Telegram Yanıtı:", res.status_code, res.text)
    except Exception as e:
        print("Telegram hatası:", e)

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Doğrulanmış ArcGIS Hub CSV İndirme Bağlantıları (Dataset ID: 3da2b9ca97684916b75c4013f95d18ab)
    csv_urls = [
        "https://hub.arcgis.com/api/v3/datasets/3da2b9ca97684916b75c4013f95d18ab_0/downloads/data?format=csv&spatialRefId=4326&where=1%3D1",
        "https://portwatch.imf.org/api/v3/datasets/3da2b9ca97684916b75c4013f95d18ab_0/downloads/data?format=csv"
    ]

    df = pd.DataFrame()
    for url in csv_urls:
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                df = pd.read_csv(io.StringIO(r.text))
                if not df.empty:
                    break
        except Exception:
            continue

    if df.empty:
        print("Kritik Hata: Veri kaynaklarından geçerli CSV dosyası alınamadı (404/Bağlantı Hatası).")
        return

    # Sütun isimlerini güvenli okuma için küçük harfe çevir
    df.columns = [str(col).lower() for col in df.columns]

    # Tarihe göre en sondan (en güncelden) geriye sırala
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"], unit="ms")
        except Exception:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values(by="date", ascending=False)

    noktalar = [
        ("Süveyş Kanalı", ["suez", "chokepoint1"]),
        ("Babülmendep Boğazı", ["bab_el_mandeb", "bab el-mandeb", "chokepoint2"]),
        ("Hürmüz Boğazı", ["hormuz", "chokepoint6", "chokepoint3"]),
        ("Ümit Burnu", ["cape_of_good_hope", "cape of good hope", "chokepoint8", "chokepoint5"]),
    ]

    id_col = next((col for col in ["portid", "chokepoint", "chokepoint_name", "name"] if col in df.columns), None)

    if not id_col:
        print("CSV dosyasında id/isim sütunu bulunamadı.")
        return

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for etiket, kelimeler in noktalar:
        kayit = None
        for kelime in kelimeler:
            # Boğaz ismi veya ID'si içeren satırları filtrele
            filtre = df[df[id_col].astype(str).str.lower().str.contains(kelime, na=False)]
            if not filtre.empty:
                # Toplam geçişi 0'dan büyük olan ilk güncel satırı al
                for _, satir in filtre.iterrows():
                    toplam_test = satir.get("n_total") or satir.get("total_calls") or satir.get("transit_calls") or 0
                    if pd.notna(toplam_test) and float(toplam_test) > 0:
                        kayit = satir
                        break
                if kayit is not None:
                    break

        if kayit is not None:
            toplam = kayit.get("n_total") or kayit.get("total_calls") or kayit.get("transit_calls") or 0
            tanker = kayit.get("n_tanker") or kayit.get("tanker_calls") or kayit.get("tankers") or 0
            konteyner = kayit.get("n_container") or kayit.get("container_calls") or kayit.get("containers") or 0
            kuru = kayit.get("n_dry_bulk") or kayit.get("dry_bulk_calls") or kayit.get("cargo_calls") or 0

            mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {int(float(toplam))})")
            mesajlar.append(
                f"  ▫️ Tanker: {int(float(tanker))} | Konteyner: {int(float(konteyner))} | Kuru Yük: {int(float(kuru))}\n"
            )
            bulunan += 1
        else:
            print(f"{etiket} için geçerli kayıt bulunamadı.")

    if bulunan > 0:
        mesajlar.append(
            "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
        )
        send_telegram("\n".join(mesajlar))
        print(f"Başarılı: {bulunan} boğaz Telegram'a iletildi.")
    else:
        print("Kritik: Hiçbir boğazdan kayıt alınamadı.")

if __name__ == "__main__":
    main()
