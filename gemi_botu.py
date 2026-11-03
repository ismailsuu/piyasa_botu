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
        print("Telegram gönderim hatası:", e)


def main():
    endpoint = "https://services9.arcgis.com/fqDgCAUbok0cvzq7/arcgis/rest/services/PortWatch_Chokepoints_Daily_Transit_Data/FeatureServer/0/query"

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
        # Doğrudan ArcGIS'in tanıdığı portid alanı sorgulanır
        params = {
            "where": f"portid='{pid}'",
            "outFields": "*",
            "orderByFields": "date desc",
            "resultRecordCount": 1,
            "f": "json",
        }

        try:
            r = requests.get(endpoint, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                
                # ArcGIS hata dönerse sebebini loga bas
                if "error" in data:
                    print(f"{etiket} API Hatası:", data["error"].get("message"))
                    continue

                features = data.get("features", [])
                if features:
                    attr = features[0].get("attributes", {})

                    toplam = (
                        attr.get("n_total")
                        or attr.get("transit_calls")
                        or attr.get("total_calls")
                        or 0
                    )
                    tanker = (
                        attr.get("n_tanker")
                        or attr.get("tanker_calls")
                        or attr.get("tankers")
                        or 0
                    )
                    konteyner = (
                        attr.get("n_container")
                        or attr.get("container_calls")
                        or attr.get("containers")
                        or 0
                    )
                    kuru = (
                        attr.get("n_dry_bulk")
                        or attr.get("dry_bulk_calls")
                        or attr.get("cargo_calls")
                        or 0
                    )

                    mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
                    mesajlar.append(
                        f"  ▫️ Tanker: {int(tanker)} | Konteyner: {int(konteyner)} | Kuru Yük: {int(kuru)}\n"
                    )
                    bulunan += 1
                else:
                    print(f"{etiket} için {pid} ile kayıt bulunamadı.")
            else:
                print(f"{etiket} HTTP Hatası: {r.status_code}")
        except Exception as e:
            print(f"{etiket} hatası: {e}")

    if bulunan > 0:
        mesajlar.append(
            "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
        )
        send_telegram("\n".join(mesajlar))
        print("Telegram'a başarıyla iletildi.")
    else:
        print("Veri bulunamadığı için mesaj atılmadı.")


if __name__ == "__main__":
    main()
