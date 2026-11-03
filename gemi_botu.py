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
    # Şifre/Token istemeyen halka açık PortWatch servisi
    endpoint = "https://services9.arcgis.com/fqDgCAUbok0cvzq7/arcgis/rest/services/PortWatch_Chokepoints_Daily_Transit_Data/FeatureServer/0/query"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    noktalar = [
        ("Süveyş Kanalı", "chokepoint1"),
        ("Babülmendep Boğazı", "chokepoint2"),
        ("Hürmüz Boğazı", "chokepoint6"),
        ("Ümit Burnu", "chokepoint8"),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for etiket, pid in noktalar:
        params = {
            "where": f"portid='{pid}'",
            "outFields": "*",
            "orderByFields": "date desc",
            "resultRecordCount": 10,
            "f": "json",
        }
        try:
            r = requests.get(endpoint, params=params, headers=headers, timeout=20)
            data = r.json()

            if "error" in data:
                print(f"{etiket} ({pid}) API Hatası:", data["error"].get("message"))
                continue

            features = data.get("features", [])
            kayit = None

            if features:
                # Son günlerde toplam geçişi 0'dan büyük olan ilk geçerli günü al
                for f in features:
                    attr = f.get("attributes", {})
                    toplam_deger = (
                        attr.get("n_total")
                        or attr.get("transit_calls")
                        or attr.get("total_calls")
                        or 0
                    )
                    if toplam_deger > 0:
                        kayit = attr
                        break
                if not kayit:
                    kayit = features[0].get("attributes", {})

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
        except Exception as e:
            print(f"{etiket} bağlantı hatası:", e)

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
