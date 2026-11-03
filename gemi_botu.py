import os
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
        res = requests.post(url, json=payload, timeout=15)
        print("Telegram Yanıtı:", res.status_code, res.text)
    except Exception as e:
        print("Telegram hatası:", e)


def main():
    # Süveyş'i getiren doğrulanmış servis adresi
    endpoint = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    noktalar = [
        ("Süveyş Kanalı", ["chokepoint1"]),
        ("Babülmendep Boğazı", ["chokepoint2"]),
        ("Hürmüz Boğazı", ["chokepoint3", "chokepoint6"]),
        ("Ümit Burnu", ["chokepoint5", "chokepoint8"]),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for etiket, id_listesi in noktalar:
        kayit = None
        for pid in id_listesi:
            # Doğrudan dolu kaydı çeken sorgu yapısı
            params = {
                "where": f"portid='{pid}' AND n_total > 0",
                "outFields": "date,n_total,n_tanker,n_container,n_dry_bulk",
                "orderByFields": "date DESC",
                "resultRecordCount": 1,
                "f": "json",
            }
            try:
                r = requests.get(endpoint, params=params, headers=headers, timeout=15)
                data = r.json()

                if "error" in data:
                    print(f"{etiket} ({pid}) API Hatası:", data["error"].get("message"))
                    continue

                features = data.get("features", [])
                if features:
                    kayit = features[0].get("attributes", {})
                    break
            except Exception as e:
                print(f"{etiket} ({pid}) bağlantı hatası:", e)

        if kayit:
            toplam = kayit.get("n_total") or 0
            tanker = kayit.get("n_tanker") or 0
            konteyner = kayit.get("n_container") or 0
            kuru = kayit.get("n_dry_bulk") or 0

            mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
            mesajlar.append(
                f"  ▫️ Tanker: {int(tanker)} | Konteyner: {int(konteyner)} | Kuru Yük: {int(kuru)}\n"
            )
            bulunan += 1
        else:
            print(f"{etiket} için kayıt bulunamadı.")

    if bulunan > 0:
        mesajlar.append(
            "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
        )
        send_telegram("\n".join(mesajlar))
        print(f"Başarılı: {bulunan} boğaz Telegram'a iletildi.")
    else:
        print("Hiçbir boğazdan veri alınamadı.")


if __name__ == "__main__":
    main()
