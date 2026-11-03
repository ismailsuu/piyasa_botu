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
    endpoint = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    noktalar = [
        ("chokepoint1", "Süveyş Kanalı"),
        ("chokepoint2", "Babülmendep Boğazı"),
        ("chokepoint6", "Hürmüz Boğazı"),
        ("chokepoint8", "Ümit Burnu"),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for pid, etiket in noktalar:
        # n_total > 0 şartı: Henüz verisi işlenmemiş boş günleri atlar, verisi olan en güncel günü getirir
        params = {
            "where": f"portid='{pid}' AND n_total > 0",
            "outFields": "date,n_total,n_tanker,n_container,n_dry_bulk",
            "orderByFields": "date DESC",
            "resultRecordCount": 1,
            "f": "json",
        }

        try:
            r = requests.get(endpoint, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                features = data.get("features", [])
                if features:
                    attr = features[0].get("attributes", {})
                    toplam = attr.get("n_total") or 0
                    tanker = attr.get("n_tanker") or 0
                    konteyner = attr.get("n_container") or 0
                    kuru = attr.get("n_dry_bulk") or 0

                    mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
                    mesajlar.append(
                        f"  ▫️ Tanker: {int(tanker)} | Konteyner: {int(konteyner)} | Kuru Yük: {int(kuru)}\n"
                    )
                    bulunan += 1
                else:
                    print(f"{etiket} için n_total > 0 olan kayıt bulunamadı.")
            else:
                print(f"{etiket} HTTP Hatası: {r.status_code}")
        except Exception as e:
            print(f"{etiket} hatası: {e}")

    if bulunan > 0:
        mesajlar.append(
            "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
        )
        send_telegram("\n".join(mesajlar))
        print("Telegram mesajı başarıyla iletildi.")
    else:
        print("Veri bulunamadığı için mesaj atılmadı.")


if __name__ == "__main__":
    main()
