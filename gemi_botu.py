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
    # Token istemeyen, ArcGIS Hub PortWatch Açık Katmanı
    endpoint = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/chokepoints_daily/FeatureServer/0/query"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    noktalar = [
        ("Süveyş Kanalı", ["chokepoint1", "suez"]),
        ("Babülmendep Boğazı", ["chokepoint2", "bab_el_mandeb"]),
        ("Hürmüz Boğazı", ["chokepoint6", "chokepoint3", "hormuz"]),
        ("Ümit Burnu", ["chokepoint8", "chokepoint5", "cape_of_good_hope"]),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for etiket, idler in noktalar:
        kayit = None
        for pid in idler:
            params = {
                "where": f"(portid='{pid}' OR chokepoint='{pid}') AND (n_total > 0 OR transit_calls > 0)",
                "outFields": "*",
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

                fts = data.get("features", [])
                if fts:
                    kayit = fts[0].get("attributes", {})
                    break
            except Exception as e:
                print(f"{etiket} bağlantı hatası:", e)

        if kayit:
            toplam = (
                kayit.get("n_total")
                or kayit.get("transit_calls")
                or kayit.get("total_calls")
                or 0
            )
            tanker = (
                kayit.get("n_tanker")
                or kayit.get("tanker_calls")
                or kayit.get("tankers")
                or 0
            )
            konteyner = (
                kayit.get("n_container")
                or kayit.get("container_calls")
                or kayit.get("containers")
                or 0
            )
            kuru = (
                kayit.get("n_dry_bulk")
                or kayit.get("dry_bulk_calls")
                or kayit.get("cargo_calls")
                or 0
            )

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
        print(f"{bulunan} boğaz bilgisi başarıyla Telegram'a iletildi.")
    else:
        print("Hiçbir boğazdan kayıt alınamadı.")


if __name__ == "__main__":
    main()
