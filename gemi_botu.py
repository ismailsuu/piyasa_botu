import os
import pandas as pd
import requests

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

def main():
    csv_file = "PortWatch_chokepoints_database.csv"

    if not os.path.exists(csv_file):
        print(f"Kritik Hata: {csv_file} dosyası dizinde bulunamadı!")
        return

    df = pd.read_csv(csv_file)
    print(f"Dosya başarıyla yüklendi. Toplam boğaz sayısı: {len(df)}")

    # Yalnızca hedeflenen 3 ana boğaz
    noktalar = [
        ("Süveyş Kanalı", "chokepoint1"),
        ("Hürmüz Boğazı", "chokepoint6"),
        ("Ümit Burnu", "chokepoint7"),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Kritik Boğazlar Trafik Raporu</b>\n"]
    bulunan = 0

    def safe_int(val):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    for etiket, pid in noktalar:
        satir = df[df["portid"] == pid]
        if not satir.empty:
            kayit = satir.iloc[0]

            toplam = safe_int(kayit.get("vessel_count_total", 0))
            tanker = safe_int(kayit.get("vessel_count_tanker", 0))
            konteyner = safe_int(kayit.get("vessel_count_container", 0))
            kuru = safe_int(kayit.get("vessel_count_dry_bulk", 0))

            mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam Geçiş: <b>{toplam:,}</b>)")
            mesajlar.append(
                f"   ▫️ Tanker: {tanker:,} | Konteyner: {konteyner:,} | Kuru Yük: {kuru:,}\n"
            )
            bulunan += 1
        else:
            print(f"{etiket} ({pid}) bulunamadı.")

    if bulunan > 0:
        mesajlar.append("📊 <b>Canlı Panel:</b> https://ismail-piyasa.streamlit.app/")
        send_telegram("\n".join(mesajlar))
        print(f"İşlem Tamamlandı: {bulunan} boğaz Telegram'a iletildi.")
    else:
        print("Uyarı: Hiçbir boğaz listelenemedi.")

if __name__ == "__main__":
    main()
