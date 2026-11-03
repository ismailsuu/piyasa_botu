import os
import requests
import urllib.parse

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
    noktalar = [
        ("Süveyş Kanalı", ["chokepoint1"]),
        ("Babülmendep Boğazı", ["chokepoint2"]),
        ("Hürmüz Boğazı", ["chokepoint6", "chokepoint3"]),
        ("Ümit Burnu", ["chokepoint8", "chokepoint5"]),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for etiket, id_listesi in noktalar:
        kayit = None
        for pid in id_listesi:
            # Asıl çalışan ArcGIS URL'sini uçtan uca URL formatına çeviriyoruz
            arcgis_url = (
                f"https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
                f"Daily_Chokepoints_Data/FeatureServer/0/query?"
                f"where=portid='{pid}'&outFields=date,n_total,n_tanker,n_container,n_dry_bulk"
                f"&orderByFields=date DESC&resultRecordCount=10&f=json"
            )
            
            # GitHub Actions IP engelini ve WAF 499 (Token Required) hatasını aşmak için proxy rotası
            proxy_url = f"https://api.allorigins.win/raw?url={urllib.parse.quote(arcgis_url)}"
            
            try:
                r = requests.get(proxy_url, timeout=25)
                data = r.json()

                if "error" in data:
                    print(f"{etiket} ({pid}) API Uyarısı:", data["error"].get("message"))
                    continue

                features = data.get("features", [])
                if features:
                    # En güncel, dolu (n_total > 0) olan kaydı bul
                    for f in features:
                        attr = f.get("attributes", {})
                        if (attr.get("n_total") or 0) > 0:
                            kayit = attr
                            break
                    if not kayit:
                        kayit = features[0].get("attributes", {})
                    if kayit:
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
