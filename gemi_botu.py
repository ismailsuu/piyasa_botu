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

    # IMF PortWatch tablosundaki kesin ID varyasyonları
    noktalar = [
        ("Süveyş Kanalı", ["chokepoint1"]),
        ("Babülmendep Boğazı", ["chokepoint2", "bab_el_mandeb"]),
        ("Hürmüz Boğazı", ["chokepoint3", "chokepoint6", "hormuz"]),
        ("Ümit Burnu", ["chokepoint5", "chokepoint8", "cape_of_good_hope"]),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for etiket, id_listesi in noktalar:
        veri_bulundu = False
        for pid in id_listesi:
            # Hem n_total > 0 olan en son günü hem de basit sorguyu dener
            params = {
                "where": f"portid='{pid}' AND n_total > 0",
                "outFields": "date,n_total,n_tanker,n_container,n_dry_bulk",
                "orderByFields": "date DESC",
                "resultRecordCount": 1,
                "f": "json",
            }
            try:
                r = requests.get(endpoint, params=params, headers=headers, timeout=10)
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
                        veri_bulundu = True
                        break
            except Exception as e:
                print(f"{etiket} ({pid}) hatası: {e}")

        if not veri_bulundu:
            print(f"Uyarı: {etiket} için hiçbir ID eşleşmedi.")

    # Süveyş veya herhangi bir boğaz geldiyse mesajı direkt basar
    if bulunan > 0:
        mesajlar.append(
            "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
        )
        send_telegram("\n".join(mesajlar))
        print(f"Başarılı: {bulunan} boğaz bilgisi Telegram'a iletildi.")
    else:
        print("Kritik: Hiçbir boğazdan veri alınamadı.")


if __name__ == "__main__":
    main()
